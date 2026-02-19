"""Tests for the web_search tool."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from research_agent.tools.web_search import WebSearchTool


@pytest.mark.asyncio
async def test_web_search_success():
    mock_results = [
        {"title": "Result 1", "href": "http://example.com/1", "body": "snippet 1"},
        {"title": "Result 2", "href": "http://example.com/2", "body": "snippet 2"},
    ]
    with patch("research_agent.tools.web_search.DDGS") as mock_ddgs:
        mock_ddgs.return_value.text.return_value = mock_results
        tool = WebSearchTool(max_results=2)
        result = await tool.run(query="test query")

    assert result.success
    assert "Result 1" in result.data
    assert "Result 2" in result.data
    assert len(result.evidence) == 2
    assert result.evidence[0].url == "http://example.com/1"


@pytest.mark.asyncio
async def test_web_search_empty_results():
    with patch("research_agent.tools.web_search.DDGS") as mock_ddgs:
        mock_ddgs.return_value.text.return_value = []
        tool = WebSearchTool()
        result = await tool.run(query="nothing")

    assert result.success
    assert result.data == "No results found."
    assert result.evidence == []


@pytest.mark.asyncio
async def test_web_search_rate_limit_then_success():
    from duckduckgo_search.exceptions import RatelimitException

    mock_results = [{"title": "OK", "href": "http://ok.com", "body": "ok"}]

    call_count = 0

    def text_side_effect(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            raise RatelimitException("rate limited")
        return mock_results

    with (
        patch("research_agent.tools.web_search.DDGS") as mock_ddgs,
        patch("research_agent.tools.web_search.asyncio") as mock_asyncio,
    ):
        mock_ddgs.return_value.text.side_effect = text_side_effect
        mock_asyncio.sleep = MagicMock()  # make sleep a no-op coroutine

        # asyncio.sleep needs to be awaitable
        async def noop_sleep(s):
            pass

        mock_asyncio.sleep = noop_sleep

        tool = WebSearchTool()
        result = await tool.run(query="retry test")

    assert result.success
    assert "OK" in result.data


@pytest.mark.asyncio
async def test_web_search_rate_limit_exhausted():
    from duckduckgo_search.exceptions import RatelimitException

    with (
        patch("research_agent.tools.web_search.DDGS") as mock_ddgs,
        patch("research_agent.tools.web_search.asyncio") as mock_asyncio,
    ):
        mock_ddgs.return_value.text.side_effect = RatelimitException("rate limited")

        async def noop_sleep(s):
            pass

        mock_asyncio.sleep = noop_sleep

        tool = WebSearchTool()
        result = await tool.run(query="always limited")

    assert not result.success
    assert "rate-limited after" in result.data


@pytest.mark.asyncio
async def test_web_search_generic_exception():
    with patch("research_agent.tools.web_search.DDGS") as mock_ddgs:
        mock_ddgs.return_value.text.side_effect = RuntimeError("network down")
        tool = WebSearchTool()
        result = await tool.run(query="fail")

    assert not result.success
    assert "network down" in result.data
