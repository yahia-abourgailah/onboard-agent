"""HTTP routes for the onboarding agent: a public health check plus a
token-protected /chat that runs the agent graph.
"""

from __future__ import annotations

import json
import uuid
from collections.abc import Iterator, Sequence
from typing import cast

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from fastapi.responses import Response as FastAPIResponse
from fastapi.responses import StreamingResponse
from langchain_core.messages import BaseMessage, ToolMessage
from pydantic import BaseModel

from api.metrics import log_request_metrics
from api.security import verify_token
from config import FLOOR_SVG_PATH, MAPS_JSON_PATH
from graph.build_graph import invoke_graph, stream_graph_tokens

router = APIRouter()

with open(FLOOR_SVG_PATH, encoding="utf-8") as f:
    _FLOOR_SVG = f.read()

with open(MAPS_JSON_PATH, encoding="utf-8") as f:
    _VALID_DESTINATIONS = list(json.load(f).keys())


class ChatRequest(BaseModel):
    prompt: str


class ChatResponse(BaseModel):
    response: str
    session_id: str
    thread_id: str
    floor_map: dict[str, object] | None = None
    # {"destination", "url", "route"} when directions were given


def _extract_floor_map(messages: Sequence[BaseMessage]) -> dict[str, object] | None:
    """Pull the most recent get_office_directions tool result out of this
    turn's messages, if the agent called it, so the frontend can render the
    highlighted floor map instead of relying on the LLM to describe it."""
    for msg in reversed(messages):
        if isinstance(msg, ToolMessage) and msg.name == "get_office_directions":
            if not isinstance(msg.content, str):
                return None
            try:
                data = json.loads(msg.content)
            except (json.JSONDecodeError, TypeError):
                return None
            if isinstance(data, dict) and data.get("type") == "floor_map":
                return cast(dict[str, object], data)
            return None
    return None


def _sse(payload: dict[str, object]) -> str:
    return f"data: {json.dumps(payload)}\n\n"


@router.get("/health")
def health() -> dict[str, str]:
    """Public liveness probe — intentionally unauthenticated for load balancers."""

    return {"status": "ok"}


@router.get("/floor-map")
def floor_map(highlight: str | None = None) -> FastAPIResponse:
    """Public by design: an <img src="..."> tag in the chat UI can't attach
    a bearer token, and the SVG itself has no sensitive content."""
    svg = _FLOOR_SVG
    if highlight is not None:
        if highlight not in _VALID_DESTINATIONS:
            raise HTTPException(
                400, f"Unknown destination '{highlight}'. Valid: {_VALID_DESTINATIONS}"
            )
        svg = svg.replace(
            f'<g id="{highlight}" class="section">',
            f'<g id="{highlight}" class="section highlight">',
        )
    return FastAPIResponse(
        content=svg,
        media_type="image/svg+xml",
        headers={"Cache-Control": "public, max-age=3600"},
    )


@router.post("/chat", response_model=ChatResponse)
def chat(
    request: ChatRequest,
    http_request: Request,
    response: Response,
    _token: str = Depends(verify_token),
) -> ChatResponse:
    session_id = http_request.cookies.get("session_id") or str(uuid.uuid4())
    thread_id = http_request.cookies.get("thread_id") or str(uuid.uuid4())

    response.set_cookie("session_id", session_id, httponly=True)
    response.set_cookie("thread_id", thread_id, httponly=True)

    try:
        result = invoke_graph(request.prompt, thread_id)
    except Exception as exc:
        raise HTTPException(status_code=502, detail="Chatbot request failed.") from exc

    log_request_metrics(
        user_id=session_id,
        session_id=session_id,
        latency_ms=0.0,
        usage_metadata=None,
    )

    return ChatResponse(
        response=result["messages"][-1].content,
        session_id=session_id,
        thread_id=thread_id,
        floor_map=_extract_floor_map(result["messages"]),
    )


@router.post("/chat/stream")
def chat_stream(
    request: ChatRequest,
    http_request: Request,
    _token: str = Depends(verify_token),
) -> StreamingResponse:
    session_id = http_request.cookies.get("session_id") or str(uuid.uuid4())

    thread_id = http_request.cookies.get("thread_id") or str(uuid.uuid4())

    def events() -> Iterator[str]:
        try:
            for token in stream_graph_tokens(request.prompt, thread_id):
                yield _sse({"type": "token", "content": token})

        except Exception:
            yield _sse({"type": "error", "detail": "Chatbot request failed."})

            return

        yield _sse({"type": "done", "session_id": session_id, "thread_id": thread_id})

    stream = StreamingResponse(events(), media_type="text/event-stream")

    stream.set_cookie("session_id", session_id, httponly=True)

    stream.set_cookie("thread_id", thread_id, httponly=True)

    return stream


@router.post("/new-chat")
def new_chat(response: Response, _token: str = Depends(verify_token)) -> dict[str, str]:
    response.delete_cookie("session_id")

    response.delete_cookie("thread_id")

    return {"status": "new chat ready"}
