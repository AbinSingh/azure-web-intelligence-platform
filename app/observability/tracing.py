from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from typing import Any, Callable, TypeVar

from opentelemetry import trace
from opentelemetry.trace import Span, Status, StatusCode
from functools import wraps

F = TypeVar("F", bound=Callable)

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

def trace_node(node_name: str):
    """
    Decorate a synchronous or asynchronous LangGraph node
    without changing its input or output contract.
    """
    def decorator(func: F) -> F:
        if getattr(func, "__observability_traced__", False):
            return func

        if __import__("inspect").iscoroutinefunction(func):

            @wraps(func)
            async def async_wrapper(state, *args, **kwargs):
                execution_id = state.get("execution_id")

                attributes = {}

                if execution_id:
                    attributes["underwriting.execution_id"] = (
                        execution_id
                    )

                with trace_operation(
                    f"langgraph.node.{node_name}",
                    attributes=attributes,
                ):
                    result = await func(
                        state,
                        *args,
                        **kwargs,
                    )

                    return result

            async_wrapper.__observability_traced__ = True
            return async_wrapper  # type: ignore[return-value]

        @wraps(func)
        def sync_wrapper(state, *args, **kwargs):
            execution_id = state.get("execution_id")

            attributes = {}

            if execution_id:
                attributes["underwriting.execution_id"] = (
                    execution_id
                )

            with trace_operation(
                f"langgraph.node.{node_name}",
                attributes=attributes,
            ):
                return func(
                    state,
                    *args,
                    **kwargs,
                )

        sync_wrapper.__observability_traced__ = True
        return sync_wrapper  # type: ignore[return-value]

    return decorator