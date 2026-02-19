"""Single LLM adapter used everywhere in the codebase."""

from __future__ import annotations

import logging

from research_agent.llm.client import OllamaClient

logger = logging.getLogger(__name__)

# Module-level singleton; import and call get_llm() everywhere.
_instance: LLMAdapter | None = None


class LLMAdapter:
    """High-level interface that the rest of the codebase calls."""

    def __init__(self, client: OllamaClient | None = None) -> None:
        self.client = client or OllamaClient()

    async def query(
        self,
        prompt: str,
        *,
        system: str | None = None,
        temperature: float = 0.3,
        max_tokens: int = 4096,
    ) -> str:
        return await self.client.generate(
            prompt, system=system, temperature=temperature, max_tokens=max_tokens
        )


def get_llm(client: OllamaClient | None = None) -> LLMAdapter:
    global _instance
    if _instance is None:
        _instance = LLMAdapter(client)
    return _instance
