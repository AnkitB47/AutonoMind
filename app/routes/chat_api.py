# --- app/routes/chat_api.py ---
from fastapi import APIRouter, UploadFile, File, HTTPException, Request
from pydantic import BaseModel
from typing import List, Dict

from agents import rag_agent, search_agent, translate_agent
from models.whisper_runner import transcribe_audio
from models.gemini_vision import extract_image_text

router = APIRouter()


class Question(BaseModel):
    question: str
    session_id: str | None = None


class TextPayload(BaseModel):
    text: str
    session_id: str | None = None


class SearchPayload(BaseModel):
    query: str
    session_id: str | None = None


@router.post("/rag/query")
async def rag_query(payload: Question) -> Dict[str, float | str]:
    answer, conf, _ = rag_agent.query_with_confidence(payload.question, session_id=payload.session_id)
    return {"answer": answer, "confidence": conf}


@router.post("/ocr")
async def ocr_image(file: UploadFile = File(...)) -> Dict[str, str]:
    data = await file.read()
    text = extract_image_text(data)
    return {"text": text}


@router.post("/transcribe")
async def transcribe(file: UploadFile = File(...)) -> Dict[str, str]:
    data = await file.read()
    text = transcribe_audio(data)
    return {"text": text}


@router.post("/search/image")
async def search_image(payload: SearchPayload) -> Dict[str, List[Dict[str, str]]]:
    summary = search_agent.search_web(payload.query + " images")
    images = [{"url": line.split("\n")[0], "alt": line} for line in summary.split("\n\n")]
    return {"images": images}


@router.post("/voice/assist")
async def voice_assist(payload: TextPayload) -> Dict[str, str]:
    reply = search_agent.handle_query(payload.text)
    rag_agent.save_memory(payload.text, reply, session_id=payload.session_id)
    return {"reply": reply}


class ChatRequest(BaseModel):
    message: str
    lang: str = "en"
    session_id: str | None = None


def chat_logic(text: str, lang: str = "en", session_id: str | None = None):
    ans, conf, source = rag_agent.query_pdf_image(text, session_id=session_id)

    if source not in ("pdf", "image") or conf < 0.6:
        for fn in (
            search_agent.search_arxiv,
            search_agent.search_semantic_scholar,
            search_agent.search_web,
        ):
            result = fn(text)
            if result and "no" not in result.lower():
                ans = result
                break

    rag_agent.save_memory(text, ans, session_id=session_id)
    translated = translate_agent.translate_response(ans, lang)
    return translated, conf

SUPPORTED_IMAGES = {"image/png", "image/jpeg", "image/gif", "image/webp"}
SUPPORTED_AUDIO = {"audio/wav", "audio/webm", "audio/mpeg", "audio/x-wav"}


@router.post("/chat")
async def chat_endpoint(request: Request, file: UploadFile | None = File(None)) -> Dict[str, float | str]:
    if file is not None:
        content = await file.read()
        if file.content_type in SUPPORTED_IMAGES:
            text = extract_image_text(content)
        elif file.content_type in SUPPORTED_AUDIO:
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
