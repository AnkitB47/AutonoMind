# --- app/routes/input_handler.py ---
import requests
from fastapi import APIRouter, UploadFile, File
from agents import search_agent, translate_agent
from models.whisper_runner import transcribe_audio
from models.gemini_vision import extract_image_text
from agents.pod_monitor import is_runpod_live
from app.routes.chat import chat_logic
from app.config import Settings

settings = Settings()
RUNPOD_URL = settings.RUNPOD_URL
router = APIRouter(prefix="/input", tags=["input"])


@router.post("/text")
async def handle_text_input(payload: dict):
    query = payload.get("query")
    lang = payload.get("lang", "en")
    session_id = payload.get("session_id")
    if not query or not query.strip():
        return {"error": "query required"}

    if session_id:
        reply, _ = chat_logic(query, lang, session_id)
    else:
        result = search_agent.handle_query(query)
        reply = translate_agent.translate_response(result, lang)

    return {"response": reply}


@router.post("/voice")
async def handle_voice_input(
    file: UploadFile = File(...), lang: str = "en", session_id: str | None = None
):
    audio_bytes = await file.read()
    if not audio_bytes:
        return {"error": "empty audio"}
    try:
        if is_runpod_live(RUNPOD_URL):
            res = requests.post(
                f"{RUNPOD_URL}/transcribe", files={"file": audio_bytes}
            )
            text = res.json().get("text", "")
        else:
            text = transcribe_audio(audio_bytes)
    except Exception as e:
        return {"error": f"transcription failed: {e}"}

    query = text.lower()
    if not query.strip():
        return {"error": "empty transcription"}
    if session_id:
        reply, _ = chat_logic(text, lang, session_id)
    else:
        result = search_agent.handle_query(text)
        reply = translate_agent.translate_response(result, lang)

    return {"response": reply}


@router.post("/image")
async def handle_image_input(file: UploadFile = File(...), lang: str = "en", session_id: str | None = None):
    image_bytes = await file.read()
    if not image_bytes:
        return {"error": "empty image"}
    try:
        if is_runpod_live(RUNPOD_URL):
            res = requests.post(f"{RUNPOD_URL}/vision", files={"file": image_bytes})
            image_text = res.json().get("text", "")
        else:
            image_text = extract_image_text(image_bytes)
    except Exception as e:
        return {"error": f"image OCR failed: {e}"}
    reply, _ = chat_logic(image_text, lang, session_id)
    return {"response": reply}


@router.post("/search")
async def handle_search_input(payload: dict):
    query = payload.get("query")
    lang = payload.get("lang", "en")
    # search endpoint does not use session data but accept it for consistency
    payload.get("session_id")
    if not query or not query.strip():
        return {"error": "query required"}
    result = search_agent.handle_query(query)
    translated = translate_agent.translate_response(result, lang)
    return {"response": translated}
