from firecrawl import AsyncFirecrawl

from app.core.config import get_settings
from app.domain.schemas import SearchResult


class FirecrawlService:
    """
    Extracts web page content for underwriting research.
    """

    def __init__(self) -> None:
        settings = get_settings()

        self.client = AsyncFirecrawl(
            api_key=settings.firecrawl_api_key
        )
        self.max_content_chars = settings.max_content_chars_per_source

    async def scrape(
        self,
        result: SearchResult,
    ) -> SearchResult:
        """
        Extract page content from a discovered URL.
        """

        document = await self.client.scrape(
            str(result.url),
            formats=["markdown"],
        )

        markdown = getattr(document, "markdown", None) or ""

        return result.model_copy(
            update={
                "content": markdown[: self.max_content_chars],
                "extraction_status": "success",
                "extraction_error": None,
            }
        )