# --- app/routes/file_upload.py ---
from fastapi import APIRouter, UploadFile
from agents.rag_agent import process_file

router = APIRouter()


@router.post("/upload")
async def upload_file(file: UploadFile, session_id: str | None = None):
    result = await process_file(file, session_id=session_id)
    return {"message": result}

