
from typing import TypedDict

from app.domain.schemas import (
    Evidence,
    SearchResult,
    UnderwritingInsight,
    UnderwritingReport,
    UnderwritingType,
)


class UnderwritingState(TypedDict, total=False):
    """
    Runtime state for a single underwriting research execution.

    The state is the single source of truth passed between LangGraph nodes.
    """

    # ------------------------------------------------------------------
    # Request
    # ------------------------------------------------------------------
    account_name: str
    address: str
    type: UnderwritingType
    underwriting_questions: list[str]

    # ------------------------------------------------------------------
    # Research planning
    # ------------------------------------------------------------------
    search_queries: list[str]

    # ------------------------------------------------------------------
    # Discovery
    # ------------------------------------------------------------------
    search_results: list[SearchResult]

    # ------------------------------------------------------------------
    # Evidence
    # ------------------------------------------------------------------
    evidence: list[Evidence]

    # ------------------------------------------------------------------
    # Analysis
    # ------------------------------------------------------------------
    insights: list[UnderwritingInsight]

    # ------------------------------------------------------------------
    # Final output
    # ------------------------------------------------------------------
    report: UnderwritingReport

    # ------------------------------------------------------------------
    # Execution metadata
    # ------------------------------------------------------------------
    execution_id: str
    errors: list[str]