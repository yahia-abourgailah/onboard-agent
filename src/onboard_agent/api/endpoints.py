
from __future__ import annotations
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from onboard_agent.model.llm import llm
from langchain.messages import HumanMessage



app = FastAPI()


class ChatRequest(BaseModel):
    prompt: str 

class ChatResponse(BaseModel):
    response: str


@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest) -> ChatResponse:
    try:
        result = llm.invoke([HumanMessage(content=request.prompt)]) # should be graph invoke later
    except Exception as exc: 
        raise HTTPException(status_code=502, detail="Chatbot request failed.") from exc

    return ChatResponse(response=result.content)