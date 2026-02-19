"""Research endpoint."""

from __future__ import annotations

import uuid
from typing import Literal

from fastapi import APIRouter
from pydantic import BaseModel, Field

from research_agent.graph.builder import build_graph
from research_agent.graph.state import AgentState
from research_agent.memory.store import RunStore
from research_agent.report.renderer import render_report
from research_agent.util.logging import setup_logging

router = APIRouter()


class ResearchRequest(BaseModel):
    question: str
    audience: Literal["engineer", "executive"] = "engineer"
    desired_depth: str = "thorough"
    max_iters: int = Field(default=6, ge=1, le=20)
    timebox_minutes: int = Field(default=5, ge=1, le=60)


class ResearchResponse(BaseModel):
    run_id: str
    question: str
    report: str
    evidence_count: int
    iterations: int


@router.post("/research", response_model=ResearchResponse)
async def run_research(req: ResearchRequest) -> ResearchResponse:
    run_id = uuid.uuid4().hex[:12]
    logger = setup_logging(run_id)
    logger.info("Starting research: %s", req.question)

    initial_state = AgentState(
        question=req.question,
        audience=req.audience,
        desired_depth=req.desired_depth,
        max_iters=req.max_iters,
        timebox_minutes=req.timebox_minutes,
        run_id=run_id,
    )

    graph = build_graph()
    final_state_dict = await graph.ainvoke(initial_state.model_dump())
    final_state = AgentState.model_validate(final_state_dict)

    final_state.report = render_report(final_state)

    store = RunStore()
    store.save(final_state)

    return ResearchResponse(
        run_id=run_id,
        question=req.question,
        report=final_state.report,
        evidence_count=len(final_state.evidence),
        iterations=final_state.iteration,
    )


@router.get("/runs")
async def list_runs() -> list[dict]:
    store = RunStore()
    return store.list_runs()


@router.get("/runs/{run_id}")
async def get_run(run_id: str) -> dict:
    store = RunStore()
    state = store.get(run_id)
    if state is None:
        return {"error": "Run not found"}
    return {
        "run_id": state.run_id,
        "question": state.question,
        "report": state.report,
        "evidence_count": len(state.evidence),
        "iterations": state.iteration,
    }
