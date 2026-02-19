"""Fetch a URL and extract main text content."""

from __future__ import annotations

import logging
from typing import Any

import httpx
import trafilatura

from research_agent.tools.base import BaseTool, EvidenceItem, ToolResult

logger = logging.getLogger(__name__)

MAX_CONTENT_CHARS = 12_000


class FetchUrlTool(BaseTool):
    name = "fetch_url"
    description = "Fetch a URL and extract its main textual content."

    async def run(self, *, query: str, **kwargs: Any) -> ToolResult:
        url = query.strip()
        logger.info("FetchUrl: %s", url)
        try:
            async with httpx.AsyncClient(timeout=30, follow_redirects=True) as client:
                resp = await client.get(url)
                resp.raise_for_status()
        except Exception as exc:
            logger.warning("FetchUrl failed for %s: %s", url, exc)
            return ToolResult(tool=self.name, success=False, data=str(exc))

        text = trafilatura.extract(resp.text) or resp.text[:MAX_CONTENT_CHARS]
        text = text[:MAX_CONTENT_CHARS]

        title = url.split("/")[2] if "/" in url else url
        evidence = [EvidenceItem.now(title=title, url=url, snippet=text[:300])]

        return ToolResult(
            tool=self.name,
            success=True,
            data=text,
            evidence=evidence,
        )
