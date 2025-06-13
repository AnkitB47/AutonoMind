"""File ingestion endpoints."""
from uuid import uuid4
from fastapi import APIRouter, UploadFile
from agents.rag_agent import process_file

router = APIRouter(tags=["upload"])

@router.post("/upload")
async def upload_file(file: UploadFile, session_id: str | None = None) -> dict:
    sid = session_id or str(uuid4())
    msg, _ = await process_file(file, session_id=sid)
    # Session id is stored internally for 1h in rag_agent.session_store
    return {"message": msg, "session_id": sid}
