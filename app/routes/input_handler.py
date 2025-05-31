# --- app/routes/input_handler.py ---
import requests
import streamlit as st
from fastapi import APIRouter, UploadFile, File
from agents import mcp_server
from models.whisper_runner import transcribe_audio
from models.gemini_vision import extract_image_text
from agents.pod_monitor import is_runpod_live
from app.config import Settings

settings = Settings()
RUNPOD_URL = settings.RUNPOD_URL
router = APIRouter(prefix="/input", tags=["input"])


@router.post("/text")
async def handle_text_input(payload: dict):
    query = payload.get("query")
    lang = payload.get("lang", "en")
    result = mcp_server.route_with_langgraph(query, lang)
    return {"response": result}


@router.post("/voice")
async def handle_voice_input(file: UploadFile = File(...), lang: str = "en"):
    audio_bytes = await file.read()
    if is_runpod_live(RUNPOD_URL):
        res = requests.post(f"{RUNPOD_URL}/transcribe", files={"file": audio_bytes})
        text = res.json().get("text", "")
    else:
        text = transcribe_audio(audio_bytes)
    result = mcp_server.route_with_langgraph(text, lang)
    return {"response": result}


@router.post("/image")
async def handle_image_input(file: UploadFile = File(...), lang: str = "en"):
    image_bytes = await file.read()
    if is_runpod_live(RUNPOD_URL):
        res = requests.post(f"{RUNPOD_URL}/vision", files={"file": image_bytes})
        image_text = res.json().get("text", "")
    else:
        image_text = extract_image_text(image_bytes)
    result = mcp_server.route_with_langgraph(image_text, lang)
    return {"response": result}


def render():
    st.subheader("📥 Input Handler")
    query = st.text_input("Enter your question:")
    lang = st.selectbox("Select language:", ["en", "de", "fr", "hi"])

    if st.button("Ask"):
        result = mcp_server.route_with_langgraph(query, lang)
        st.success(result)
