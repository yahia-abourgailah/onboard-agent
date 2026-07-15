from __future__ import annotations

from fastapi import Depends, APIRouter, HTTPException
from pydantic import BaseModel
from onboard_agent.model.llm import llm
from langchain.messages import HumanMessage

from onboard_agent.api.security import verify_token

router = APIRouter()


class ChatRequest(BaseModel):
    prompt: str


class ChatResponse(BaseModel):
    response: str


@router.get("/health")
def health() -> dict[str, str]:
    """Public route/no token required"""
    return {"status": "ok"}


@router.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest, _token: str = Depends(verify_token)) -> ChatResponse:
    """Protected route/requires Authorization"""
    try:
        result = llm.invoke([HumanMessage(content=request.prompt)])  # should be graph invoke later
    except Exception as exc:
        raise HTTPException(status_code=502, detail="Chatbot request failed.") from exc

    return ChatResponse(response=result.content)
