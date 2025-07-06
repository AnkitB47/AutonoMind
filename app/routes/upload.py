from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import JSONResponse
import logging
from uuid import uuid4
from agents import rag_agent

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(tags=["upload"])

# File size limits (50MB for PDFs, 10MB for images)
MAX_PDF_SIZE = 50 * 1024 * 1024  # 50MB
MAX_IMAGE_SIZE = 10 * 1024 * 1024  # 10MB

@router.post("/upload")
async def upload(file: UploadFile = File(...), session_id: str = Form("")):
    """Ingest a PDF or image and return session info."""
    try:
        # Log incoming request
        logger.info(f"Upload request: filename={file.filename}, size={file.size}, session_id={session_id}")
        
        # Validate file
        if not file.filename:
            raise HTTPException(status_code=400, detail="No filename provided")
        
        # Check file size
        file_size = file.size or 0
        suffix = file.filename.rsplit(".", 1)[-1].lower()
        
        if suffix == "pdf" and file_size > MAX_PDF_SIZE:
            raise HTTPException(status_code=413, detail=f"PDF too large: {file_size} bytes (max {MAX_PDF_SIZE})")
        elif suffix in {"png", "jpg", "jpeg", "gif", "webp"} and file_size > MAX_IMAGE_SIZE:
            raise HTTPException(status_code=413, detail=f"Image too large: {file_size} bytes (max {MAX_IMAGE_SIZE})")
        
        # Ensure session_id exists
        if not session_id:
            session_id = str(uuid4())
            logger.info(f"Generated new session_id: {session_id}")
        
        # Process file
        logger.info(f"Processing file: {file.filename} for session: {session_id}")
        message, sid = await rag_agent.process_file(file, session_id)
        
        logger.info(f"Upload successful: {message} for session: {sid}")
        return {"message": message, "session_id": sid}
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Upload failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Upload processing failed: {str(e)}")

@router.post("/debug-upload")
async def debug_upload(file: UploadFile = File(...), session_id: str = Form("")):
    """Debug endpoint to log incoming file size and session_id."""
    try:
        file_size = len(await file.read())
        logger.info(f"DEBUG: File upload - name: {file.filename}, size: {file_size}, session_id: {session_id}")
        return {
            "filename": file.filename,
            "size": file_size,
            "session_id": session_id or str(uuid4()),
            "content_type": file.content_type,
            "message": "Debug upload successful"
        }
    except Exception as e:
        logger.error(f"Debug upload failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Debug upload failed: {str(e)}")
