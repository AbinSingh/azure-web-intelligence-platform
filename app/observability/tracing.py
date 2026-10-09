from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from typing import Any

from opentelemetry import trace
from opentelemetry.trace import Span, Status, StatusCode

tracer = trace.get_tracer(
    "underwriting-intelligence-agent"
)


@contextmanager
def trace_operation(
    operation_name: str,
    *,
    attributes: dict[str, Any] | None = None,
) -> Iterator[Span]:
    """
    Trace an application operation.

    Exceptions are recorded and re-raised so that existing
    workflow error handling remains unchanged.
    """
    with tracer.start_as_current_span(
        operation_name,
        attributes=attributes,
        record_exception=True,
        set_status_on_exception=True,
    ) as span:
        try:
            yield span

        except Exception as exc:
            span.set_status(
                Status(
                    StatusCode.ERROR,
                    description=type(exc).__name__,
                )
            )

            span.set_attribute(
                "error.type",
                type(exc).__name__,
            )

            raise


def record_event(
    span: Span,
    event_name: str,
    *,
    attributes: dict[str, Any] | None = None,
) -> None:
    """Record a diagnostic event on the current span."""
    span.add_event(
        event_name,
        attributes=attributes or {},
    )