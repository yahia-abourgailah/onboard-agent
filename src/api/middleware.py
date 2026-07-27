import logging
import time
from collections import defaultdict
from collections.abc import Awaitable, Callable
from datetime import UTC, datetime, timedelta

from fastapi import FastAPI, Request, Response, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from api.security import get_user_id
from config import get_settings

logger = logging.getLogger("onboard_agent")
logging.basicConfig(level=logging.INFO)

_request_log: defaultdict[tuple[str, str], list[float]] = defaultdict(list)


def setup_middleware(app: FastAPI) -> None:
    settings = get_settings()

    app.add_middleware(
        CORSMiddleware,
        # Origins come from config, per environment — never a credentialed wildcard.
        allow_origins=settings.cors_allow_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.middleware("http")
    async def log_requests(
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        start = time.perf_counter()

        auth_header = request.headers.get("Authorization")
        credentials = None
        if auth_header is not None:
            scheme, _, token = auth_header.partition(" ")
            if scheme.lower() == "bearer" and token:
                credentials = type("Cred", (), {"credentials": token})()
        user_id = get_user_id(credentials)
        session_id = request.cookies.get("session_id") or "anonymous"
        key = (user_id, session_id)

        if settings.RATE_LIMIT_ENABLED:
            window_seconds = settings.RATE_LIMIT_WINDOW_SECONDS
            now = datetime.now(UTC)
            window_start = now - timedelta(seconds=window_seconds)
            history = _request_log[key]
            history[:] = [
                timestamp for timestamp in history if timestamp >= window_start.timestamp()
            ]
            if len(history) >= settings.RATE_LIMIT_MAX_REQUESTS:
                return JSONResponse(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    content={"detail": "Rate limit exceeded"},
                )
            history.append(now.timestamp())

        response = await call_next(request)
        duration_ms = (time.perf_counter() - start) * 1000
        logger.info(
            "%s %s -> %s (%.1fms)",
            request.method,
            request.url.path,
            response.status_code,
            duration_ms,
        )

        if settings.METRICS_ENABLED:
            logger.info(
                "request_metrics user=%s session=%s latency_ms=%.2f",
                user_id,
                session_id,
                duration_ms,
            )

        return response
