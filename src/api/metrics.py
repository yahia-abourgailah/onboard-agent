"""Request metrics helpers for API-layer observability."""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger("onboard_agent.metrics")


def log_request_metrics(
    *,
    user_id: str,
    session_id: str,
    latency_ms: float,
    usage_metadata: dict[str, Any] | None = None,
) -> None:
    """Emit a compact structured log line for request cost and latency."""
    input_tokens = None
    output_tokens = None
    total_tokens = None

    if usage_metadata:
        input_tokens = usage_metadata.get("input_tokens")
        output_tokens = usage_metadata.get("output_tokens")
        total_tokens = usage_metadata.get("total_tokens")

    logger.info(
        "request_metrics user=%s session=%s latency_ms=%.2f "
        "input_tokens=%s output_tokens=%s total_tokens=%s",
        user_id,
        session_id,
        round(latency_ms, 2),
        input_tokens,
        output_tokens,
        total_tokens,
    )
