"""Small HTTP and CLI adapters for bounded classification experiments."""

import json
import subprocess
import tempfile
from collections.abc import Sequence
from typing import Any
from urllib.request import Request, urlopen

from src.services.categories import CATEGORY_DEFINITIONS
from src.services.classification import ArticleInput
from src.services.provider import ProviderResult, article_json, parse_category

MAX_RESPONSE_BYTES = 16_384


def _tokens(value: object) -> int | None:
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError("Provider returned invalid token usage")
    return value


class ChatHttpProvider:
    """Call a Chat Completions compatible endpoint."""

    def __init__(
        self,
        *,
        url: str,
        model: str,
        instructions: str,
        api_key: str | None,
        timeout: float = 30,
        response_format: str = "plain",
    ) -> None:
        if not url or not model or timeout <= 0:
            raise ValueError("URL, model, and positive timeout are required")
        if response_format not in {"plain", "json", "schema"}:
            raise ValueError("Unsupported response format")
        self.url = url
        self.model = model
        self.instructions = instructions
        self.api_key = api_key
        self.timeout = timeout
        self.response_format = response_format

    def __call__(self, article: ArticleInput) -> ProviderResult:
        payload: dict[str, Any] = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": self.instructions},
                {"role": "user", "content": article_json(article)},
            ],
            "max_completion_tokens": 128,
            "stream": False,
        }
        if self.response_format == "json":
            payload["response_format"] = {"type": "json_object"}
        elif self.response_format == "schema":
            payload["response_format"] = {
                "type": "json_schema",
                "json_schema": {
                    "name": "article_category",
                    "strict": True,
                    "schema": {
                        "type": "object",
                        "properties": {
                            "category_id": {
                                "type": ["string", "null"],
                                "enum": [*CATEGORY_DEFINITIONS, None],
                            }
                        },
                        "required": ["category_id"],
                        "additionalProperties": False,
                    },
                },
            }
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        request = Request(
            self.url,
            data=json.dumps(payload).encode("utf-8"),
            headers=headers,
            method="POST",
        )
        with urlopen(request, timeout=self.timeout) as response:
            raw = response.read(MAX_RESPONSE_BYTES + 1)
        if len(raw) > MAX_RESPONSE_BYTES:
            raise ValueError("Provider response exceeds the size limit")
        data = json.loads(raw)
        if not isinstance(data, dict):
            raise ValueError("Provider response must be an object")
        choice = data["choices"][0]
        if choice.get("finish_reason") != "stop":
            raise ValueError("Provider response did not finish normally")
        content = choice["message"]["content"]
        if not isinstance(content, str):
            raise ValueError("Provider response must contain text")
        category = parse_category(json.loads(content))
        usage = data.get("usage") or {}
        return ProviderResult(
            category_id=category,
            model=data.get("model") or self.model,
            input_tokens=_tokens(usage.get("prompt_tokens")),
            output_tokens=_tokens(usage.get("completion_tokens")),
        )


class CliProvider:
    """Send one JSON request to a command and read one JSON result."""

    def __init__(
        self,
        *,
        command: Sequence[str],
        model: str,
        instructions: str,
        timeout: float = 30,
    ) -> None:
        if not command or not model or timeout <= 0:
            raise ValueError(
                "Command, model, and positive timeout are required"
            )
        self.command = list(command)
        self.model = model
        self.instructions = instructions
        self.timeout = timeout

    def __call__(self, article: ArticleInput) -> ProviderResult:
        payload = json.dumps(
            {
                "model": self.model,
                "instructions": self.instructions,
                "article": json.loads(article_json(article)),
            },
            ensure_ascii=False,
        )
        with tempfile.TemporaryFile() as output:
            subprocess.run(
                self.command,
                input=payload.encode("utf-8"),
                stdout=output,
                stderr=subprocess.DEVNULL,
                timeout=self.timeout,
                check=True,
            )
            output.seek(0)
            raw = output.read(MAX_RESPONSE_BYTES + 1)
        if len(raw) > MAX_RESPONSE_BYTES:
            raise ValueError("Provider response exceeds the size limit")
        data = json.loads(raw)
        if not isinstance(data, dict):
            raise ValueError("Provider response must be an object")
        category = parse_category({"category_id": data["category_id"]})
        return ProviderResult(
            category_id=category,
            model=data.get("model") or self.model,
            input_tokens=_tokens(data.get("input_tokens")),
            output_tokens=_tokens(data.get("output_tokens")),
        )
