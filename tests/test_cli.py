"""Tests for the CLI entry point."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from typer.testing import CliRunner

from research_agent.cli.main import _run, app
from research_agent.graph.state import AgentState
from research_agent.tools.base import EvidenceItem

runner = CliRunner()


# ---------------------------------------------------------------------------
# _run() — raw output
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_run_raw_output():
    final_state = AgentState(
        question="q?",
        run_id="r1",
        report="## Raw",
        iteration=2,
        evidence=[EvidenceItem.now(title="E", url="u", snippet="s")],
        status="done",
    )

    mock_graph = AsyncMock()
    mock_graph.ainvoke = AsyncMock(return_value=final_state.model_dump())

    with (
        patch("research_agent.graph.builder.build_graph", return_value=mock_graph),
        patch("research_agent.memory.store.RunStore") as mock_store_cls,
        patch("research_agent.report.renderer.render_report", return_value="## Rendered"),
        patch("research_agent.util.logging.setup_logging", return_value=MagicMock()),
    ):
        mock_store_cls.return_value = MagicMock()
        await _run("q?", "engineer", "thorough", 3, 2, raw=True)


# ---------------------------------------------------------------------------
# _run() — rich output
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_run_rich_output():
    final_state = AgentState(
        question="q?",
        run_id="r1",
        report="## Rich",
        iteration=1,
        status="done",
    )

    mock_graph = AsyncMock()
    mock_graph.ainvoke = AsyncMock(return_value=final_state.model_dump())

    with (
        patch("research_agent.graph.builder.build_graph", return_value=mock_graph),
        patch("research_agent.memory.store.RunStore") as mock_store_cls,
        patch("research_agent.report.renderer.render_report", return_value="## Rich Report"),
        patch("research_agent.util.logging.setup_logging", return_value=MagicMock()),
    ):
        mock_store_cls.return_value = MagicMock()
        await _run("q?", "engineer", "thorough", 3, 2, raw=False)


# ---------------------------------------------------------------------------
# CLI: research command via CliRunner
# ---------------------------------------------------------------------------


def test_research_command():
    with patch("research_agent.cli.main.asyncio") as mock_asyncio:
        mock_asyncio.run = MagicMock()
        result = runner.invoke(app, ["research", "What is AI?", "--raw"])

    assert result.exit_code == 0


# ---------------------------------------------------------------------------
# CLI: runs command
# ---------------------------------------------------------------------------


def test_runs_command():
    with patch("research_agent.memory.store.RunStore") as mock_cls:
        mock_cls.return_value.list_runs.return_value = [
            {"run_id": "a", "question": "q?", "created_at": "2024-01-01"},
        ]
        result = runner.invoke(app, ["runs"])

    assert result.exit_code == 0


def test_runs_command_empty():
    with patch("research_agent.memory.store.RunStore") as mock_cls:
        mock_cls.return_value.list_runs.return_value = []
        result = runner.invoke(app, ["runs"])

    assert result.exit_code == 0
