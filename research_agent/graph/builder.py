"""Build the LangGraph StateGraph for the research agent."""

from __future__ import annotations

from langgraph.graph import END, StateGraph

from research_agent.graph.nodes import (
    act_node,
    observe_node,
    plan_node,
    reflect_node,
    write_report_node,
)
from research_agent.graph.state import AgentState


def _route_after_reflect(state: AgentState) -> str:
    if state.should_stop or state.status == "writing":
        return "write_report"
    return "act"


def _route_after_act(state: AgentState) -> str:
    if state.status == "reflecting":
        return "reflect"
    return "observe"


def build_graph() -> StateGraph:
    """Construct and compile the Plan → Act → Observe → Reflect loop."""
    graph = StateGraph(AgentState)

    graph.add_node("plan", plan_node)
    graph.add_node("act", act_node)
    graph.add_node("observe", observe_node)
    graph.add_node("reflect", reflect_node)
    graph.add_node("write_report", write_report_node)

    graph.set_entry_point("plan")

    graph.add_edge("plan", "act")
    graph.add_conditional_edges("act", _route_after_act, {"observe": "observe", "reflect": "reflect"})
    graph.add_edge("observe", "reflect")
    graph.add_conditional_edges(
        "reflect", _route_after_reflect, {"act": "act", "write_report": "write_report"}
    )
    graph.add_edge("write_report", END)

    return graph.compile()
