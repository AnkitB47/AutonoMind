"""Unified chat endpoint with multimodal fallbacks."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request, UploadFile, File
from uuid import uuid4
from pydantic import BaseModel
from agents import rag_agent, search_agent, translate_agent
from agents.rag_agent import search_clip_image
from models.whisper_runner import transcribe_audio
from models.gemini_vision import extract_image_text
from agents.pod_monitor import is_runpod_live
from app.config import Settings
import requests
import tempfile
import os

settings = Settings()
RUNPOD_URL = settings.RUNPOD_URL

router = APIRouter(tags=["chat"])

class ChatRequest(BaseModel):
    message: str
    lang: str = "en"
    session_id: str | None = None


@router.post("/ocr")
async def ocr_image(file: UploadFile = File(...)) -> dict:
    data = await file.read()
    if RUNPOD_URL and is_runpod_live(RUNPOD_URL):
        res = requests.post(f"{RUNPOD_URL}/vision", files={"file": data})
        text = res.json().get("text", "")
    else:
        text = extract_image_text(data)
    return {"text": text}


@router.post("/transcribe")
async def transcribe(file: UploadFile = File(...)) -> dict:
    data = await file.read()
    if RUNPOD_URL and is_runpod_live(RUNPOD_URL):
        res = requests.post(f"{RUNPOD_URL}/transcribe", files={"file": data})
        text = res.json().get("text", "")
    else:
        text = transcribe_audio(data)
    return {"text": text}


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


def chat_logic(text: str, lang: str, session_id: str | None) -> tuple[str, float]:
    """Run RAG search with fallbacks and save memory."""
    try:
        ans, conf, src = rag_agent.query_pdf_image(text, session_id=session_id)
    except Exception:
        ans, conf, src = "", 0.0, None
    if conf >= 0.6 and src == "image":
        rag_agent.save_memory(text, ans, session_id=session_id)
        translated = translate_agent.translate_response(ans, lang)
        return translated, conf
    if conf < 0.6 or src not in {"pdf", "image"}:
        for fn in (
            search_agent.search_arxiv,
            search_agent.search_semantic_scholar,
            search_agent.search_web,
        ):
            try:
                res = fn(text)
                if res and "no" not in res.lower():
                    ans, conf = res, 0.0
                    break
            except Exception:
                continue
        if not ans:
            ans = "No answer found"
    rag_agent.save_memory(text, ans, session_id=session_id)
    translated = translate_agent.translate_response(ans, lang)
    return translated, conf


@router.post("/chat")
async def chat_endpoint(request: Request, file: UploadFile | None = File(None)) -> dict:
    if file is not None:
        content = await file.read()
        if not content:
            raise HTTPException(status_code=400, detail="empty file")
        lang = "en"
        session_id = None
        try:
            form = await request.form()
            lang = form.get("lang", "en")
            session_id = form.get("session_id")
        except Exception:
            pass
        try:
            if file.content_type and file.content_type.startswith("image/"):
                with tempfile.NamedTemporaryFile(delete=False, suffix=".img") as tmp:
                    tmp.write(content)
                    tmp_path = tmp.name
                text = extract_image_text(tmp_path)
                os.remove(tmp_path)
            elif file.content_type in {"audio/wav", "audio/webm", "audio/mpeg", "audio/x-wav"}:
                if RUNPOD_URL and is_runpod_live(RUNPOD_URL):
                    res = requests.post(f"{RUNPOD_URL}/transcribe", files={"file": content})
                    text = res.json().get("text", "")
                else:
                    text = transcribe_audio(content)
            else:
                raise HTTPException(status_code=400, detail="Unsupported file type")
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Processing failed: {e}")
    else:
        data = await request.json()
        text = data.get("message")
        if not text:
            raise HTTPException(status_code=400, detail="message required")
        lang = data.get("lang", "en")
        session_id = data.get("session_id")

    if not session_id:
        session_id = str(uuid4())

    reply, conf = chat_logic(text, lang, session_id)
    return {"reply": reply, "confidence": conf, "session_id": session_id}
