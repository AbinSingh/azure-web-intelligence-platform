import asyncio
import random
from collections.abc import Awaitable, Callable
from typing import TypeVar

from app.core.config import get_settings


T = TypeVar("T")


settings = get_settings()


async def retry_async(
    operation: Callable[[], Awaitable[T]],
    *,
    operation_name: str,
) -> T:
    """
    Execute an async operation with bounded exponential backoff.

    Retries are intentionally bounded so an unavailable external
    provider cannot block the underwriting workflow indefinitely.
    """

    attempts = settings.max_provider_retries + 1

    for attempt in range(1, attempts + 1):
        try:
            return await asyncio.wait_for(
                operation(),
                timeout=settings.provider_timeout_seconds,
            )

        except Exception:
            if attempt >= attempts:
                raise

            delay = min(
                settings.retry_max_wait_seconds,
                settings.retry_min_wait_seconds
                * (2 ** (attempt - 1)),
            )

            # Small jitter prevents synchronized retries.
            delay += random.uniform(0, delay * 0.25)

            await asyncio.sleep(delay)

    raise RuntimeError(
        f"Recovery failed for operation: {operation_name}"
    )