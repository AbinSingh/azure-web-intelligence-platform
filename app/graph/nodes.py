from datetime import datetime, timezone
from uuid import uuid4

from app.core.config import get_settings
from app.domain.schemas import (
    Evidence,
    UnderwritingInsight,
    UnderwritingReport,
)
from app.graph.state import UnderwritingState
from app.services.firecrawl import FirecrawlService
from app.services.llm import AzureOpenAIService
from app.services.tavily import TavilySearchService

settings = get_settings()

tavily_service = TavilySearchService()
firecrawl_service = FirecrawlService()
llm_service = AzureOpenAIService()


async def build_search_queries(
    state: UnderwritingState,
) -> UnderwritingState:
    """
    Build research queries for the supplied underwriting questions.

    The number of queries executed is controlled separately by
    max_search_queries in application settings.
    """

    account_name = state["account_name"]
    address = state["address"]
    questions = state["underwriting_questions"]

    queries: list[str] = []

    for question in questions:
        queries.append(
            f'"{account_name}" '
            f'"{address}" '
            f"{question}"
        )

    return {
        **state,
        "search_queries": queries,
    }


async def discover_web_sources(
    state: UnderwritingState,
) -> UnderwritingState:
    """
    Discover web sources using Tavily.

    The number of Tavily calls is controlled by
    settings.max_search_queries.
    """

    queries = state.get("search_queries", [])

    limited_queries = queries[
        : settings.max_search_queries
    ]

    search_results = []

    for query in limited_queries:
        search_results = await tavily_service.search(
            account_name=state["account_name"],
            address=state["address"],
            question=query,
        )

        search_results.extend(search_results)

    return {
        **state,
        "search_results": search_results,
    }


async def extract_evidence(
    state: UnderwritingState,
) -> UnderwritingState:
    """
    Extract source content using Firecrawl.

    The number of Firecrawl calls is controlled by
    settings.max_sources_to_scrape.
    """

    evidence: list[Evidence] = []

    search_results = state.get("search_results", [])

    limited_results = search_results[
        : settings.max_sources_to_scrape
    ]

    evidence: list[Evidence] = []
    errors = list(state.get("errors", []))

    for result in limited_results:
        try:
            extracted_result = await firecrawl_service.scrape(
                result
            )

            if (
                extracted_result.extraction_status != "success"
                or not extracted_result.content
            ):
                errors.append(
                    f"Failed to extract source: {result.url}"
                )
                continue

            evidence.append(
                Evidence(
                    evidence_id=f"EV-{uuid4().hex[:12]}",
                    title=extracted_result.title,
                    url=extracted_result.url,
                    source=extracted_result.source or "web",
                    content=extracted_result.content,
                    relevance=(
                        "Source discovered through Tavily "
                        "and successfully extracted by Firecrawl."
                    ),
                )
            )

        except Exception as exc:
            errors.append(
                f"Firecrawl extraction failed for "
                f"{result.url}: {exc}"
            )

    return {
        **state,
        "evidence": evidence,
        "errors": errors,
    }


async def synthesize_underwriting_report(
    state: UnderwritingState,
) -> UnderwritingState:
    """
    Use Azure OpenAI to synthesize evidence into
    underwriting intelligence.
    """

    report_data = await llm_service.generate_report(
        account_name=state["account_name"],
        address=state["address"],
        underwriting_type=state["type"],
        questions=state["underwriting_questions"],
        evidence=state.get("evidence", []),
    )

    report = UnderwritingReport(
        account_name=state["account_name"],
        address=state["address"],
        type=state["type"],
        executive_summary=report_data[
            "executive_summary"
        ],
        insights=[
            UnderwritingInsight(**item)
            for item in report_data["insights"]
        ],
        evidence=state.get("evidence", []),
        information_gaps=report_data.get(
            "information_gaps",
            [],
        ),
        recommended_follow_up_questions=report_data.get(
            "recommended_follow_up_questions",
            [],
        ),
        research_timestamp=datetime.now(
            timezone.utc
        ),
    )

    return {
        **state,
        "report": report,
    }