# --- app/routes/chat_api.py ---
"""Chat endpoint using RAG search with fallback."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request, UploadFile, File
from pydantic import BaseModel

from agents import rag_agent, search_agent, translate_agent
from models.whisper_runner import transcribe_audio
from models.gemini_vision import extract_image_text

router = APIRouter()


class TextPayload(BaseModel):
    text: str
    session_id: str | None = None


class SearchPayload(BaseModel):
    query: str
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


@router.post("/search/image")
async def search_image(payload: SearchPayload) -> dict:
    summary = search_agent.search_web(payload.query + " images")
    images = [{"url": line.split("\n")[0], "alt": line} for line in summary.split("\n\n")]
    return {"images": images}


@router.post("/voice/assist")
async def voice_assist(payload: TextPayload) -> dict:
    reply = search_agent.handle_query(payload.text)
    rag_agent.save_memory(payload.text, reply, session_id=payload.session_id)
    return {"reply": reply}


class ChatRequest(BaseModel):
    message: str
    lang: str = "en"
    session_id: str | None = None


def chat_logic(text: str, lang: str = "en", session_id: str | None = None) -> tuple[str, float]:
    ans, conf, source = rag_agent.query_pdf_image(text, session_id=session_id)
    if source not in {"pdf", "image"} or conf < 0.6:
        for fn in (
            search_agent.search_arxiv,
            search_agent.search_semantic_scholar,
            search_agent.search_web,
        ):
            res = fn(text)
            if res and "no" not in res.lower():
                ans, conf = res, 0.0
                break
    rag_agent.save_memory(text, ans, session_id=session_id)
    translated = translate_agent.translate_response(ans, lang)
    return translated, conf


@router.post("/chat")
async def chat_endpoint(request: Request, file: UploadFile | None = File(None)) -> dict:
    if file is not None:
        content = await file.read()
        if file.content_type in {"image/png", "image/jpeg", "image/gif", "image/webp"}:
            text = extract_image_text(content)
        elif file.content_type in {"audio/wav", "audio/webm", "audio/mpeg", "audio/x-wav"}:
            text = transcribe_audio(content)
        else:
            raise HTTPException(status_code=400, detail="Unsupported file type")
        lang = "en"
        session_id = None
        try:
            form = await request.form()
            lang = form.get("lang", "en")
            session_id = form.get("session_id")
        except Exception:
            pass
    else:
        data = await request.json()
        text = data.get("message")
        if not text:
            raise HTTPException(status_code=400, detail="message required")
        lang = data.get("lang", "en")
        session_id = data.get("session_id")

    reply, conf = chat_logic(text, lang, session_id)
    return {"reply": reply, "confidence": conf}
