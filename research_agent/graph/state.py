"""Typed state for the research agent LangGraph state machine."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from research_agent.tools.base import EvidenceItem


class AgentState(BaseModel):
    """Full state carried through the graph."""

    # Input
    question: str = ""
    audience: Literal["engineer", "executive"] = "engineer"
    desired_depth: str = "thorough"
    max_iters: int = 6
    timebox_minutes: int = 5
    tool_call_limit: int = 30

    # Optional PDF reference document
    pdf_context: str = ""
    pdf_filename: str = ""

    # Tracking
    run_id: str = ""
    iteration: int = 0
    tool_calls_made: int = 0
    start_time: float = 0.0  # epoch seconds

    # Plan → Act → Observe → Reflect
    plan: list[str] = Field(default_factory=list)
    current_step_index: int = 0
    scratchpad: str = ""

    # Tool interaction
    pending_tool: str = ""
    pending_tool_query: str = ""
    last_tool_result: str = ""

    # Evidence & notes
    evidence: list[EvidenceItem] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)
    bibliography: dict[str, EvidenceItem] = Field(default_factory=dict)

    # Control flow
    status: Literal["planning", "acting", "observing", "reflecting", "writing", "done"] = (
        "planning"
    )
    should_stop: bool = False
    confidence: float = 0.0  # 0.0–1.0

    # Output
    report: str = ""
