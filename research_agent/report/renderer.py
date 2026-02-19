"""Post-process the LLM-generated report to ensure structure."""

from __future__ import annotations

from research_agent.graph.state import AgentState


def render_report(state: AgentState) -> str:
    """Return the final report, appending a sources section if the LLM omitted one."""
    report = state.report

    # If the LLM didn't include a Sources section, append one from bibliography
    if "## sources" not in report.lower() and "## citations" not in report.lower():
        if state.bibliography:
            report += "\n\n## Sources\n\n"
            for idx, (_, ev) in enumerate(state.bibliography.items(), 1):
                if ev.url:
                    report += f"{idx}. [{ev.title}]({ev.url})\n"
                else:
                    report += f"{idx}. {ev.title}\n"

    # Ensure mermaid block exists (even a placeholder)
    if "```mermaid" not in report:
        report += (
            "\n\n## Architecture Diagram\n\n"
            "```mermaid\ngraph TD\n"
            "    A[Research Question] --> B[Evidence Gathering]\n"
            "    B --> C[Analysis]\n"
            "    C --> D[Report]\n"
            "```\n"
        )

    return report
