# --- app/routes/file_upload.py ---
import streamlit as st
from fastapi import APIRouter, UploadFile
from agents.rag_agent import process_file

router = APIRouter()


@router.post("/upload")
async def upload_file(file: UploadFile):
    result = await process_file(file)
    return {"message": result}


def render():
    st.subheader("📤 File Upload (PDF/Image)")
    uploaded_file = st.file_uploader("Choose a file", type=["pdf", "png", "jpg", "jpeg"])
    if uploaded_file:
        with st.spinner("Processing file..."):
            result = process_file(uploaded_file)
            st.success(result)
