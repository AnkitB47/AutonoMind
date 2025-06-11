# --- app/routes/chat_api.py ---
from fastapi import APIRouter, UploadFile, File
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


def chat_logic(message: str, lang: str = "en", session_id: str | None = None):
    answer, conf, source = rag_agent.query_with_confidence(message, session_id=session_id)
    if source not in ("pdf", "image") or conf < 0.6:
        # Fallback chain
        for fn in (
            search_agent.search_arxiv,
            search_agent.search_semantic_scholar,
            search_agent.search_web,
        ):
            result = fn(message)
            if result and "no" not in result.lower():
                answer = result
                break
    rag_agent.save_memory(message, answer, session_id=session_id)
    translated = translate_agent.translate_response(answer, lang)
    return translated, conf


@router.post("/chat")
async def chat_endpoint(payload: ChatRequest) -> Dict[str, float | str]:
    reply, conf = chat_logic(payload.message, payload.lang, payload.session_id)
    return {"reply": reply, "confidence": conf}
