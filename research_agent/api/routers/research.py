"""Research endpoint."""

from __future__ import annotations

import json
import logging
import uuid
from collections.abc import AsyncGenerator
from typing import Literal

from fastapi import APIRouter, File, Form, HTTPException, Request, UploadFile
from pydantic import BaseModel
from starlette.responses import StreamingResponse

from research_agent.config import settings
from research_agent.graph.builder import build_graph
from research_agent.graph.state import AgentState
from research_agent.memory.store import RunStore
from research_agent.report.renderer import render_report
from research_agent.tools.base import EvidenceItem
from research_agent.util.logging import setup_logging
from research_agent.util.pdf import extract_text_from_pdf

router = APIRouter()
logger = logging.getLogger(__name__)


class ResearchResponse(BaseModel):
    run_id: str
    question: str
    report: str
    evidence_count: int
    iterations: int


async def _build_initial_state(
    question: str,
    audience: str,
    desired_depth: str,
    max_iters: int,
    timebox_minutes: int,
    run_id: str,
    pdf_file: UploadFile | None,
    run_logger: logging.Logger,
) -> AgentState:
    """Extract PDF (if any) and build the initial AgentState."""
    pdf_context = ""
    pdf_filename = ""
    initial_evidence: list[EvidenceItem] = []
    initial_bibliography: dict[str, EvidenceItem] = {}

    if pdf_file is not None:
        if not pdf_file.filename or not pdf_file.filename.lower().endswith(".pdf"):
            raise HTTPException(status_code=400, detail="Only .pdf files are accepted")

        pdf_bytes = await pdf_file.read()
        max_bytes = settings.pdf_max_size_mb * 1024 * 1024
        if len(pdf_bytes) > max_bytes:
            raise HTTPException(
                status_code=413,
                detail=f"PDF exceeds {settings.pdf_max_size_mb} MB limit",
            )

        try:
            pdf_context = extract_text_from_pdf(pdf_bytes, max_chars=settings.pdf_max_extract_chars)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

        pdf_filename = pdf_file.filename
        ev = EvidenceItem.now(
            title=pdf_filename,
            url=f"upload://{pdf_filename}",
            snippet=pdf_context[:300],
        )
        initial_evidence.append(ev)
        initial_bibliography[ev.url] = ev
        run_logger.info("PDF uploaded: %s (%d chars extracted)", pdf_filename, len(pdf_context))

    return AgentState(
        question=question,
        audience=audience,
        desired_depth=desired_depth,
        max_iters=max_iters,
        timebox_minutes=timebox_minutes,
        run_id=run_id,
        pdf_context=pdf_context,
        pdf_filename=pdf_filename,
        evidence=initial_evidence,
        bibliography=initial_bibliography,
    )


def _sse_event(event: str, data: dict) -> str:
    """Format a single SSE event."""
    return f"event: {event}\ndata: {json.dumps(data)}\n\n"


def _status_from_state(node: str, state: dict) -> dict:
    """Build a status payload from node name and current state dict."""
    return {
        "node": node,
        "status": state.get("status", ""),
        "iteration": state.get("iteration", 0),
        "step_index": state.get("current_step_index", 0),
        "total_steps": len(state.get("plan", [])),
        "tool": state.get("pending_tool", ""),
        "evidence_count": len(state.get("evidence", [])),
        "confidence": state.get("confidence", 0.0),
    }


async def _stream_research(initial_state: AgentState, run_id: str) -> AsyncGenerator[str, None]:
    """Async generator that yields SSE events as the graph executes."""
    graph = build_graph()
    state_dict = initial_state.model_dump()

    # Emit initial status
    yield _sse_event("status", _status_from_state("plan", state_dict))

    try:
        async for chunk in graph.astream(state_dict, stream_mode="updates"):
            # chunk is {node_name: update_dict}
            for node_name, update in chunk.items():
                # Merge update into running state
                state_dict.update(update)

                # After plan node, emit the plan steps
                if node_name == "plan" and "plan" in update:
                    yield _sse_event("plan", {"steps": update["plan"]})

                # Emit status after every node
                yield _sse_event("status", _status_from_state(node_name, state_dict))

        # Graph completed — render report, save, emit complete
        final_state = AgentState.model_validate(state_dict)
        final_state.report = render_report(final_state)

        store = RunStore()
        store.save(final_state)

        yield _sse_event(
            "complete",
            {
                "run_id": run_id,
                "question": final_state.question,
                "report": final_state.report,
                "evidence_count": len(final_state.evidence),
                "iterations": final_state.iteration,
            },
        )
    except Exception as exc:
        logger.exception("Streaming research failed for run %s", run_id)
        yield _sse_event("error", {"message": str(exc)})


@router.post("/research")
async def run_research(
    request: Request,
    question: str = Form(...),
    audience: Literal["engineer", "executive"] = Form("engineer"),
    desired_depth: str = Form("thorough"),
    max_iters: int = Form(6),
    timebox_minutes: int = Form(5),
    pdf_file: UploadFile | None = File(None),
):
    run_id = uuid.uuid4().hex[:12]
    run_logger = setup_logging(run_id)
    run_logger.info("Starting research: %s", question)

    initial_state = await _build_initial_state(
        question=question,
        audience=audience,
        desired_depth=desired_depth,
        max_iters=max_iters,
        timebox_minutes=timebox_minutes,
        run_id=run_id,
        pdf_file=pdf_file,
        run_logger=run_logger,
    )

    # SSE streaming path
    accept = request.headers.get("accept", "")
    if "text/event-stream" in accept:
        return StreamingResponse(
            _stream_research(initial_state, run_id),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "X-Accel-Buffering": "no",
            },
        )

    # Standard JSON path (backward compat for CLI/tests)
    graph = build_graph()
    final_state_dict = await graph.ainvoke(initial_state.model_dump())
    final_state = AgentState.model_validate(final_state_dict)

    final_state.report = render_report(final_state)

    store = RunStore()
    store.save(final_state)

    return ResearchResponse(
        run_id=run_id,
        question=question,
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
        raise HTTPException(status_code=404, detail="Run not found")
    return {
        "run_id": state.run_id,
        "question": state.question,
        "report": state.report,
        "audience": state.audience,
        "created_at": store.get_created_at(run_id),
        "evidence_count": len(state.evidence),
        "iterations": state.iteration,
    }
