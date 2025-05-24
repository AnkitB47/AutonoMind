# --- app/main.py ---
import streamlit as st
from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware
from app.routes import input_handler, file_upload, langgraph

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(input_handler.router)
app.include_router(file_upload.router)
app.include_router(langgraph.router)

st.set_page_config(page_title="AutonoMind AI")
st.title("🤖 AutonoMind AI - Agentic Multimodal Assistant")
st.info("Upload PDF/Image or Ask Anything")
