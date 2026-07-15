
from __future__ import annotations
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from onboard_agent.model.llm import llm
from langchain_core.messages import HumanMessage
from onboard_agent.graph.build_graph import invoke_graph


app = FastAPI()


class ChatRequest(BaseModel):
    prompt: str 

class ChatResponse(BaseModel):
    response: str


@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest) -> ChatResponse:
    try:
        result = invoke_graph(request.prompt)
    except Exception as exc: 
        raise HTTPException(status_code=502, detail="Chatbot request failed.") from exc

    last_message = result["messages"][-1]
    return ChatResponse(response=last_message.content)