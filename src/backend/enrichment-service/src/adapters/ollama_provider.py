"""Ollama chat adapter for bounded category evaluation."""

import json
from urllib.error import HTTPError, URLError
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


class OllamaProvider:
    """Classify one article through Ollama's non-streaming chat API."""

    def __init__(
        self,
        *,
        model: str,
        instructions: str,
        base_url: str,
        timeout: float = 30,
    ) -> None:
        if not model or not base_url or timeout <= 0:
            raise ValueError(
                "Model, Ollama base URL, and positive timeout are required"
            )
        self.model = model
        self.instructions = instructions
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def __call__(self, article: ArticleInput) -> ProviderResult:
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": self.instructions},
                {"role": "user", "content": article_json(article)},
            ],
            "stream": False,
            "format": category_schema(),
            "options": {"temperature": 0, "num_predict": 128},
        }
        request = Request(
            f"{self.base_url}/api/chat",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urlopen(request, timeout=self.timeout) as response:
                raw = response.read(MAX_RESPONSE_BYTES + 1)
        except HTTPError as exc:
            detail = f"Ollama API HTTP {exc.code}"
            if exc.code == 404:
                detail += ": model may be missing; pull it before evaluation"
            raise ProviderError(detail) from exc
        except (URLError, TimeoutError) as exc:
            reason = exc.reason if isinstance(exc, URLError) else exc
            detail = (
                "Ollama request timed out"
                if isinstance(reason, TimeoutError)
                else "Ollama connection failed"
            )
            raise ProviderError(detail) from exc

        if len(raw) > MAX_RESPONSE_BYTES:
            raise ValueError("Provider response exceeds the size limit")
        data = json.loads(raw)
        if not isinstance(data, dict):
            raise ValueError("Provider response must be an object")
        if data.get("done") is not True or data.get("done_reason") != "stop":
            raise ValueError("Provider response did not finish normally")
        message = data.get("message")
        if not isinstance(message, dict):
            raise ValueError("Ollama returned no message")
        content = message.get("content")
        if not isinstance(content, str) or not content.strip():
            raise ValueError("Ollama returned no answer content")
        category = parse_category(json.loads(content))
        response_model = data.get("model", self.model)
        if not isinstance(response_model, str) or not response_model:
            raise ValueError("Provider returned invalid model")
        return ProviderResult(
            category_id=category,
            model=response_model,
            input_tokens=_tokens(data.get("prompt_eval_count")),
            output_tokens=_tokens(data.get("eval_count")),
        )
