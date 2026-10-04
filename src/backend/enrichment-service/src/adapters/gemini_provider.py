"""Gemini adapter for bounded category evaluation."""

import json
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from src.services.classification import ArticleInput
from src.services.provider import (
    ProviderError,
    ProviderResult,
    article_json,
    category_schema,
    parse_category,
)

MAX_RESPONSE_BYTES = 16_384


def _tokens(value: object) -> int | None:
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError("Provider returned invalid token usage")
    return value


class GeminiProvider:
    """Classify one article through Gemini generateContent."""

    def __init__(
        self,
        *,
        model: str,
        instructions: str,
        api_key: str,
        timeout: float = 30,
    ) -> None:
        if not model or not api_key or timeout <= 0:
            raise ValueError(
                "Model, API key, and positive timeout are required"
            )
        self.model = model
        self.instructions = instructions
        self.api_key = api_key
        self.timeout = timeout

    def __call__(self, article: ArticleInput) -> ProviderResult:
        payload = {
            "systemInstruction": {
                "parts": [{"text": self.instructions}],
            },
            "contents": [
                {"role": "user", "parts": [{"text": article_json(article)}]}
            ],
            "generationConfig": {
                "temperature": 0,
                "maxOutputTokens": 128,
                "responseFormat": {
                    "text": {
                        "mimeType": "application/json",
                        "schema": category_schema(),
                    }
                },
            },
        }
        request = Request(
            f"https://generativelanguage.googleapis.com/v1beta/models/"
            f"{self.model}:generateContent",
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "X-goog-api-key": self.api_key,
            },
            method="POST",
        )
        try:
            with urlopen(request, timeout=self.timeout) as response:
                raw = response.read(MAX_RESPONSE_BYTES + 1)
        except HTTPError as exc:
            error_data: object = None
            try:
                error_data = json.loads(exc.read(MAX_RESPONSE_BYTES + 1))
            except (json.JSONDecodeError, UnicodeDecodeError):
                pass
            error = (
                error_data.get("error")
                if isinstance(error_data, dict)
                else None
            )
            status = error.get("status") if isinstance(error, dict) else None
            message = error.get("message") if isinstance(error, dict) else None
            detail = f"Gemini API HTTP {exc.code}"
            if isinstance(status, str):
                detail += f" {status}"
            if isinstance(message, str):
                detail += f": {message}"
            detail = detail.replace(self.api_key, "[REDACTED]")
            raise ProviderError(detail) from exc
        if len(raw) > MAX_RESPONSE_BYTES:
            raise ValueError("Provider response exceeds the size limit")
        data = json.loads(raw)
        if not isinstance(data, dict):
            raise ValueError("Provider response must be an object")
        candidates = data.get("candidates")
        if not isinstance(candidates, list) or not candidates:
            raise ValueError("Gemini returned no candidate")
        candidate = candidates[0]
        if candidate.get("finishReason") != "STOP":
            raise ValueError("Provider response did not finish normally")
        parts = candidate["content"]["parts"]
        content = "".join(
            part["text"]
            for part in parts
            if "text" in part and not part.get("thought")
        )
        category = parse_category(json.loads(content))
        usage = data.get("usageMetadata") or {}
        return ProviderResult(
            category_id=category,
            model=data.get("modelVersion") or self.model,
            input_tokens=_tokens(usage.get("promptTokenCount")),
            output_tokens=_tokens(usage.get("candidatesTokenCount")),
        )
