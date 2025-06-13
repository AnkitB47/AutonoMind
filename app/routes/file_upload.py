# --- app/routes/file_upload.py ---
from fastapi import APIRouter, UploadFile
from uuid import uuid4
from agents.rag_agent import process_file

router = APIRouter()


@router.post("/upload")
async def upload_file(
    file: UploadFile,
    session_id: str | None = None,
) -> dict:
    sid = session_id or str(uuid4())
    result = await process_file(file, session_id=sid)
    return {"message": result, "session_id": sid}

