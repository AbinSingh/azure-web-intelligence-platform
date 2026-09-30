from typing import TypedDict

from app.domain.schemas import (
    Evidence,
    SearchResult,
    UnderwritingInsight,
    UnderwritingReport,
    UnderwritingType,
)

class UnderwritingState(TypedDict, total=False):
    account_name: str
    address: str
    type: UnderwritingType
    underwriting_questions: list[str]

    search_queries: list[str]
    search_results: list[SearchResult]

    evidence: list[Evidence]
    insights: list[UnderwritingInsight]

    report: UnderwritingReport
    errors: list[str]