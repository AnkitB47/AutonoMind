from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import JSONResponse
import logging
from uuid import uuid4
from agents import rag_agent
from agents import clip_faiss  # For CLIP embedding
from models import gemini_vision  # For image captioning
import requests
import numpy as np
import os
from app.image_rag_utils import analyze_image_content

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

@router.post("/image-analyze")
async def image_analyze(file: UploadFile = File(...), session_id: str = Form("")):
    """Hybrid image pipeline: CLIP embedding, clip-retrieval, modular Gemini Vision captioning/OCR/summarization."""
    try:
        logger.info(f"Image-analyze request: filename={file.filename}, session_id={session_id}")
        # Validate file
        if not file.filename:
            raise HTTPException(status_code=400, detail="No filename provided")
        suffix = file.filename.rsplit(".", 1)[-1].lower()
        if suffix not in {"png", "jpg", "jpeg", "gif", "webp"}:
            raise HTTPException(status_code=400, detail="Unsupported image type")
        # Ensure session_id exists
        if not session_id:
            session_id = str(uuid4())
            logger.info(f"Generated new session_id: {session_id}")
        # Save file to disk
        contents = await file.read()
        save_dir = "uploaded_images"
        os.makedirs(save_dir, exist_ok=True)
        save_path = os.path.join(save_dir, f"{uuid4().hex}_{file.filename}")
        with open(save_path, "wb") as f_out:
            f_out.write(contents)
        logger.info(f"Saved uploaded image to {save_path}")
        # Compute CLIP embedding
        try:
            embedding = clip_faiss._encode_image(contents)
            embedding_list = embedding.tolist() if isinstance(embedding, np.ndarray) else list(embedding)
        except Exception as e:
            logger.error(f"CLIP embedding failed: {e}")
            raise HTTPException(status_code=500, detail="Failed to compute image embedding.")
        # Call clip-retrieval API
        clip_results = []
        clip_error = None
        try:
            clip_api_url = "https://knn.laion.ai/knn-service"
            payload = {
                "embedding": embedding_list,
                "indice_name": "laion5B-L-14",
                "num_images": 5
            }
            resp = requests.post(clip_api_url, json=payload, timeout=15)
            resp.raise_for_status()
            data = resp.json()
            # Expecting a list of dicts with keys: url, score, caption
            clip_results = [
                {
                    "url": item.get("url"),
                    "score": item.get("score"),
                    "caption": item.get("caption")
                }
                for item in data if item.get("url")
            ]
            logger.info(f"clip-retrieval returned {len(clip_results)} results for session {session_id}")
        except Exception as e:
            clip_error = str(e)
            logger.error(f"clip-retrieval failed: {clip_error}")
        # Modular Gemini Vision pipeline (OCR, summarize, describe)
        ai_caption_result = analyze_image_content(save_path)
        ai_caption = ai_caption_result.get("caption")
        ai_caption_method = ai_caption_result.get("method")
        # Logging
        logger.info({
            "session_id": session_id,
            "clip_results_count": len(clip_results),
            "clip_error": clip_error,
            "similarity_scores": [r["score"] for r in clip_results],
            "caption_method": ai_caption_method
        })
        # Response construction
        if not clip_results:
            clip_message = "No visually similar images found in the public gallery."
        else:
            clip_message = None
        if not ai_caption:
            ai_caption = "Unable to generate a description for this image."
        return {
            "session_id": session_id,
            "caption": ai_caption,
            "caption_method": ai_caption_method,
            "similar_images": clip_results,
            "clip_message": clip_message
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Image-analyze failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Image-analyze failed: {str(e)}")
