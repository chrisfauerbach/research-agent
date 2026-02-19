"""Individual node functions for the research agent graph."""

from __future__ import annotations

import logging
import time

from research_agent.graph.prompts import (
    ACT_SYSTEM,
    ACT_USER,
    OBSERVE_SYSTEM,
    OBSERVE_USER,
    PLAN_SYSTEM,
    PLAN_USER,
    REFLECT_SYSTEM,
    REFLECT_USER,
    WRITE_REPORT_SYSTEM,
    WRITE_REPORT_USER,
)
from research_agent.graph.state import (
    AgentState,
    LLMCallMetric,
    NodeTimingMetric,
    RunMetrics,
    ToolCallMetric,
)
from research_agent.llm.adapter import get_llm
from research_agent.llm.client import LLMResponse
from research_agent.tools import TOOL_REGISTRY

logger = logging.getLogger(__name__)


def _llm_metric(node: str, response: LLMResponse) -> LLMCallMetric:
    """Build an LLMCallMetric from an LLMResponse."""
    return LLMCallMetric(
        node=node,
        prompt_tokens=response.prompt_eval_count,
        completion_tokens=response.eval_count,
        duration_ms=response.total_duration_ns / 1_000_000,
    )


def _copy_metrics(state: AgentState) -> RunMetrics:
    """Return a mutable copy of the current run metrics."""
    return RunMetrics(
        llm_calls=list(state.metrics.llm_calls),
        tool_calls=list(state.metrics.tool_calls),
        node_timings=list(state.metrics.node_timings),
    )


async def plan_node(state: AgentState) -> dict:
    """Generate an initial research plan."""
    node_start = time.time()
    logger.info("[plan_node] Generating plan for: %s", state.question)
    llm = get_llm()

    pdf_section = ""
    if state.pdf_context:
        pdf_section = f"\nReference document ({state.pdf_filename}):\n{state.pdf_context[:8000]}\n"

    prompt = PLAN_USER.format(
        question=state.question,
        audience=state.audience,
        desired_depth=state.desired_depth,
        pdf_section=pdf_section,
    )
    response = await llm.query(prompt, system=PLAN_SYSTEM)
    raw = response.text

    steps: list[str] = []
    for line in raw.strip().splitlines():
        line = line.strip()
        if line and line[0].isdigit():
            steps.append(line)

    if not steps:
        steps = [f"1. [web_search] {state.question}"]

    metrics = _copy_metrics(state)
    metrics.llm_calls.append(_llm_metric("plan", response))
    metrics.node_timings.append(
        NodeTimingMetric(node="plan", duration_ms=(time.time() - node_start) * 1000)
    )

    logger.info("[plan_node] Plan has %d steps", len(steps))
    return {
        "plan": steps,
        "current_step_index": 0,
        "status": "acting",
        "start_time": state.start_time or time.time(),
        "metrics": metrics,
    }


async def act_node(state: AgentState) -> dict:
    """Select and invoke the tool for the current plan step."""
    node_start = time.time()
    logger.info("[act_node] Step %d/%d", state.current_step_index + 1, len(state.plan))

    if state.current_step_index >= len(state.plan):
        metrics = _copy_metrics(state)
        metrics.node_timings.append(
            NodeTimingMetric(node="act", duration_ms=(time.time() - node_start) * 1000)
        )
        return {"status": "reflecting", "last_tool_result": "", "metrics": metrics}

    step = state.plan[state.current_step_index]
    llm = get_llm()

    notes_summary = "; ".join(state.notes[-5:]) if state.notes else "(none)"
    prompt = ACT_USER.format(
        step=step,
        evidence_count=len(state.evidence),
        notes_summary=notes_summary,
    )
    response = await llm.query(prompt, system=ACT_SYSTEM)
    raw = response.text

    tool_name = "web_search"
    query = state.question
    for line in raw.strip().splitlines():
        if line.upper().startswith("TOOL:"):
            tool_name = line.split(":", 1)[1].strip().lower()
        elif line.upper().startswith("QUERY:"):
            query = line.split(":", 1)[1].strip()

    tool_cls = TOOL_REGISTRY.get(tool_name)
    if tool_cls is None:
        logger.warning("[act_node] Unknown tool '%s', falling back to web_search", tool_name)
        tool_cls = TOOL_REGISTRY["web_search"]

    tool = tool_cls()
    tool_start = time.time()
    result = await tool.run(query=query)
    tool_duration_ms = (time.time() - tool_start) * 1000

    new_evidence = list(state.evidence) + result.evidence
    # Deduplicate bibliography by URL
    bib = dict(state.bibliography)
    for ev in result.evidence:
        key = ev.url or ev.title
        if key not in bib:
            bib[key] = ev

    metrics = _copy_metrics(state)
    metrics.llm_calls.append(_llm_metric("act", response))
    metrics.tool_calls.append(
        ToolCallMetric(
            tool_name=tool_name,
            query=query,
            duration_ms=tool_duration_ms,
            success=result.success,
        )
    )
    metrics.node_timings.append(
        NodeTimingMetric(node="act", duration_ms=(time.time() - node_start) * 1000)
    )

    return {
        "last_tool_result": result.data,
        "pending_tool": tool_name,
        "pending_tool_query": query,
        "evidence": new_evidence,
        "bibliography": bib,
        "tool_calls_made": state.tool_calls_made + 1,
        "status": "observing",
        "metrics": metrics,
    }


