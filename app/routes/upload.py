"""File ingestion endpoints."""
from fastapi import APIRouter, UploadFile, HTTPException, File, Form
from app.config import Settings
from agents.rag_agent import process_file

router = APIRouter(tags=["upload"])
settings = Settings()

@router.post("/upload")
async def upload_file(
    session_id: str = Form(...), file: UploadFile = File(...)
) -> dict:
    settings.validate_api_keys()
    msg, _ = await process_file(file, session_id=session_id)
    if not msg.startswith("✅"):
        raise HTTPException(status_code=400, detail=msg)
    return {"message": msg, "session_id": session_id}
