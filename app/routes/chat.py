"""Unified /chat endpoint with multimodal support."""
from __future__ import annotations

import base64
import asyncio
import requests
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from agents import rag_agent
from agents.pod_monitor import is_runpod_live
from models.whisper_runner import transcribe_audio
from app.config import Settings
from app.schemas import ChatRequest

settings = Settings()
RUNPOD_URL = settings.RUNPOD_URL

router = APIRouter(tags=["chat"])


def _transcribe(data: bytes) -> str:
    if RUNPOD_URL and is_runpod_live(RUNPOD_URL):
        res = requests.post(f"{RUNPOD_URL}/transcribe", files={"file": data})
        return res.json().get("text", "")
    return transcribe_audio(data)


@router.post("/chat")
async def unified_chat(payload: ChatRequest):
    """Handle all chat modes and stream the final answer."""
    settings.validate_api_keys()
    if not payload.session_id:
        raise HTTPException(status_code=400, detail="session_id required")

    mode = payload.mode
    content = payload.content

    if mode == "voice":
        audio = base64.b64decode(content)
        content = _transcribe(audio)
        mode = "text"

    text, conf, src = rag_agent.handle_query(mode, content, payload.session_id, payload.lang)

    async def streamer():
        for tok in text.split():
            yield tok + " "
            await asyncio.sleep(0)

    headers = {
        "X-Session-ID": payload.session_id,
        "X-Confidence": str(conf),
        "X-Source": src or "",
    }
    return StreamingResponse(streamer(), media_type="text/plain", headers=headers)
