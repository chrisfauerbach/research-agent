"""Low-level Ollama HTTP client using /api/generate."""

from __future__ import annotations

import logging
from typing import Any

import httpx

from research_agent.config import settings

logger = logging.getLogger(__name__)


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
    ) -> str:
        """Send a prompt to Ollama and return the full response text."""
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
        return text
