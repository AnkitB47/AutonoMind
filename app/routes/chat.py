"""Unified chat endpoint with multimodal fallbacks."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request, UploadFile, File
from pydantic import BaseModel
from agents import rag_agent, search_agent, translate_agent
from models.whisper_runner import transcribe_audio
from models.gemini_vision import extract_image_text

router = APIRouter(tags=["chat"])

class ChatRequest(BaseModel):
    message: str
    lang: str = "en"
    session_id: str | None = None


@router.post("/ocr")
async def ocr_image(file: UploadFile = File(...)) -> dict:
    data = await file.read()
    text = extract_image_text(data)
    return {"text": text}


@router.post("/transcribe")
async def transcribe(file: UploadFile = File(...)) -> dict:
    data = await file.read()
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


def _process_chat(text: str, lang: str, session_id: str | None) -> tuple[str, float]:
    ans, conf, src = rag_agent.query_pdf_image(text, session_id=session_id)
    if conf < 0.6 or src not in {"pdf", "image"}:
        ans = _fallback_search(text)
        conf = 0.0
    rag_agent.save_memory(text, ans, session_id=session_id)
    translated = translate_agent.translate_response(ans, lang)
    return translated, conf


@router.post("/chat")
async def chat_endpoint(request: Request, file: UploadFile | None = File(None)) -> dict:
    if file is not None:
        content = await file.read()
        lang = "en"
        session_id = None
        try:
            form = await request.form()
            lang = form.get("lang", "en")
            session_id = form.get("session_id")
        except Exception:
            pass
        if file.content_type in {"image/png", "image/jpeg", "image/gif", "image/webp"}:
            text = extract_image_text(content)
        elif file.content_type in {"audio/wav", "audio/webm", "audio/mpeg", "audio/x-wav"}:
            text = transcribe_audio(content)
        else:
            raise HTTPException(status_code=400, detail="Unsupported file type")
    else:
        data = await request.json()
        text = data.get("message")
        if not text:
            raise HTTPException(status_code=400, detail="message required")
        lang = data.get("lang", "en")
        session_id = data.get("session_id")

    reply, conf = _process_chat(text, lang, session_id)
    return {"reply": reply, "confidence": conf}
