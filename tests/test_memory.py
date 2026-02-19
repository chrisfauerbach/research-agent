"""Tests for the RunStore persistence layer."""

from __future__ import annotations

import tempfile

import pytest

from research_agent.graph.state import AgentState
from research_agent.memory.store import RunStore


def test_save_and_get() -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
        store = RunStore(db_path=f"{tmpdir}/test.db")
        state = AgentState(run_id="abc123", question="test?", report="# Report")
        store.save(state)
        loaded = store.get("abc123")
        assert loaded is not None
        assert loaded.question == "test?"
        assert loaded.report == "# Report"


def test_list_runs() -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
        store = RunStore(db_path=f"{tmpdir}/test.db")
        for i in range(3):
            state = AgentState(run_id=f"run-{i}", question=f"q{i}", report="r")
            store.save(state)
        runs = store.list_runs()
        assert len(runs) == 3


def test_get_missing() -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
        store = RunStore(db_path=f"{tmpdir}/test.db")
        assert store.get("nonexistent") is None
