# --- app/routes/input_handler.py ---
import requests
import streamlit as st
from fastapi import APIRouter, UploadFile, File
from agents import mcp_server, search_agent, translate_agent
from models.whisper_runner import transcribe_audio
from models.gemini_vision import extract_image_text
from agents.pod_monitor import is_runpod_live
from app.config import Settings

settings = Settings()
RUNPOD_URL = settings.RUNPOD_URL
router = APIRouter(prefix="/input", tags=["input"], trailing_slash=False)


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


@router.post("/search")
async def handle_search_input(payload: dict):
    query = payload.get("query")
    lang = payload.get("lang", "en")
    result = search_agent.handle_query(query)
    translated = translate_agent.translate_response(result, lang)
    return {"response": translated}


def render():
    st.subheader("📥 Ask via Text, Voice or Image")
    lang = st.selectbox("🌐 Choose Language:", ["en", "de", "fr", "hi"])

    # --- Text Input ---
    with st.expander("💬 Text Input"):
        query = st.text_input("Type your question")
        if st.button("Ask via Text") and query:
            with st.spinner("Thinking..."):
                result = mcp_server.route_with_langgraph(query, lang)
                st.success(result)

    # --- Voice Input ---
    with st.expander("🎤 Voice Input (WAV only)"):
        audio_file = st.file_uploader("Upload voice query", type=["wav"], key="voice_input")
        if audio_file and st.button("Ask via Voice"):
            with st.spinner("Transcribing..."):
                audio_bytes = audio_file.read()
                if is_runpod_live(RUNPOD_URL):
                    res = requests.post(f"{RUNPOD_URL}/transcribe", files={"file": audio_bytes})
                    query = res.json().get("text", "")
                else:
                    query = transcribe_audio(audio_bytes)

                st.info(f"🎧 Transcribed Text: `{query}`")
                result = mcp_server.route_with_langgraph(query, lang)
                st.success(result)

    # --- Image Input ---
    with st.expander("🖼️ Image Input (PNG, JPG)"):
        image_file = st.file_uploader("Upload an image", type=["png", "jpg", "jpeg"], key="image_input")
        if image_file and st.button("Ask via Image"):
            with st.spinner("Extracting from image..."):
                image_bytes = image_file.read()
                if is_runpod_live(RUNPOD_URL):
                    res = requests.post(f"{RUNPOD_URL}/vision", files={"file": image_bytes})
                    query = res.json().get("text", "")
                else:
                    query = extract_image_text(image_bytes)

                st.info(f"📝 Extracted Text: `{query}`")
                result = mcp_server.route_with_langgraph(query, lang)
                st.success(result)
