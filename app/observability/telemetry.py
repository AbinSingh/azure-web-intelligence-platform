from __future__ import annotations

import logging
from threading import Lock

from app.core.config import get_settings

logger = logging.getLogger(__name__)

_initialization_lock = Lock()
_initialized = False


def initialize_telemetry(app=None) -> None:
    """
    Initialize OpenTelemetry and Azure Monitor once per process.

    Telemetry initialization must not prevent the application
    from starting if the monitoring configuration is unavailable.
    """
    global _initialized

    settings = get_settings()

    if not settings.otel_enabled:
        logger.info("OpenTelemetry is disabled.")
        return

    with _initialization_lock:
        if _initialized:
            return

        connection_string = (
            settings.applicationinsights_connection_string
        )

        if not connection_string:
            logger.warning(
                "Application Insights connection string is missing. "
                "Azure Monitor telemetry will not be exported."
            )
            return

        try:
            from azure.monitor.opentelemetry import (
                configure_azure_monitor,
            )

            from opentelemetry.instrumentation.fastapi import (
                FastAPIInstrumentor,
            )

            configure_azure_monitor(
                connection_string=connection_string,
                logger_name="underwriting-intelligence-agent",
            )

            if app is not None:
                FastAPIInstrumentor.instrument_app(app)

            _initialized = True

            logger.info(
                "OpenTelemetry initialized successfully.",
                extra={
                    "service_name": settings.otel_service_name,
                },
            )

        except Exception:
            # Monitoring failures should not crash the agent.
            logger.exception(
                "Failed to initialize OpenTelemetry."
            )