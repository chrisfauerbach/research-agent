"""Web search via DuckDuckGo (ddgs)."""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from duckduckgo_search import DDGS
from duckduckgo_search.exceptions import RatelimitException

from research_agent.tools.base import BaseTool, EvidenceItem, ToolResult

logger = logging.getLogger(__name__)

MAX_RETRIES = 3
RETRY_BACKOFF_SECONDS = [2, 5, 10]


class WebSearchTool(BaseTool):
    name = "web_search"
    description = "Search the web using DuckDuckGo and return top results."

    def __init__(self, max_results: int = 5) -> None:
        self.max_results = max_results

    async def run(self, *, query: str, **kwargs: Any) -> ToolResult:
        logger.info("WebSearch: %s", query)
        results: list[dict[str, str]] = []
        for attempt in range(MAX_RETRIES):
            try:
                results = DDGS().text(query, max_results=self.max_results)
                break
            except RatelimitException:
                delay = RETRY_BACKOFF_SECONDS[attempt]
                logger.warning(
                    "WebSearch rate-limited (attempt %d/%d), retrying in %ds",
                    attempt + 1,
                    MAX_RETRIES,
                    delay,
                )
                await asyncio.sleep(delay)
            except Exception as exc:
                logger.warning("WebSearch failed: %s", exc)
                return ToolResult(tool=self.name, success=False, data=str(exc))
        else:
            msg = f"WebSearch rate-limited after {MAX_RETRIES} retries"
            logger.warning(msg)
            return ToolResult(tool=self.name, success=False, data=msg)

        evidence: list[EvidenceItem] = []
        lines: list[str] = []
        for r in results:
            title = r.get("title", "")
            url = r.get("href", "")
            snippet = r.get("body", "")
            lines.append(f"- [{title}]({url}): {snippet}")
            evidence.append(EvidenceItem.now(title=title, url=url, snippet=snippet))

        return ToolResult(
            tool=self.name,
            success=True,
            data="\n".join(lines) if lines else "No results found.",
            evidence=evidence,
        )
