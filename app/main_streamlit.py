# --- app/main_streamlit.py ---
import streamlit as st
from app.routes.input_handler import render

st.set_page_config(page_title="AutonoMind AI", layout="centered")
st.title("🤖 AutonoMind AI Assistant")

# Render unified input UI. In a CPU-only deployment this page can call the
# same FastAPI endpoints defined in `chat_api.py` using `requests` to provide
# a lightweight interface without the Next.js frontend.
render()
