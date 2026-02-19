"""Research endpoint."""

from __future__ import annotations

import logging
import uuid
from typing import Literal

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from pydantic import BaseModel

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


@router.post("/research", response_model=ResearchResponse)
async def run_research(
    question: str = Form(...),
    audience: Literal["engineer", "executive"] = Form("engineer"),
    desired_depth: str = Form("thorough"),
    max_iters: int = Form(6),
    timebox_minutes: int = Form(5),
    pdf_file: UploadFile | None = File(None),
) -> ResearchResponse:
    run_id = uuid.uuid4().hex[:12]
    run_logger = setup_logging(run_id)
    run_logger.info("Starting research: %s", question)

    # --- PDF handling ---
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
            pdf_context = extract_text_from_pdf(
                pdf_bytes, max_chars=settings.pdf_max_extract_chars
            )
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

    initial_state = AgentState(
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
        return {"error": "Run not found"}
    return {
        "run_id": state.run_id,
        "question": state.question,
        "report": state.report,
        "evidence_count": len(state.evidence),
        "iterations": state.iteration,
    }
