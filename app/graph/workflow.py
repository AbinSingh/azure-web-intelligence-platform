from uuid import uuid4

from langgraph.graph import END, START, StateGraph

from app.graph.nodes import (
    build_search_queries,
    discover_web_sources,
    extract_evidence,
    synthesize_underwriting_report,
)
from app.graph.state import UnderwritingState


def build_underwriting_graph():
    graph = StateGraph(UnderwritingState)

    graph.add_node(
        "build_search_queries",
        build_search_queries,
    )

    graph.add_node(
        "discover_web_sources",
        discover_web_sources,
    )

    graph.add_node(
        "extract_evidence",
        extract_evidence,
    )

    graph.add_node(
        "synthesize_underwriting_report",
        synthesize_underwriting_report,
    )

    graph.add_edge(
        START,
        "build_search_queries",
    )

    graph.add_edge(
        "build_search_queries",
        "discover_web_sources",
    )

    graph.add_edge(
        "discover_web_sources",
        "extract_evidence",
    )

    graph.add_edge(
        "extract_evidence",
        "synthesize_underwriting_report",
    )

    graph.add_edge(
        "synthesize_underwriting_report",
        END,
    )

    return graph.compile()


underwriting_graph = build_underwriting_graph()

def create_initial_state(
    *,
    account_name: str,
    address: str,
    underwriting_type,
    underwriting_questions: list[str],
) -> UnderwritingState:
    """
    Create the initial state for one underwriting execution.
    """

    return UnderwritingState(
        execution_id=str(uuid4()),
        account_name=account_name,
        address=address,
        type=underwriting_type,
        underwriting_questions=underwriting_questions,
        search_queries=[],
        search_results=[],
        evidence=[],
        insights=[],
        errors=[],
    )