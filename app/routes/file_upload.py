# --- app/routes/file_upload.py ---
from fastapi import APIRouter, UploadFile
from agents.rag_agent import process_file

router = APIRouter()

@router.post("/upload")
async def upload_file(file: UploadFile):
    result = await process_file(file)
    return {"message": result}
