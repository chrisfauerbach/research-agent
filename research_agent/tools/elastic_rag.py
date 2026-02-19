"""ElasticRagTool stub — interface only, no Elasticsearch dependency required.

Implement this tool when you want to integrate an Elasticsearch-backed RAG pipeline.
"""

from __future__ import annotations

import logging
from typing import Any

from research_agent.tools.base import BaseTool, ToolResult

logger = logging.getLogger(__name__)


class ElasticRagTool(BaseTool):
    name = "elastic_rag"
    description = (
        "Query an Elasticsearch RAG index for relevant documents. "
        "(Stub — not yet implemented.)"
    )

    async def run(self, *, query: str, **kwargs: Any) -> ToolResult:
        logger.info("ElasticRagTool called but not implemented; query=%s", query)
        return ToolResult(
            tool=self.name,
            success=False,
            data=(
                "ElasticRagTool is a stub. To use it, provide an Elasticsearch "
                "connection and implement the search logic in this file."
            ),
        )
