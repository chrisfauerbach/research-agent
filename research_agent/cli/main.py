"""Typer CLI for the research agent."""

from __future__ import annotations

import asyncio
import uuid

import typer
from rich.console import Console
from rich.markdown import Markdown

from research_agent.config import settings

app = typer.Typer(name="research-agent", help="Autonomous technical research agent.")
console = Console()


@app.command()
def research(
    question: str = typer.Argument(..., help="The research question to investigate."),
    audience: str = typer.Option("engineer", help="Target audience: engineer or executive."),
    depth: str = typer.Option("thorough", help="Desired depth of research."),
    max_iters: int = typer.Option(settings.max_iters, help="Maximum research iterations."),
    timebox: int = typer.Option(settings.timebox_minutes, help="Timebox in minutes."),
    raw: bool = typer.Option(False, "--raw", help="Print raw markdown instead of rendered."),
) -> None:
    """Run a research query and print the report."""
    asyncio.run(_run(question, audience, depth, max_iters, timebox, raw))


async def _run(
    question: str,
    audience: str,
    depth: str,
    max_iters: int,
    timebox: int,
    raw: bool,
) -> None:
    from research_agent.graph.builder import build_graph
    from research_agent.graph.state import AgentState
    from research_agent.memory.store import RunStore
    from research_agent.report.renderer import render_report
    from research_agent.util.logging import setup_logging

    run_id = uuid.uuid4().hex[:12]
    logger = setup_logging(run_id)
    logger.info("CLI research start: %s", question)

    console.print(f"\n[bold]Research Agent[/bold]  run_id={run_id}")
    console.print(f"Question: {question}\n")

    initial_state = AgentState(
        question=question,
        audience=audience,  # type: ignore[arg-type]
        desired_depth=depth,
        max_iters=max_iters,
        timebox_minutes=timebox,
        run_id=run_id,
    )

    graph = build_graph()

    with console.status("[bold green]Researching..."):
        final_state_dict = await graph.ainvoke(initial_state.model_dump())

    final_state = AgentState.model_validate(final_state_dict)
    final_state.report = render_report(final_state)

    store = RunStore()
    store.save(final_state)

    console.print()
    if raw:
        print(final_state.report)
    else:
        console.print(Markdown(final_state.report))

    console.print(
        f"\n[dim]Completed in {final_state.iteration} iterations, "
        f"{len(final_state.evidence)} evidence items.[/dim]"
    )


@app.command()
def runs(limit: int = typer.Option(20, help="Number of runs to list.")) -> None:
    """List previous research runs."""
    from research_agent.memory.store import RunStore

    store = RunStore()
    for run in store.list_runs(limit):
        console.print(f"  {run['run_id']}  {run['created_at']}  {run['question'][:60]}")


if __name__ == "__main__":
    app()
