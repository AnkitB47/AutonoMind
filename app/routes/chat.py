# app/routes/chat.py
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse, JSONResponse
import agents.rag_agent as rag_agent
from agents import search_agent
from app.config import Settings
import base64, asyncio, json
import logging

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
        text, conf, src = await rag_agent.handle_query(mode, content, payload.session_id, payload.lang)
        # If image query failed, return error as plain text
        if (mode == "image" or (mode == "text" and src == None)) and isinstance(text, str) and text.startswith("Image query processing failed"):
            # Log error
            logging.getLogger(__name__).error(f"Image query failed: {text}")
            return JSONResponse(content={"error": text}, status_code=400)
        # Post-process RAG answers for conciseness
        if mode == "text" and src and src != "web":
            text = rag_agent.rewrite_answer(text, content, payload.lang)

    # Check if response is JSON (image query result)
    try:
        response_data = json.loads(text)
        if isinstance(response_data, dict) and ("image_url" in response_data or "description" in response_data or "results" in response_data):
            # Return structured JSON response for image queries
            headers = {
                "X-Session-ID": payload.session_id,
                "X-Confidence": str(conf),
                "X-Source": src or "",
                "Content-Type": "application/json"
            }
            return JSONResponse(content=response_data, headers=headers)
    except (json.JSONDecodeError, TypeError):
        # Not JSON, continue with streaming text response
        pass

    # Standard streaming text response
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
