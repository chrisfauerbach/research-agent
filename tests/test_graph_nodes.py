"""Tests for individual graph node functions — targeting edge cases."""

from __future__ import annotations

import time
from unittest.mock import AsyncMock, patch

import pytest

from research_agent.graph.nodes import (
    act_node,
    plan_node,
    reflect_node,
    write_report_node,
)
from research_agent.graph.state import AgentState
from research_agent.llm.client import LLMResponse
from research_agent.tools.base import EvidenceItem, ToolResult


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


def _make_state(**overrides) -> AgentState:
    defaults = {
        "question": "What is X?",
        "run_id": "test-001",
        "start_time": time.time(),
    }
    defaults.update(overrides)
    return AgentState(**defaults)


# ---------------------------------------------------------------------------
# plan_node
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_plan_node_with_pdf_context(mock_ollama):
    state = _make_state(pdf_context="PDF content here", pdf_filename="doc.pdf")
    result = await plan_node(state)
    assert "plan" in result
    assert len(result["plan"]) > 0
    assert "metrics" in result
    assert len(result["metrics"].llm_calls) == 1
    assert result["metrics"].llm_calls[0].node == "plan"
    assert result["metrics"].llm_calls[0].prompt_tokens == 100


@pytest.mark.asyncio
async def test_plan_node_empty_llm_response(mock_ollama):
    mock_ollama.generate = AsyncMock(return_value=_make_llm_response(""))
    import research_agent.llm.adapter as adapter_mod
    from research_agent.llm.adapter import LLMAdapter

    adapter = LLMAdapter(client=mock_ollama)
    with patch.object(adapter_mod, "_instance", adapter):
        state = _make_state()
        result = await plan_node(state)

    # Fallback plan
    assert len(result["plan"]) == 1
    assert "web_search" in result["plan"][0]


# ---------------------------------------------------------------------------
# act_node
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_act_node_index_beyond_plan(mock_ollama):
    state = _make_state(
        plan=["1. [web_search] query"],
        current_step_index=5,  # beyond plan length
    )
    result = await act_node(state)
    assert result["status"] == "reflecting"
    assert result["last_tool_result"] == ""


@pytest.mark.asyncio
async def test_act_node_unknown_tool(mock_ollama):
    # LLM returns an unknown tool name
    mock_ollama.generate = AsyncMock(
        return_value=_make_llm_response("TOOL: nonexistent_tool\nQUERY: test")
    )
    import research_agent.llm.adapter as adapter_mod
    from research_agent.llm.adapter import LLMAdapter

    adapter = LLMAdapter(client=mock_ollama)

    mock_tool_result = ToolResult(
        tool="web_search",
        success=True,
        data="fallback result",
        evidence=[EvidenceItem.now(title="T", url="http://u.com", snippet="s")],
    )

    class MockTool:
        name = "web_search"

        async def run(self, *, query, **kwargs):
            return mock_tool_result

    with (
        patch.object(adapter_mod, "_instance", adapter),
        patch(
            "research_agent.graph.nodes.TOOL_REGISTRY",
            {"web_search": MockTool},
        ),
    ):
        state = _make_state(plan=["1. [unknown_tool] something"])
        result = await act_node(state)

    assert result["status"] == "observing"
    assert "fallback result" in result["last_tool_result"]


# ---------------------------------------------------------------------------
# reflect_node
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_reflect_node_timebox_exceeded(mock_ollama):
    state = _make_state(
        start_time=time.time() - 600,  # 10 mins ago
        timebox_minutes=1,
        iteration=0,
        plan=["step1"],
        current_step_index=1,
    )
    result = await reflect_node(state)
    assert result["should_stop"] is True
    assert result["status"] == "writing"


@pytest.mark.asyncio
async def test_reflect_node_iter_exceeded(mock_ollama):
    state = _make_state(
        iteration=6,
        max_iters=6,
        plan=["step1"],
        current_step_index=1,
    )
    result = await reflect_node(state)
    assert result["should_stop"] is True


@pytest.mark.asyncio
async def test_reflect_node_tool_limit_exceeded(mock_ollama):
    state = _make_state(
        tool_calls_made=30,
        tool_call_limit=30,
        plan=["step1"],
        current_step_index=1,
    )
    result = await reflect_node(state)
    assert result["should_stop"] is True


@pytest.mark.asyncio
async def test_reflect_node_continue_with_remaining_steps(mock_ollama):
    state = _make_state(
        plan=["step1", "step2", "step3"],
        current_step_index=1,  # still have steps 2 and 3
        iteration=0,
    )
    result = await reflect_node(state)
    assert result["status"] == "acting"
    assert "should_stop" not in result


@pytest.mark.asyncio
async def test_reflect_node_continue_with_new_steps(mock_ollama):
    mock_ollama.generate = AsyncMock(
        return_value=_make_llm_response(
            "DECISION: CONTINUE\n"
            "REASON: Need more data.\n"
            "NEW_STEPS: 4. [web_search] extra query\n"
            "5. [fetch_url] http://example.com"
        )
    )
    import research_agent.llm.adapter as adapter_mod
    from research_agent.llm.adapter import LLMAdapter

    adapter = LLMAdapter(client=mock_ollama)
    with patch.object(adapter_mod, "_instance", adapter):
        state = _make_state(
            plan=["1. step one", "2. step two"],
            current_step_index=2,  # all steps done
            iteration=1,
        )
        result = await reflect_node(state)

    assert result["status"] == "acting"
    assert len(result["plan"]) == 4  # 2 original + 2 new


@pytest.mark.asyncio
async def test_reflect_node_stop_with_bad_confidence(mock_ollama):
    mock_ollama.generate = AsyncMock(
        return_value=_make_llm_response("DECISION: STOP\nCONFIDENCE: not_a_number\nREASON: Done.")
    )
    import research_agent.llm.adapter as adapter_mod
    from research_agent.llm.adapter import LLMAdapter

    adapter = LLMAdapter(client=mock_ollama)
    with patch.object(adapter_mod, "_instance", adapter):
        state = _make_state(
            plan=["1. step"],
            current_step_index=1,
            iteration=1,
        )
        result = await reflect_node(state)

    assert result["should_stop"] is True
    assert result["confidence"] == 0.7  # fallback default


# ---------------------------------------------------------------------------
# write_report_node
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_write_report_node_with_pdf(mock_ollama):
    state = _make_state(
        pdf_context="PDF doc text",
        pdf_filename="ref.pdf",
        notes=["note1"],
        bibliography={
            "http://a.com": EvidenceItem.now(title="A", url="http://a.com", snippet="s"),
        },
    )
    result = await write_report_node(state)
    assert "report" in result
    assert result["status"] == "done"


@pytest.mark.asyncio
async def test_write_report_node_dedup_bibliography(mock_ollama):
    ev = EvidenceItem.now(title="Dup", url="http://dup.com", snippet="s")
    state = _make_state(
        notes=["note"],
        bibliography={
            "http://dup.com": ev,
            "dup_key_2": EvidenceItem(
                title="Dup2", url="http://dup.com", snippet="s2", retrieved_at=""
            ),
        },
    )
    result = await write_report_node(state)
    assert result["status"] == "done"
