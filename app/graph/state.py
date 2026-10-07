
from typing import TypedDict, Literal, Any

from app.domain.schemas import (
    Evidence,
    SearchResult,
    UnderwritingInsight,
    UnderwritingReport,
    UnderwritingType,
)

ExecutionStatus = Literal[
    "pending",
    "running",
    "completed",
    "completed_with_errors",
    "failed",
]

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
    type: str
    underwriting_questions: list[str]

    # ------------------------------------------------------------------
    # Research planning
    # ------------------------------------------------------------------
    search_queries: list[str]

    # ------------------------------------------------------------------
    # Discovery
    # ------------------------------------------------------------------
    search_results: list[dict[str, Any]]

    # ------------------------------------------------------------------
    # Evidence
    # ------------------------------------------------------------------
    evidence: list[dict[str, Any]]

    # ------------------------------------------------------------------
    # Analysis
    # ------------------------------------------------------------------
    insights: list[dict[str, Any]]

    # ------------------------------------------------------------------
    # Final output
    # ------------------------------------------------------------------
    report: dict[str, Any] | None

    # ------------------------------------------------------------------
    # Execution metadata
    # ------------------------------------------------------------------
    execution_id: str
    execution_status: ExecutionStatus
    errors: list[str]