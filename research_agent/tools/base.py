"""Base class for all agent tools."""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel


class ToolResult(BaseModel):
    """Standardised result returned by every tool."""

    tool: str
    success: bool
    data: str
    evidence: list[EvidenceItem] = []


class EvidenceItem(BaseModel):
    title: str
    url: str = ""
    snippet: str = ""
    retrieved_at: str = ""

    @classmethod
    def now(cls, **kwargs: Any) -> EvidenceItem:
        return cls(
            retrieved_at=datetime.now(timezone.utc).isoformat(),
            **kwargs,
        )


# Rebuild ToolResult so forward-ref to EvidenceItem resolves.
ToolResult.model_rebuild()


class BaseTool(ABC):
    """Interface every tool must implement."""

    name: str = "base"
    description: str = ""

    @abstractmethod
    async def run(self, *, query: str, **kwargs: Any) -> ToolResult:
        ...