async def observe_node(state: AgentState) -> dict:
    """Summarise the latest tool output into a note."""
    node_start = time.time()
    logger.info("[observe_node] Summarising tool output")
    llm = get_llm()

    step = (
        state.plan[state.current_step_index] if state.current_step_index < len(state.plan) else ""
    )
    prompt = OBSERVE_USER.format(
        step=step,
        tool=state.pending_tool,
        tool_output=state.last_tool_result[:3000],
    )
    response = await llm.query(prompt, system=OBSERVE_SYSTEM)

    new_notes = list(state.notes) + [response.text.strip()]

    metrics = _copy_metrics(state)
    metrics.llm_calls.append(_llm_metric("observe", response))
    metrics.node_timings.append(
        NodeTimingMetric(node="observe", duration_ms=(time.time() - node_start) * 1000)
    )

    return {
        "notes": new_notes,
        "current_step_index": state.current_step_index + 1,
        "status": "reflecting",
        "metrics": metrics,
    }


async def reflect_node(state: AgentState) -> dict:
    """Decide whether to continue or stop."""
    node_start = time.time()
    logger.info(
        "[reflect_node] Iteration %d, evidence=%d, steps=%d/%d",
        state.iteration,
        len(state.evidence),
        state.current_step_index,
        len(state.plan),
    )

    elapsed = time.time() - state.start_time if state.start_time else 0
    timebox_exceeded = elapsed > state.timebox_minutes * 60
    iter_exceeded = state.iteration >= state.max_iters
    tool_limit_exceeded = state.tool_calls_made >= state.tool_call_limit

    if timebox_exceeded or iter_exceeded or tool_limit_exceeded:
        reason = []
        if timebox_exceeded:
            reason.append("timebox exceeded")
        if iter_exceeded:
            reason.append("max iterations reached")
        if tool_limit_exceeded:
            reason.append("tool call limit reached")
        logger.info("[reflect_node] Forced stop: %s", ", ".join(reason))
        metrics = _copy_metrics(state)
        metrics.node_timings.append(
            NodeTimingMetric(node="reflect", duration_ms=(time.time() - node_start) * 1000)
        )
        return {
            "should_stop": True,
            "status": "writing",
            "iteration": state.iteration + 1,
            "metrics": metrics,
        }

    # If there are remaining plan steps, keep going
    if state.current_step_index < len(state.plan):
        metrics = _copy_metrics(state)
        metrics.node_timings.append(
            NodeTimingMetric(node="reflect", duration_ms=(time.time() - node_start) * 1000)
        )
        return {"status": "acting", "iteration": state.iteration + 1, "metrics": metrics}

    # Ask the LLM whether we have enough evidence
    llm = get_llm()
    prompt = REFLECT_USER.format(
        question=state.question,
        iteration=state.iteration,
        max_iters=state.max_iters,
        steps_completed=state.current_step_index,
        total_steps=len(state.plan),
        evidence_count=len(state.evidence),
        notes="\n".join(f"- {n}" for n in state.notes[-10:]),
    )
    response = await llm.query(prompt, system=REFLECT_SYSTEM)
    raw = response.text

    metrics = _copy_metrics(state)
    metrics.llm_calls.append(_llm_metric("reflect", response))
    metrics.node_timings.append(
        NodeTimingMetric(node="reflect", duration_ms=(time.time() - node_start) * 1000)
    )

    if "DECISION: STOP" in raw.upper():
        confidence = 0.7
        for line in raw.splitlines():
            if line.upper().startswith("CONFIDENCE:"):
                try:
                    confidence = float(line.split(":", 1)[1].strip())
                except ValueError:
                    pass
        return {
            "should_stop": True,
            "confidence": confidence,
            "status": "writing",
            "iteration": state.iteration + 1,
            "metrics": metrics,
        }

    # CONTINUE — parse optional new steps
    new_steps: list[str] = []
    in_new = False
    for line in raw.splitlines():
        if line.upper().startswith("NEW_STEPS:"):
            rest = line.split(":", 1)[1].strip()
            if rest:
                new_steps.append(rest)
            in_new = True
        elif in_new and line.strip() and line.strip()[0].isdigit():
            new_steps.append(line.strip())

    plan = list(state.plan)
    if new_steps:
        plan.extend(new_steps)

    return {
        "plan": plan,
        "status": "acting",
        "iteration": state.iteration + 1,
        "metrics": metrics,
    }


async def write_report_node(state: AgentState) -> dict:
    """Produce the final Markdown report."""
    node_start = time.time()
    logger.info("[write_report_node] Writing report with %d evidence items", len(state.evidence))
    llm = get_llm()

    evidence_text = ""
    seen_urls: set[str] = set()
    idx = 1
    for key, ev in state.bibliography.items():
        if ev.url in seen_urls:
            continue
        seen_urls.add(ev.url)
        evidence_text += f"[{idx}] {ev.title} — {ev.url}\n    Snippet: {ev.snippet[:200]}\n\n"
        idx += 1

    notes_text = "\n".join(f"- {n}" for n in state.notes)

    pdf_section = ""
    if state.pdf_context:
        pdf_section = f"\nReference document ({state.pdf_filename}):\n{state.pdf_context[:20000]}\n"

    prompt = WRITE_REPORT_USER.format(
        question=state.question,
        audience=state.audience,
        evidence=evidence_text or "(no external evidence collected)",
        notes=notes_text or "(no notes)",
        pdf_section=pdf_section,
    )
    response = await llm.query(prompt, system=WRITE_REPORT_SYSTEM, max_tokens=8192)

    metrics = _copy_metrics(state)
    metrics.llm_calls.append(_llm_metric("write_report", response))
    metrics.node_timings.append(
        NodeTimingMetric(node="write_report", duration_ms=(time.time() - node_start) * 1000)
    )

    return {"report": response.text.strip(), "status": "done", "metrics": metrics}
