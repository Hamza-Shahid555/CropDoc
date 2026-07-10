from typing import Literal, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ..agent.agent import run_agent

router = APIRouter()


class ChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str


class ChatRequest(BaseModel):
    message: str
    detected_disease: Optional[str] = None
    history: list[ChatMessage] = []


@router.post("/chat")
async def chat_endpoint(req: ChatRequest):
    try:
        reply = run_agent(
            message=req.message,
            history=[m.model_dump() for m in req.history],
            detected_disease=req.detected_disease,
        )
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))
    return {"reply": reply}
