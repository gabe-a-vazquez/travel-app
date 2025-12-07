from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from src.services.llm import generate_response

router = APIRouter()


class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    response: str


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    if not request.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty")

    response = await generate_response(request.message)
    return ChatResponse(response=response)
