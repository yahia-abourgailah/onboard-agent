import logging
import time

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

logger = logging.getLogger("onboard_agent")
logging.basicConfig(level=logging.INFO)


def setup_middleware(app: FastAPI) -> None:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


    @app.middleware("http")
    async def log_requests(request: Request, call_next):
        start = time.time()
        response = await call_next(request)
        duration_ms = (time.time() - start) * 1000
        logger.info(
            f"{request.method} {request.url.path} "
            f"-> {response.status_code} ({duration_ms:.1f}ms)"
        )
        return response