"""LangGraph wiring for property_intake.

Pipeline: ingest -> extract -> verify -> merge -> validate -> assemble.
Extract collects per-field candidates from every document; verify judges each
against its evidence (#5); merge reconciles by source priority and flags
conflicts (``mau_thuan``); validate runs rule/arithmetic cross-checks (feature 4);
assemble applies confidence tiering (#9) and emits the form.
"""

from __future__ import annotations

from functools import lru_cache

from langgraph.graph import END, StateGraph

from shb.ai.plugins.property_intake.nodes import (
    assemble_node,
    extract_node,
    ingest_node,
    merge_node,
    validate_node,
    verify_node,
)
from shb.ai.plugins.property_intake.schema import PropertyIntakeInput, PropertyIntakeOutput
from shb.ai.plugins.property_intake.state import IntakeState


def build_graph():
    """Build and compile the property_intake state graph."""
    graph = StateGraph(IntakeState)
    graph.add_node("ingest", ingest_node)
    graph.add_node("extract", extract_node)
    graph.add_node("verify", verify_node)
    graph.add_node("merge", merge_node)
    graph.add_node("validate", validate_node)
    graph.add_node("assemble", assemble_node)

    graph.set_entry_point("ingest")
    graph.add_edge("ingest", "extract")
    graph.add_edge("extract", "verify")
    graph.add_edge("verify", "merge")
    graph.add_edge("merge", "validate")
    graph.add_edge("validate", "assemble")
    graph.add_edge("assemble", END)
    return graph.compile()


@lru_cache(maxsize=1)
def _compiled_graph():
    """Cache the compiled graph (nodes are stateless; state is per-invocation)."""
    return build_graph()


async def run_intake(intake_input: PropertyIntakeInput, ctx) -> PropertyIntakeOutput:
    """Run the pipeline end-to-end and return the assembled output."""
    initial: IntakeState = {"input": intake_input, "ctx": ctx, "warnings": []}
    final_state = await _compiled_graph().ainvoke(initial)
    return final_state["output"]
