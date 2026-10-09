from fastapi import FastAPI
from app.api.routes import router
from app.core.config import get_settings
from app.infrastructure.logging import configure_logging
from contextlib import asynccontextmanager
from app.infrastructure.checkpointer import create_checkpointer
from app.graph.workflow import build_underwriting_graph
from app.observability.telemetry import initialize_telemetry


settings = get_settings()
configure_logging(settings.log_level)

@asynccontextmanager
async def lifespan(app: FastAPI):
    async with create_checkpointer() as checkpointer:
        # Initialize telemetry before serving requests.
        initialize_telemetry(app)

        # Initialize the SQLite checkpointer
        app.state.checkpointer = checkpointer

        # Compile & Build graph using this checkpointer.
        app.state.underwriting_graph = build_underwriting_graph(
            checkpointer=checkpointer,
        )

        yield

app = FastAPI(
    title="Property Underwriting Web Intelligence API",
    lifespan=lifespan,
)
app.include_router(router)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
