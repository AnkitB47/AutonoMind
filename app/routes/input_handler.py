# --- app/routes/input_handler.py ---
from fastapi import APIRouter, UploadFile, File
from agents import mcp_server, translate_agent
from models.whisper_runner import transcribe_audio

router = APIRouter(prefix="/input", tags=["input"])

@router.post("/text")
async def handle_text_input(payload: dict):
    query = payload.get("query")
    lang = payload.get("lang", "en")
    result = mcp_server.route_with_langgraph(query, lang)
    return {"response": result}

@router.post("/voice")
async def handle_voice_input(file: UploadFile = File(...), lang: str = "en"):
    text = transcribe_audio(await file.read())
    result = mcp_server.route_with_langgraph(text, lang)
    return {"response": result}