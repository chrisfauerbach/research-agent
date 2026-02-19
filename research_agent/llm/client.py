"""Low-level Ollama HTTP client using /api/generate."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

import httpx

from research_agent.config import settings

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class LLMResponse:
    """Structured response from an Ollama generate call."""

    text: str = ""
    prompt_eval_count: int = 0
    eval_count: int = 0
    total_duration_ns: int = 0
    prompt_eval_duration_ns: int = 0
    eval_duration_ns: int = 0


class OllamaClient:
    """Thin wrapper around Ollama's /api/generate endpoint."""

    def __init__(
        self,
        host: str | None = None,
        model: str | None = None,
        timeout: int | None = None,
    ) -> None:
        self.host = (host or settings.ollama_host).rstrip("/")
        self.model = model or settings.ollama_model
        self.timeout = timeout or settings.ollama_timeout_seconds

    async def generate(
        self,
        prompt: str,
        *,
        system: str | None = None,
        temperature: float = 0.3,
        max_tokens: int = 4096,
    ) -> LLMResponse:
        """Send a prompt to Ollama and return a structured LLMResponse."""
        payload: dict[str, Any] = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
            },
        }
        if system:
            payload["system"] = system

        url = f"{self.host}/api/generate"
        logger.debug("POST %s model=%s prompt_len=%d", url, self.model, len(prompt))

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.post(url, json=payload)
            resp.raise_for_status()
            data = resp.json()

        text: str = data.get("response", "")
        logger.debug("Ollama response len=%d", len(text))
        return LLMResponse(
            text=text,
            prompt_eval_count=data.get("prompt_eval_count", 0),
            eval_count=data.get("eval_count", 0),
            total_duration_ns=data.get("total_duration", 0),
            prompt_eval_duration_ns=data.get("prompt_eval_duration", 0),
            eval_duration_ns=data.get("eval_duration", 0),
        )
