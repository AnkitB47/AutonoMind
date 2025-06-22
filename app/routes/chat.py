"""Unified chat endpoint with multimodal fallbacks."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException, UploadFile, File
from agents import rag_agent, search_agent, translate_agent
from models.whisper_runner import transcribe_audio
from models.gemini_vision import extract_image_text
from agents.pod_monitor import is_runpod_live
from app.config import Settings
from app.schemas import ChatRequest
import requests
import tempfile
import os

settings = Settings()
RUNPOD_URL = settings.RUNPOD_URL

router = APIRouter(tags=["chat"])


@router.post("/ocr")
async def ocr_image(file: UploadFile = File(...)) -> dict:
    """Run OCR on the uploaded image using Gemini Vision."""
    try:
        settings.validate_api_keys()
        data = await file.read()
        if RUNPOD_URL and is_runpod_live(RUNPOD_URL):
            res = requests.post(f"{RUNPOD_URL}/vision", files={"file": data})
            text = res.json().get("text", "")
        else:
            with tempfile.NamedTemporaryFile(suffix=".img", delete=False) as tmp:
                tmp.write(data)
                tmp_path = tmp.name
            try:
                text = extract_image_text(tmp_path)
            finally:
                os.remove(tmp_path)
        return {"text": text}
    except Exception as e:  # pragma: no cover - defensive
        return {"error": str(e)}


@router.post("/transcribe")
async def transcribe(file: UploadFile = File(...)) -> dict:
    """Transcribe an uploaded audio file."""
    try:
        settings.validate_api_keys()
        data = await file.read()
        if RUNPOD_URL and is_runpod_live(RUNPOD_URL):
            res = requests.post(f"{RUNPOD_URL}/transcribe", files={"file": data})
            text = res.json().get("text", "")
        else:
            text = transcribe_audio(data)
        return {"text": text}
    except Exception as e:  # pragma: no cover - defensive
        return {"error": str(e)}


def _fallback_search(text: str) -> str:
    for fn in (
        search_agent.search_arxiv,
        search_agent.search_semantic_scholar,
        search_agent.search_web,
    ):
        res = fn(text)
        if res and "no" not in res.lower():
            return res
    return "No answer found"


def chat_logic(text: str, lang: str, session_id: str | None) -> tuple[str, float, str | None]:
    """Run RAG search with fallbacks and save memory."""
    raw = rag_agent.session_store.get(session_id, {}).get("text", "")
    combined = f"{raw}\n\nUser question: {text}" if raw else text
    try:
        ans, conf, src = rag_agent.query_pdf_image(combined, session_id=session_id)
    except Exception:
        ans, conf, src = "", 0.0, None

    if src == "image":
        rag_agent.save_memory(text, ans, session_id=session_id)
        return ans, conf, src

    if conf < settings.MIN_RAG_CONFIDENCE:
        ans = _fallback_search(text)
        conf = 0.0
        src = None

    rag_agent.save_memory(text, ans, session_id=session_id)
    translated = translate_agent.translate_response(ans, lang)
    return translated, conf, src


@router.post("/chat")
async def chat_endpoint(payload: ChatRequest) -> dict:
    try:
        settings.validate_api_keys()
        if not payload.session_id:
            raise HTTPException(status_code=400, detail="session_id required")

        reply, conf, src = chat_logic(
            payload.message, payload.lang, payload.session_id
        )
        if src == "image":
            return {
                "image_url": reply,
                "confidence": conf,
                "session_id": payload.session_id,
            }
        return {
            "reply": reply,
            "confidence": conf,
            "session_id": payload.session_id,
        }
    except HTTPException as exc:
        # Re-raise HTTPExceptions to preserve status
        raise exc
    except Exception as e:  # pragma: no cover - defensive
        return {"error": str(e)}
