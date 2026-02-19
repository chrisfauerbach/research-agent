"""Typed state for the research agent LangGraph state machine."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from research_agent.tools.base import EvidenceItem


class LLMCallMetric(BaseModel):
    """Metrics for a single LLM call."""

    node: str = ""
    prompt_tokens: int = 0
    completion_tokens: int = 0
    duration_ms: float = 0.0


class ToolCallMetric(BaseModel):
    """Metrics for a single tool invocation."""

    tool_name: str = ""
    query: str = ""
    duration_ms: float = 0.0
    success: bool = True


class NodeTimingMetric(BaseModel):
    """Wall-clock timing for a graph node."""

    node: str = ""
    duration_ms: float = 0.0


class RunMetrics(BaseModel):
    """Accumulated metrics for an entire research run."""

    llm_calls: list[LLMCallMetric] = Field(default_factory=list)
    tool_calls: list[ToolCallMetric] = Field(default_factory=list)
    node_timings: list[NodeTimingMetric] = Field(default_factory=list)

    @property
    def total_prompt_tokens(self) -> int:
        return sum(c.prompt_tokens for c in self.llm_calls)

    @property
    def total_completion_tokens(self) -> int:
        return sum(c.completion_tokens for c in self.llm_calls)

    @property
    def total_llm_calls(self) -> int:
        return len(self.llm_calls)

    @property
    def total_llm_time_ms(self) -> float:
        return sum(c.duration_ms for c in self.llm_calls)

    @property
    def total_tool_time_ms(self) -> float:
        return sum(c.duration_ms for c in self.tool_calls)

    @property
    def total_research_time_ms(self) -> float:
        return sum(n.duration_ms for n in self.node_timings)

    def summary(self) -> dict:
        """Return a JSON-serializable summary of all metrics."""
        return {
            "total_prompt_tokens": self.total_prompt_tokens,
            "total_completion_tokens": self.total_completion_tokens,
            "total_llm_calls": self.total_llm_calls,
            "total_llm_time_ms": round(self.total_llm_time_ms, 1),
            "total_tool_time_ms": round(self.total_tool_time_ms, 1),
            "total_research_time_ms": round(self.total_research_time_ms, 1),
            "llm_calls": [c.model_dump() for c in self.llm_calls],
            "tool_calls": [c.model_dump() for c in self.tool_calls],
            "node_timings": [n.model_dump() for n in self.node_timings],
        }


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
    status: Literal["planning", "acting", "observing", "reflecting", "writing", "done"] = "planning"
    should_stop: bool = False
    confidence: float = 0.0  # 0.0–1.0

    # Metrics
    metrics: RunMetrics = Field(default_factory=RunMetrics)

    # Output
    report: str = ""
