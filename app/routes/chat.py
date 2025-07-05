# app/routes/chat.py
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from agents.rag_agent import handle_query
from app.config import Settings
import base64, asyncio

from app.schemas import ChatRequest

settings = Settings()
router = APIRouter(tags=["chat"])

@router.post("/chat")
async def unified_chat(payload: ChatRequest):
    settings.validate_api_keys()
    if not payload.session_id:
        raise HTTPException(400, "session_id required")

    mode, content = payload.mode, payload.content
    # if voice: content already base64-audio, transcribe upstream
    if mode=="voice":
        pass

    text,conf,src = handle_query(mode, content, payload.session_id, payload.lang)

    async def streamer():
        for tok in text.split():
            yield tok + " "
            await asyncio.sleep(0)

    headers={
      "X-Session-ID": payload.session_id,
      "X-Confidence": str(conf),
      "X-Source": src or ""
    }
    return StreamingResponse(streamer(), media_type="text/plain", headers=headers)
