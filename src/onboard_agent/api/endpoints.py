"""HTTP routes for the onboarding agent: a public health check plus a
token-protected /chat that runs the agent graph.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from onboard_agent.api.security import verify_token
from onboard_agent.graph.build_graph import invoke_graph

router = APIRouter()


class ChatRequest(BaseModel):
    prompt: str


class ChatResponse(BaseModel):
    response: str


@router.get("/health")
def health() -> dict[str, str]:
    """Public liveness probe — intentionally unauthenticated for load balancers."""
    return {"status": "ok"}


@router.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest, _token: str = Depends(verify_token)) -> ChatResponse:
    try:
        result = invoke_graph(request.prompt)
    except Exception as exc:
        # Return a clean 502; the underlying error is logged server-side by the
        # request middleware rather than leaked to the client.
        raise HTTPException(status_code=502, detail="Chatbot request failed.") from exc

    return ChatResponse(response=result["messages"][-1].content)
