from fastapi import FastAPI
from app.api.routes import router
from app.core.config import get_settings
from app.infrastructure.logging import configure_logging

settings = get_settings()
configure_logging(settings.log_level)

app = FastAPI(
    title="Property Underwriting Web Intelligence API",
    version="0.1.0",
    description="Agentic web research and evidence synthesis for property underwriting.",
)
app.include_router(router)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
