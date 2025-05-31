# --- app/main.py ---
import streamlit as st
from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware
from app.routes import input_handler, file_upload, langgraph

# FastAPI backend setup
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount all API routers
app.include_router(input_handler.router)
app.include_router(file_upload.router)
app.include_router(langgraph.router)

# --- Streamlit frontend setup ---
st.set_page_config(page_title="AutonoMind AI", layout="wide")
st.title("🤖 AutonoMind AI - Agentic Multimodal Assistant")
st.info("Upload PDF/Image or Ask Anything")

# Sidebar navigation
option = st.sidebar.radio("🧭 Navigate", ["Home", "Text/Voice/Image Input", "File Upload", "LangGraph Controls"])

if option == "Text/Voice/Image Input":
    input_handler.render()
elif option == "File Upload":
    file_upload.render()
elif option == "LangGraph Controls":
    langgraph.render()
else:
    st.markdown("👋 Welcome to AutonoMind AI! Use the sidebar to interact with the app.")
