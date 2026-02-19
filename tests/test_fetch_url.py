"""Tests for the fetch_url tool."""

from __future__ import annotations

from unittest.mock import patch

import httpx
import pytest
import respx

from research_agent.tools.fetch_url import FetchUrlTool, MAX_CONTENT_CHARS


@pytest.mark.asyncio
@respx.mock
async def test_fetch_url_success():
    respx.get("http://example.com/page").mock(
        return_value=httpx.Response(200, text="<html><body>Hello World</body></html>")
    )
    with patch("research_agent.tools.fetch_url.trafilatura") as mock_traf:
        mock_traf.extract.return_value = "Hello World extracted"
        tool = FetchUrlTool()
        result = await tool.run(query="http://example.com/page")

    assert result.success
    assert "Hello World extracted" in result.data
    assert len(result.evidence) == 1
    assert result.evidence[0].url == "http://example.com/page"


@pytest.mark.asyncio
@respx.mock
async def test_fetch_url_trafilatura_returns_none():
    html = "<html><body>Raw content here</body></html>"
    respx.get("http://example.com/raw").mock(
        return_value=httpx.Response(200, text=html)
    )
    with patch("research_agent.tools.fetch_url.trafilatura") as mock_traf:
        mock_traf.extract.return_value = None
        tool = FetchUrlTool()
        result = await tool.run(query="http://example.com/raw")

    assert result.success
    # Should fall back to raw text
    assert "Raw content here" in result.data


@pytest.mark.asyncio
@respx.mock
async def test_fetch_url_http_error():
    respx.get("http://example.com/404").mock(
        return_value=httpx.Response(404, text="Not Found")
    )
    tool = FetchUrlTool()
    result = await tool.run(query="http://example.com/404")

    assert not result.success


@pytest.mark.asyncio
async def test_fetch_url_connection_error():
    with respx.mock:
        respx.get("http://unreachable.invalid/page").mock(
            side_effect=httpx.ConnectError("Connection refused")
        )
        tool = FetchUrlTool()
        result = await tool.run(query="http://unreachable.invalid/page")

    assert not result.success
    assert "Connection refused" in result.data


@pytest.mark.asyncio
@respx.mock
async def test_fetch_url_truncation():
    long_text = "A" * (MAX_CONTENT_CHARS + 5000)
    respx.get("http://example.com/long").mock(
        return_value=httpx.Response(200, text=long_text)
    )
    with patch("research_agent.tools.fetch_url.trafilatura") as mock_traf:
        mock_traf.extract.return_value = long_text
        tool = FetchUrlTool()
        result = await tool.run(query="http://example.com/long")

    assert result.success
    assert len(result.data) == MAX_CONTENT_CHARS
