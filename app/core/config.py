from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


PROJECT_ROOT = Path(__file__).resolve().parents[2]
ENV_FILE = PROJECT_ROOT / ".env"


class Settings(BaseSettings):
    app_env: str = "local"
    log_level: str = "INFO"

    # Azure OpenAI / Microsoft Foundry
    azure_openai_endpoint: str
    azure_openai_api_key: str
    azure_openai_deployment: str = "gpt-4o"

    # Web intelligence providers
    tavily_api_key: str
    firecrawl_api_key: str

    # Research controls
    max_search_queries: int = 1
    max_search_results: int = 8
    max_sources_to_scrape: int = 1

    # Evidence controls
    max_content_chars_per_source: int = 18_000
    min_source_quality: float = 0.55

    model_config = SettingsConfigDict(
        env_file=ENV_FILE,
        case_sensitive=False,
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()