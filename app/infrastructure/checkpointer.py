
from pathlib import Path

from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver


PROJECT_ROOT = Path(__file__).resolve().parents[2]
CHECKPOINT_DIR = PROJECT_ROOT / "data"
CHECKPOINT_DB = CHECKPOINT_DIR / "underwriting_checkpoints.sqlite"


def create_checkpointer() -> AsyncSqliteSaver:
    CHECKPOINT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    return AsyncSqliteSaver.from_conn_string(str(CHECKPOINT_DB),)