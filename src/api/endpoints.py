"""HTTP routes for the onboarding agent: a public health check plus a
token-protected /chat that runs the agent graph.
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from pydantic import BaseModel

from api.security import verify_token
from graph.build_graph import invoke_graph

router = APIRouter()


class ChatRequest(BaseModel):
    prompt: str


class ChatResponse(BaseModel):
    response: str
    session_id: str
    thread_id: str


@router.get("/health")
def health() -> dict[str, str]:
    """Public liveness probe — intentionally unauthenticated for load balancers."""
    return {"status": "ok"}


@router.post("/chat", response_model=ChatResponse)
def chat(
    request: ChatRequest,
    http_request: Request,
    response: Response,
    _token: str = Depends(verify_token),
) -> ChatResponse:
    # Read cookies manually so they never show up as declared parameters in
    # the Swagger docs — /chat visually only ever takes `prompt`.
    session_id = http_request.cookies.get("session_id") or str(uuid.uuid4())
    thread_id = http_request.cookies.get("thread_id") or str(uuid.uuid4())

    response.set_cookie("session_id", session_id, httponly=True)
    response.set_cookie("thread_id", thread_id, httponly=True)

    try:
        result = invoke_graph(request.prompt, thread_id)
    except Exception as exc:
        raise HTTPException(status_code=502, detail="Chatbot request failed.") from exc

    return ChatResponse(
        response=result["messages"][-1].content,
        session_id=session_id,
        thread_id=thread_id,
    )


@router.post("/new-chat")
def new_chat(response: Response, _token: str = Depends(verify_token)) -> dict[str, str]:
    """Clears session cookies so the next /chat call starts a fresh
    session_id and thread_id — i.e. a brand new conversation."""
    response.delete_cookie("session_id")
    response.delete_cookie("thread_id")
    return {"status": "new chat ready"}
