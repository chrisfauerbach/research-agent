"""Shared fixtures — mock Ollama client for integration tests."""

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

import research_agent.llm.adapter as adapter_mod
from research_agent.llm.adapter import LLMAdapter
from research_agent.llm.client import LLMResponse, OllamaClient


def _make_llm_response(text: str) -> LLMResponse:
    """Build an LLMResponse with realistic token/timing data."""
    return LLMResponse(
        text=text,
        prompt_eval_count=100,
        eval_count=50,
        total_duration_ns=500_000_000,
        prompt_eval_duration_ns=200_000_000,
        eval_duration_ns=300_000_000,
    )


@pytest.fixture()
def mock_ollama(monkeypatch: pytest.MonkeyPatch) -> AsyncMock:
    """Replace the global LLM adapter with a mock that returns canned responses."""
    mock_client = AsyncMock(spec=OllamaClient)

    # Default: return a sensible plan, then stub summaries
    call_count = 0

    async def _generate(prompt: str, **kwargs) -> LLMResponse:  # type: ignore[override]
        nonlocal call_count
        call_count += 1

        # First call → plan
        if call_count == 1:
            return _make_llm_response(
                "1. [web_search] best practices for deploying LLMs\n"
                "2. [web_search] LLM inference optimization techniques\n"
                "3. [fetch_url] https://example.com/llm-guide\n"
            )
        # Act calls
        if "TOOL:" in prompt or "Extract the tool" in prompt:
            return _make_llm_response("TOOL: web_search\nQUERY: LLM deployment best practices")
        # Observe
        if "Summarise" in prompt:
            return _make_llm_response(
                "Key finding: containerized deployments with GPU support are recommended."
            )
        # Reflect
        if "continue researching or write" in prompt:
            return _make_llm_response(
                "DECISION: STOP\nCONFIDENCE: 0.8\nREASON: Sufficient evidence gathered."
            )
        # Write report
        return _make_llm_response(
            "## Summary\nTest summary.\n\n"
            "## Key Findings\n- Finding 1\n\n"
            "## Recommendations\n- Use containers\n\n"
            "## Architecture Diagram\n```mermaid\ngraph TD\n    A-->B\n```\n\n"
            "## Sources\n1. Example source\n"
        )

    mock_client.generate = _generate

    mock_adapter = LLMAdapter(client=mock_client)
    monkeypatch.setattr(adapter_mod, "_instance", mock_adapter)
    return mock_client
