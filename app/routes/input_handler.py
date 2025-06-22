# --- app/routes/input_handler.py ---
import requests
import tempfile
import os
from fastapi import APIRouter, UploadFile, File, Form
from agents import search_agent, translate_agent
from models.whisper_runner import transcribe_audio
from models.gemini_vision import extract_image_text
from agents.pod_monitor import is_runpod_live
from app.routes.chat import chat_logic
from app.config import Settings
from app.schemas import TextInput, SearchInput

settings = Settings()
RUNPOD_URL = settings.RUNPOD_URL
router = APIRouter(prefix="/input", tags=["input"])


@router.post("/text")
async def handle_text_input(payload: TextInput):
    try:
        query = payload.query
        lang = payload.lang
        session_id = payload.session_id
        if not query or not query.strip():
            return {"error": "query required"}
        if not session_id:
            return {"error": "session_id required"}

        reply, _, _ = chat_logic(query, lang, session_id)
        return {"response": reply}
    except Exception as e:  # pragma: no cover - defensive
        return {"error": str(e)}


@router.post("/voice")
async def handle_voice_input(
    file: UploadFile = File(...),
    lang: str = Form("en"),
    session_id: str | None = Form(None),
):
    try:
        if not session_id:
            return {"error": "session_id required"}
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

        reply, _, _ = chat_logic(text, lang, session_id)
        return {"response": reply}
    except Exception as e:  # pragma: no cover - defensive
        return {"error": str(e)}


@router.post("/image")
async def handle_image_input(
    file: UploadFile = File(...),
    lang: str = Form("en"),
    session_id: str | None = Form(None),
):
    try:
        if not session_id:
            return {"error": "session_id required"}
        image_bytes = await file.read()
        if not image_bytes:
            return {"error": "empty image"}
        try:
            if is_runpod_live(RUNPOD_URL):
                res = requests.post(f"{RUNPOD_URL}/vision", files={"file": image_bytes})
                image_text = res.json().get("text", "")
            else:
                with tempfile.NamedTemporaryFile(delete=False, suffix=".img") as tmp:
                    tmp.write(image_bytes)
                    tmp_path = tmp.name
                try:
                    image_text = extract_image_text(tmp_path)
                finally:
                    os.remove(tmp_path)
        except Exception as e:
            return {"error": f"image OCR failed: {e}"}
        reply, _, _ = chat_logic(image_text, lang, session_id)
        return {"response": reply}
    except Exception as e:  # pragma: no cover - defensive
        return {"error": str(e)}


@router.post("/search")
async def handle_search_input(payload: SearchInput):
    try:
        query = payload.query
        lang = payload.lang
        session_id = payload.session_id
        if not query or not query.strip():
            return {"error": "query required"}
        if not session_id:
            return {"error": "session_id required"}
        result = search_agent.handle_query(query)
        translated = translate_agent.translate_response(result, lang)
        return {"response": translated}
    except Exception as e:  # pragma: no cover - defensive
        return {"error": str(e)}
