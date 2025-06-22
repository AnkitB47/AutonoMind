"""File ingestion endpoints."""
from fastapi import APIRouter, UploadFile, HTTPException, File, Form
from app.config import Settings
from agents.rag_agent import process_file

router = APIRouter(tags=["upload"])
settings = Settings()

@router.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    session_id: str | None = Form(None),
) -> dict:
    """Ingest a file and return the session id used."""
    settings.validate_api_keys()
    msg, sid = await process_file(file, session_id=session_id)
    if not msg.startswith("✅"):
        raise HTTPException(status_code=400, detail=msg)
    return {"message": msg, "session_id": sid}
