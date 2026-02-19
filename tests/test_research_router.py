"""Tests for the research API router."""

from __future__ import annotations

import json
from io import BytesIO
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from research_agent.api.app import app
from research_agent.api.routers.research import (
    _build_initial_state,
    _sse_event,
    _status_from_state,
)
from research_agent.graph.state import AgentState
from research_agent.tools.base import EvidenceItem


client = TestClient(app)


# ---------------------------------------------------------------------------
# _sse_event
# ---------------------------------------------------------------------------


def test_sse_event_format():
    result = _sse_event("status", {"node": "plan"})
    assert result.startswith("event: status\n")
    assert "data: " in result
    assert result.endswith("\n\n")
    payload = json.loads(result.split("data: ", 1)[1].strip())
    assert payload == {"node": "plan"}


# ---------------------------------------------------------------------------
# _status_from_state
# ---------------------------------------------------------------------------


def test_status_from_state_extracts_fields():
    state = {
        "status": "acting",
        "iteration": 2,
        "current_step_index": 1,
        "plan": ["step1", "step2", "step3"],
        "pending_tool": "web_search",
        "evidence": [{"title": "a"}],
        "confidence": 0.75,
    }
    result = _status_from_state("act", state)
    assert result["node"] == "act"
    assert result["status"] == "acting"
    assert result["iteration"] == 2
    assert result["step_index"] == 1
    assert result["total_steps"] == 3
    assert result["tool"] == "web_search"
    assert result["evidence_count"] == 1
    assert result["confidence"] == 0.75


def test_status_from_state_defaults():
    result = _status_from_state("plan", {})
    assert result["status"] == ""
    assert result["iteration"] == 0
    assert result["total_steps"] == 0
    assert result["tool"] == ""
    assert result["evidence_count"] == 0
    assert result["confidence"] == 0.0
    assert "metrics" not in result


def test_status_from_state_includes_metrics():
    from research_agent.graph.state import LLMCallMetric, RunMetrics

    metrics = RunMetrics(
        llm_calls=[LLMCallMetric(node="plan", prompt_tokens=100, completion_tokens=50)]
    )
    state = {"status": "acting", "metrics": metrics}
    result = _status_from_state("plan", state)
    assert "metrics" in result
    assert result["metrics"]["total_prompt_tokens"] == 100
    assert result["metrics"]["total_completion_tokens"] == 50


# ---------------------------------------------------------------------------
# _build_initial_state
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_build_initial_state_no_pdf():
    state = await _build_initial_state(
        question="test?",
        audience="engineer",
        desired_depth="thorough",
        max_iters=3,
        timebox_minutes=2,
        run_id="abc123",
        pdf_file=None,
        run_logger=MagicMock(),
    )
    assert isinstance(state, AgentState)
    assert state.question == "test?"
    assert state.run_id == "abc123"
    assert state.pdf_context == ""
    assert state.evidence == []


@pytest.mark.asyncio
async def test_build_initial_state_invalid_extension():
    mock_file = AsyncMock()
    mock_file.filename = "report.txt"
    with pytest.raises(Exception) as exc_info:
        await _build_initial_state(
            question="q",
            audience="engineer",
            desired_depth="thorough",
            max_iters=3,
            timebox_minutes=2,
            run_id="x",
            pdf_file=mock_file,
            run_logger=MagicMock(),
        )
    assert exc_info.value.status_code == 400
    assert "Only .pdf" in exc_info.value.detail


@pytest.mark.asyncio
async def test_build_initial_state_pdf_too_large():
    mock_file = AsyncMock()
    mock_file.filename = "big.pdf"
    mock_file.read = AsyncMock(return_value=b"x" * (21 * 1024 * 1024))
    with pytest.raises(Exception) as exc_info:
        await _build_initial_state(
            question="q",
            audience="engineer",
            desired_depth="thorough",
            max_iters=3,
            timebox_minutes=2,
            run_id="x",
            pdf_file=mock_file,
            run_logger=MagicMock(),
        )
    assert exc_info.value.status_code == 413


@pytest.mark.asyncio
async def test_build_initial_state_pdf_parse_error():
    mock_file = AsyncMock()
    mock_file.filename = "bad.pdf"
    mock_file.read = AsyncMock(return_value=b"not a pdf")
    with patch(
        "research_agent.api.routers.research.extract_text_from_pdf",
        side_effect=ValueError("parse error"),
    ):
        with pytest.raises(Exception) as exc_info:
            await _build_initial_state(
                question="q",
                audience="engineer",
                desired_depth="thorough",
                max_iters=3,
                timebox_minutes=2,
                run_id="x",
                pdf_file=mock_file,
                run_logger=MagicMock(),
            )
        assert exc_info.value.status_code == 400
        assert "parse error" in exc_info.value.detail


