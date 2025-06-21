"""File ingestion endpoints."""
from uuid import uuid4
from fastapi import APIRouter, UploadFile, HTTPException
from app.config import Settings
from agents.rag_agent import process_file

router = APIRouter(tags=["upload"])
settings = Settings()

@router.post("/upload")
async def upload_file(file: UploadFile, session_id: str | None = None) -> dict:
    settings.validate_api_keys()
    sid = session_id or str(uuid4())
    msg, _ = await process_file(file, session_id=sid)
    if not msg.startswith("✅"):
        raise HTTPException(status_code=400, detail=msg)
    return {"message": msg, "session_id": sid}
