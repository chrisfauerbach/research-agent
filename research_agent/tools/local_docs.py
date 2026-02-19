"""Read from local ./docs and ./data directories for offline corpora."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from research_agent.tools.base import BaseTool, EvidenceItem, ToolResult

logger = logging.getLogger(__name__)

SEARCH_DIRS = [Path("docs"), Path("data")]
MAX_FILE_CHARS = 10_000


class LocalDocsTool(BaseTool):
    name = "local_docs"
    description = "Search local docs/ and data/ directories for relevant files."

    async def run(self, *, query: str, **kwargs: Any) -> ToolResult:
        query_lower = query.lower()
        logger.info("LocalDocs: searching for '%s'", query)

        matches: list[str] = []
        evidence: list[EvidenceItem] = []

        for search_dir in SEARCH_DIRS:
            if not search_dir.exists():
                continue
            for fpath in search_dir.rglob("*"):
                if not fpath.is_file():
                    continue
                if fpath.suffix not in {".md", ".txt", ".json", ".csv", ".yaml", ".yml"}:
                    continue
                try:
                    content = fpath.read_text(errors="replace")
                except Exception:
                    continue

                if query_lower in content.lower() or query_lower in fpath.name.lower():
                    snippet = content[:MAX_FILE_CHARS]
                    matches.append(f"### {fpath}\n{snippet}")
                    evidence.append(
                        EvidenceItem.now(
                            title=fpath.name,
                            url=str(fpath),
                            snippet=snippet[:300],
                        )
                    )

        if not matches:
            return ToolResult(
                tool=self.name, success=True, data="No matching local documents found."
            )

        return ToolResult(
            tool=self.name,
            success=True,
            data="\n\n".join(matches),
            evidence=evidence,
        )
