# --- app/main_streamlit.py ---
import streamlit as st
import threading
import uvicorn
from fastapi import FastAPI
from app.routes import input_handler

api_app = FastAPI()
api_app.include_router(input_handler.router)

def _run_api():
    uvicorn.run(api_app, host="0.0.0.0", port=8080, log_level="info")

@st.experimental_singleton
def start_api():
    t = threading.Thread(target=_run_api, daemon=True)
    t.start()
    return t

start_api()

from app.routes.input_handler import render

st.set_page_config(page_title="AutonoMind AI", layout="centered")
st.title("🤖 AutonoMind AI Assistant")

# Render unified input UI
render()
