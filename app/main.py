# --- app/main.py ---
import streamlit as st
from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware
from app.routes import input_handler, file_upload

# FastAPI Backend Setup
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(input_handler.router)
app.include_router(file_upload.router)

# --- Streamlit UI ---
st.set_page_config(page_title="AutonoMind AI", layout="wide")
st.title("🤖 AutonoMind AI - Agentic Multimodal Assistant")
st.info("Upload a file or ask something. All in one place.")

st.header("🗣️ Text / Voice / Image Input")
input_handler.render()

st.markdown("---")
st.header("📤 File Upload (PDF / Image)")
file_upload.render()
