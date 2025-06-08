# --- app/routes/file_upload.py ---
import streamlit as st
from fastapi import APIRouter, UploadFile
from agents.rag_agent import process_file
import asyncio

router = APIRouter(trailing_slash=False)


@router.post("/upload")
async def upload_file(file: UploadFile):
    result = await process_file(file)
    return {"message": result}


def render():
    st.subheader("📤 File Upload (PDF/Image)")
    uploaded_file = st.file_uploader("Choose a file", type=["pdf", "png", "jpg", "jpeg"])
    if uploaded_file and st.button("Upload and Ingest"):
        with st.spinner("Processing..."):
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(process_file(uploaded_file))
            st.success(result)
