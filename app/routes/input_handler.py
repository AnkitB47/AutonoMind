# --- app/routes/input_handler.py ---
import requests
from fastapi import APIRouter, UploadFile, File
from agents import search_agent, translate_agent
from app.routes.chat_api import chat_logic
import models.whisper_runner as whisper_runner
import models.gemini_vision as gemini_vision
from agents.pod_monitor import is_runpod_live
from app.config import Settings

settings = Settings()
RUNPOD_URL = settings.RUNPOD_URL
router = APIRouter(prefix="/input", tags=["input"])


@router.post("/text")
async def handle_text_input(payload: dict):
    query = payload.get("query")
    lang = payload.get("lang", "en")
    session_id = payload.get("session_id")
    reply, _ = chat_logic(query, lang, session_id)
    return {"response": reply}


@router.post("/voice")
async def handle_voice_input(file: UploadFile = File(...), lang: str = "en", session_id: str | None = None):
    audio_bytes = await file.read()
    if is_runpod_live(RUNPOD_URL):
        res = requests.post(f"{RUNPOD_URL}/transcribe", files={"file": audio_bytes})
        text = res.json().get("text", "")
    else:
        text = whisper_runner.transcribe_audio(audio_bytes)
    reply, _ = chat_logic(text, lang, session_id)
    return {"response": reply}


@router.post("/image")
async def handle_image_input(file: UploadFile = File(...), lang: str = "en", session_id: str | None = None):
    image_bytes = await file.read()
    if is_runpod_live(RUNPOD_URL):
        res = requests.post(f"{RUNPOD_URL}/vision", files={"file": image_bytes})
        image_text = res.json().get("text", "")
    else:
        image_text = gemini_vision.extract_image_text(image_bytes)
    reply, _ = chat_logic(image_text, lang, session_id)
    return {"response": reply}


@router.post("/search")
async def handle_search_input(payload: dict):
    query = payload.get("query")
    lang = payload.get("lang", "en")
    # search endpoint does not use session data but accept it for consistency
    payload.get("session_id")
    result = search_agent.handle_query(query)
    translated = translate_agent.translate_response(result, lang)
    return {"response": translated}
