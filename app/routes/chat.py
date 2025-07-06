# app/routes/chat.py
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
import agents.rag_agent as rag_agent
from agents import search_agent
from app.config import Settings
import base64, asyncio

from app.schemas import ChatRequest
from models.whisper_runner import transcribe_audio

settings = Settings()
router = APIRouter(tags=["chat"])

def _transcribe(audio_b64: str) -> str:
    data = base64.b64decode(audio_b64)
    return transcribe_audio(data)

@router.post("/chat")
async def unified_chat(payload: ChatRequest):
    settings.validate_api_keys()
    if not payload.session_id:
        raise HTTPException(400, "session_id required")

    mode, content = payload.mode, payload.content
    # if voice: content already base64-audio, transcribe upstream
    if mode=="voice":
        content = _transcribe(content)
        mode = "text"

    if mode == "search":
        text = search_agent.handle_query(content)
        conf = 1.0
        src = "web"
    else:
        text, conf, src = rag_agent.handle_query(mode, content, payload.session_id, payload.lang)

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
