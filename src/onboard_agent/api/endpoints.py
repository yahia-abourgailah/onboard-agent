"""HTTP routes for the onboarding agent.

Resolves the merge between the agent endpoint (ran the graph, no auth) and the
auth endpoint (had auth, but only a stub response) into a single router: a public
health check plus a token-protected /chat that actually runs the agent.
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
    # FIX (FIX-4): protect /chat with verify_token — the agent endpoint had no auth,
    # the auth endpoint had no agent. This keeps both.
    # FIX (FIX-3): route the question through the LangGraph agent instead of calling
    # the raw model, so the SQL and vector tools are actually used. (This also drops
    # the old `from langchain.messages import HumanMessage` — FIX-2, a wrong module
    # path — since the graph builds its own messages.)
    try:
        result = invoke_graph(request.prompt)
    except Exception as exc:
        # Return a clean 502; the underlying error is logged server-side by the
        # request middleware rather than leaked to the client.
        raise HTTPException(status_code=502, detail="Chatbot request failed.") from exc

    return ChatResponse(response=result["messages"][-1].content)
