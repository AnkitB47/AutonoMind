# --- app/routes/chat_api.py ---
from fastapi import APIRouter, UploadFile, File
from pydantic import BaseModel
from typing import List, Dict

from agents import rag_agent, search_agent
from models.whisper_runner import transcribe_audio
from models.gemini_vision import extract_image_text

router = APIRouter(trailing_slash=False)


class Question(BaseModel):
    question: str


class TextPayload(BaseModel):
    text: str


class SearchPayload(BaseModel):
    query: str


@router.post("/rag/query")
async def rag_query(payload: Question) -> Dict[str, str | float]:
    answer = rag_agent.handle_text(payload.question)
    conf = 0.8
    low_markers = ["no match", "no faiss", "no pinecone", "don't know"]
    if any(m in answer.lower() for m in low_markers):
        conf = 0.3
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


@router.post("/search/web")
async def search_web(payload: SearchPayload) -> Dict[str, List[Dict[str, str]]]:
    summary = search_agent.search_web(payload.query)
    results = [{"title": line.split("\n")[0], "snippet": line, "url": ""} for line in summary.split("\n\n")]
    return {"results": results}


@router.post("/search/image")
async def search_image(payload: SearchPayload) -> Dict[str, List[Dict[str, str]]]:
    summary = search_agent.search_web(payload.query + " images")
    images = [{"url": line.split("\n")[0], "alt": line} for line in summary.split("\n\n")]
    return {"images": images}


@router.post("/voice/assist")
async def voice_assist(payload: TextPayload) -> Dict[str, str]:
    reply = search_agent.handle_query(payload.text)
    return {"reply": reply}


class ChatRequest(BaseModel):
    message: str


@router.post("/chat")
async def chat_endpoint(payload: ChatRequest) -> Dict[str, str]:
    rag_resp = await rag_query(Question(question=payload.message))
    if rag_resp["confidence"] >= 0.6 and "i don't know" not in rag_resp["answer"].lower():
        return {"reply": rag_resp["answer"]}

    # Fallback to web search
    search_resp = search_agent.search_web(payload.message)
    return {"reply": search_resp}
