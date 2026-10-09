from typing import Any

from tavily import AsyncTavilyClient

from app.core.config import get_settings
from app.core.recovery import retry_async
from app.domain.schemas import SearchResult
from app.observability.tracing import trace_operation


class TavilySearchService:
    """
    Performs web discovery for underwriting research.
    """

    def __init__(self) -> None:
        settings = get_settings()

        self.client = AsyncTavilyClient(
            api_key=settings.tavily_api_key
        )
        self.max_search_results = settings.max_search_results

    async def search(
        self,
        account_name: str,
        address: str,
        question: str,
    ) -> list[SearchResult]:
        """
        Search Tavily and normalize results into SearchResult objects.
        """

        query = (
            f'"{account_name}" '
            f'"{address}" '
            f'"{question}"'
        )

        async def execute_search():
            return await self.client.search(
                query=query,
                search_depth="advanced",
                max_results=self.max_search_results,
                include_answer=False,
                include_raw_content=False,
            )

        with trace_operation(
                "tavily.search",
                attributes={
                    "provider.name": "tavily",
                },
        ) as span:
            response = await retry_async(
                execute_search,
                operation_name="tavily_search",
            )

            span.set_attribute(
                "tavily.result_count",
                len(response.get("results", [])),
            )

        results: list[SearchResult] = []

        for item in response.get("results", []):
            url = item.get("url")

            if not url:
                continue

            results.append(
                SearchResult(
                    title=item.get("title", "Unknown source"),
                    url=url,
                    content=item.get("content"),
                    source=item.get("source"),
                    extraction_status="pending",
                )
            )

        return results