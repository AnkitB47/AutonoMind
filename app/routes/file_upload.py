# --- app/routes/file_upload.py ---
from fastapi import APIRouter, UploadFile, File
from agents import rag_agent

router = APIRouter(prefix="/file", tags=["file"])

@router.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    result = await rag_agent.process_file(file)
    return {"response": result}