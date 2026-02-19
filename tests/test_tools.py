"""Unit tests for tool implementations."""

from __future__ import annotations

import pytest

from research_agent.tools.base import EvidenceItem, ToolResult
from research_agent.tools.local_docs import LocalDocsTool
from research_agent.tools.python_sandbox import PythonSandboxTool


@pytest.mark.asyncio
async def test_python_sandbox_success() -> None:
    tool = PythonSandboxTool()
    result = await tool.run(query="print('hello world')")
    assert result.success
    assert "hello world" in result.data


@pytest.mark.asyncio
async def test_python_sandbox_error() -> None:
    tool = PythonSandboxTool()
    result = await tool.run(query="raise ValueError('boom')")
    assert not result.success
    assert "boom" in result.data


@pytest.mark.asyncio
async def test_local_docs_no_match(tmp_path) -> None:
    tool = LocalDocsTool()
    result = await tool.run(query="nonexistent_topic_xyz_123")
    assert result.success
    assert "No matching" in result.data


def test_evidence_item_now() -> None:
    ev = EvidenceItem.now(title="Test", url="http://example.com", snippet="snippet")
    assert ev.title == "Test"
    assert ev.retrieved_at != ""
