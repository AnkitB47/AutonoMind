from fastapi import APIRouter, UploadFile, File

from agents import rag_agent

router = APIRouter(tags=["upload"])


@router.post("/upload")
async def upload(file: UploadFile = File(...), session_id: str = ""):
    """Ingest a PDF or image and return session info."""
    message, sid = await rag_agent.process_file(file, session_id or None)
    return {"message": message, "session_id": sid}
