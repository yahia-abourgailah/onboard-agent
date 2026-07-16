import logging
import time
from collections.abc import Awaitable, Callable

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware

from onboard_agent.config import get_settings

logger = logging.getLogger("onboard_agent")
logging.basicConfig(level=logging.INFO)


def setup_middleware(app: FastAPI) -> None:
    settings = get_settings()

    app.add_middleware(
        CORSMiddleware,
        # FIX (FIX-5): never pair allow_origins=["*"] with allow_credentials=True —
        # browsers reject that combination, and a credentialed wildcard is a
        # security hole. Origins now come from config, per environment.
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
        # FIX (best practice): time with perf_counter (monotonic) instead of
        # time.time(), which can jump backwards on a clock adjustment and produce
        # negative durations. Also log with %-args so the string is only built when
        # the INFO level is actually emitted.
        start = time.perf_counter()
        response = await call_next(request)
        duration_ms = (time.perf_counter() - start) * 1000
        logger.info(
            "%s %s -> %s (%.1fms)",
            request.method,
            request.url.path,
            response.status_code,
            duration_ms,
        )
        return response
