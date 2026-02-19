"""Tests for the low-level Ollama HTTP client."""

from __future__ import annotations

from unittest.mock import patch

import httpx
import pytest
import respx

from research_agent.llm.client import OllamaClient


def test_init_defaults():
    with patch("research_agent.llm.client.settings") as mock_settings:
        mock_settings.ollama_host = "http://localhost:11434"
        mock_settings.ollama_model = "gemma3:12b"
        mock_settings.ollama_timeout_seconds = 300
        client = OllamaClient()

    assert client.host == "http://localhost:11434"
    assert client.model == "gemma3:12b"
    assert client.timeout == 300


def test_init_custom():
    client = OllamaClient(host="http://custom:1234/", model="llama3", timeout=60)
    assert client.host == "http://custom:1234"  # trailing slash stripped
    assert client.model == "llama3"
    assert client.timeout == 60


@pytest.mark.asyncio
@respx.mock
async def test_generate_success():
    route = respx.post("http://test:11434/api/generate").mock(
        return_value=httpx.Response(200, json={"response": "Hello world"})
    )
    client = OllamaClient(host="http://test:11434", model="test-model", timeout=10)
    result = await client.generate("Say hello")

    assert result == "Hello world"
    assert route.called


@pytest.mark.asyncio
@respx.mock
async def test_generate_with_system():
    route = respx.post("http://test:11434/api/generate").mock(
        return_value=httpx.Response(200, json={"response": "sys reply"})
    )
    client = OllamaClient(host="http://test:11434", model="m", timeout=10)
    result = await client.generate("prompt", system="You are helpful")

    assert result == "sys reply"
    # Verify system was included in the request
    request_body = route.calls[0].request.content
    import json

    payload = json.loads(request_body)
    assert payload["system"] == "You are helpful"


@pytest.mark.asyncio
@respx.mock
async def test_generate_no_system():
    route = respx.post("http://test:11434/api/generate").mock(
        return_value=httpx.Response(200, json={"response": "no sys"})
    )
    client = OllamaClient(host="http://test:11434", model="m", timeout=10)
    result = await client.generate("prompt")

    import json

    payload = json.loads(route.calls[0].request.content)
    assert "system" not in payload


@pytest.mark.asyncio
@respx.mock
async def test_generate_empty_response():
    respx.post("http://test:11434/api/generate").mock(
        return_value=httpx.Response(200, json={})
    )
    client = OllamaClient(host="http://test:11434", model="m", timeout=10)
    result = await client.generate("prompt")
    assert result == ""


@pytest.mark.asyncio
@respx.mock
async def test_generate_http_error():
    respx.post("http://test:11434/api/generate").mock(
        return_value=httpx.Response(500, text="Internal Server Error")
    )
    client = OllamaClient(host="http://test:11434", model="m", timeout=10)
    with pytest.raises(httpx.HTTPStatusError):
        await client.generate("prompt")
