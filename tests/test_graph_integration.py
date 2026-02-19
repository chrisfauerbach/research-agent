"""Integration test for the full research graph using a mocked Ollama client."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from research_agent.graph.builder import build_graph
from research_agent.graph.state import AgentState
from research_agent.tools.base import EvidenceItem, ToolResult


@pytest.mark.asyncio
async def test_full_graph_with_mock_ollama(mock_ollama: AsyncMock) -> None:
    """Run the full graph end-to-end with mocked LLM and mocked tools."""

    mock_tool_result = ToolResult(
        tool="web_search",
        success=True,
        data="LLMs should be deployed in containers with GPU access.",
        evidence=[
            EvidenceItem.now(
                title="LLM Deployment Guide",
                url="https://example.com/guide",
                snippet="Deploy LLMs in containers.",
            )
        ],
    )

    with patch(
        "research_agent.graph.nodes.TOOL_REGISTRY",
        {
            "web_search": _make_mock_tool_cls(mock_tool_result),
            "fetch_url": _make_mock_tool_cls(mock_tool_result),
        },
    ):
        graph = build_graph()
        initial = AgentState(
            question="What are best practices for deploying LLMs?",
            max_iters=3,
            timebox_minutes=1,
            run_id="test-001",
        )
        result = await graph.ainvoke(initial.model_dump())

    state = AgentState.model_validate(result)
    assert state.status == "done"
    assert state.report != ""
    assert state.iteration >= 1
    assert state.metrics.total_llm_calls > 0
    assert len(state.metrics.node_timings) > 0
    assert state.metrics.total_prompt_tokens > 0


def _make_mock_tool_cls(result: ToolResult):  # type: ignore[no-untyped-def]
    """Create a mock tool class that returns a fixed result."""

    class MockTool:
        name = result.tool
        description = "mock"

        async def run(self, *, query: str, **kwargs) -> ToolResult:  # type: ignore[no-untyped-def]
            return result

    return MockTool
