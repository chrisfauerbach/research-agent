"""Tests for the report renderer."""

from __future__ import annotations

from research_agent.graph.state import AgentState
from research_agent.report.renderer import render_report
from research_agent.tools.base import EvidenceItem


def _make_state(**overrides) -> AgentState:
    defaults = {"question": "q?", "run_id": "r1", "report": "## Summary\nTest."}
    defaults.update(overrides)
    return AgentState(**defaults)


def test_adds_sources():
    ev = EvidenceItem.now(title="Source A", url="http://a.com", snippet="s")
    state = _make_state(bibliography={"http://a.com": ev})
    result = render_report(state)
    assert "## Sources" in result
    assert "[Source A](http://a.com)" in result


def test_source_without_url():
    ev = EvidenceItem(title="Local Doc", url="", snippet="s", retrieved_at="")
    state = _make_state(bibliography={"local": ev})
    result = render_report(state)
    assert "## Sources" in result
    # Source without URL should just show title, not a link
    assert "Local Doc" in result
    assert "[Local Doc](" not in result


def test_skips_sources_if_present():
    state = _make_state(
        report="## Summary\nTest.\n\n## Sources\n1. Already here",
        bibliography={"http://a.com": EvidenceItem.now(title="A", url="http://a.com", snippet="s")},
    )
    result = render_report(state)
    # Should not add a second Sources section
    assert result.count("## Sources") == 1


def test_skips_sources_if_citations():
    state = _make_state(
        report="## Summary\nTest.\n\n## Citations\n1. Cited",
        bibliography={"http://a.com": EvidenceItem.now(title="A", url="http://a.com", snippet="s")},
    )
    result = render_report(state)
    assert "## Sources" not in result


def test_adds_mermaid_placeholder():
    state = _make_state(report="## Summary\nNo diagram here.")
    result = render_report(state)
    assert "```mermaid" in result
    assert "Architecture Diagram" in result


def test_skips_mermaid_if_present():
    state = _make_state(
        report="## Summary\nTest.\n\n```mermaid\ngraph TD\n    A-->B\n```"
    )
    result = render_report(state)
    # Should not add a second mermaid block
    assert result.count("```mermaid") == 1


def test_empty_bibliography():
    state = _make_state(bibliography={})
    result = render_report(state)
    # No sources section should be added when bibliography is empty
    assert "## Sources" not in result