@pytest.mark.asyncio
async def test_build_initial_state_pdf_success():
    mock_file = AsyncMock()
    mock_file.filename = "doc.pdf"
    mock_file.read = AsyncMock(return_value=b"pdf bytes")
    with patch(
        "research_agent.api.routers.research.extract_text_from_pdf",
        return_value="Extracted text from PDF page 1.",
    ):
        state = await _build_initial_state(
            question="q",
            audience="engineer",
            desired_depth="thorough",
            max_iters=3,
            timebox_minutes=2,
            run_id="x",
            pdf_file=mock_file,
            run_logger=MagicMock(),
        )
    assert state.pdf_context == "Extracted text from PDF page 1."
    assert state.pdf_filename == "doc.pdf"
    assert len(state.evidence) == 1
    assert state.evidence[0].url == "upload://doc.pdf"
    assert len(state.bibliography) == 1


# ---------------------------------------------------------------------------
# POST /api/research — JSON path
# ---------------------------------------------------------------------------


def test_run_research_json_path():
    mock_state = AgentState(
        question="test?",
        run_id="r1",
        report="## Report\nDone.",
        iteration=2,
        evidence=[EvidenceItem.now(title="E1", url="http://e.com", snippet="s")],
        status="done",
    )

    with (
        patch("research_agent.api.routers.research.build_graph") as mock_build,
        patch("research_agent.api.routers.research.RunStore") as mock_store_cls,
        patch(
            "research_agent.api.routers.research.render_report",
            return_value="## Rendered Report",
        ),
    ):
        mock_graph = AsyncMock()
        mock_graph.ainvoke = AsyncMock(return_value=mock_state.model_dump())
        mock_build.return_value = mock_graph
        mock_store_cls.return_value = MagicMock()

        resp = client.post(
            "/api/research",
            data={"question": "test?", "audience": "engineer"},
        )

    assert resp.status_code == 200
    body = resp.json()
    assert body["question"] == "test?"
    assert body["report"] == "## Rendered Report"
    assert body["evidence_count"] == 1


# ---------------------------------------------------------------------------
# POST /api/research — SSE path
# ---------------------------------------------------------------------------


def test_run_research_sse_path():
    mock_state = AgentState(
        question="test?",
        run_id="r1",
        report="## SSE Report",
        iteration=1,
        status="done",
    )

    async def mock_astream(state_dict, stream_mode=None):
        yield {"plan": {"plan": ["1. [web_search] test"], "status": "acting"}}

    with (
        patch("research_agent.api.routers.research.build_graph") as mock_build,
        patch("research_agent.api.routers.research.RunStore") as mock_store_cls,
        patch(
            "research_agent.api.routers.research.render_report",
            return_value="## Rendered",
        ),
    ):
        mock_graph = MagicMock()
        mock_graph.astream = mock_astream
        mock_build.return_value = mock_graph
        mock_store_cls.return_value = MagicMock()

        resp = client.post(
            "/api/research",
            data={"question": "test?"},
            headers={"accept": "text/event-stream"},
        )

    assert resp.status_code == 200
    assert "text/event-stream" in resp.headers["content-type"]
    body = resp.text
    assert "event: status" in body


# ---------------------------------------------------------------------------
# GET /api/runs
# ---------------------------------------------------------------------------


def test_list_runs():
    with patch("research_agent.api.routers.research.RunStore") as mock_cls:
        mock_cls.return_value.list_runs.return_value = [
            {"run_id": "a", "question": "q?", "created_at": "2024-01-01"}
        ]
        resp = client.get("/api/runs")

    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["run_id"] == "a"


# ---------------------------------------------------------------------------
# GET /api/runs/{run_id}
# ---------------------------------------------------------------------------


def test_get_run_found():
    state = AgentState(
        question="q?",
        run_id="found1",
        report="rpt",
        iteration=3,
        evidence=[EvidenceItem.now(title="T", url="u", snippet="s")],
    )
    with patch("research_agent.api.routers.research.RunStore") as mock_cls:
        mock_cls.return_value.get.return_value = state
        mock_cls.return_value.get_created_at.return_value = "2024-01-01T00:00:00"
        resp = client.get("/api/runs/found1")

    assert resp.status_code == 200
    body = resp.json()
    assert body["run_id"] == "found1"
    assert body["evidence_count"] == 1
    assert "metrics" in body
    assert body["metrics"]["total_llm_calls"] == 0  # empty RunMetrics default


def test_get_run_not_found():
    with patch("research_agent.api.routers.research.RunStore") as mock_cls:
        mock_cls.return_value.get.return_value = None
        resp = client.get("/api/runs/missing")

    assert resp.status_code == 404
