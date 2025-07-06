from fastapi import FastAPI, UploadFile, File, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.routes import chat, upload
from app.config import Settings
import logging
import time
import uuid

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

settings = Settings()
app = FastAPI(title="AutonoMind API", version="2.0")
app.mount("/images", StaticFiles(directory=settings.IMAGE_STORE), name="images")

# Request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    request_id = str(uuid.uuid4())[:8]
    start_time = time.time()
    
    logger.info(f"[{request_id}] {request.method} {request.url.path} - Started")
    
    try:
        response = await call_next(request)
        process_time = time.time() - start_time
        logger.info(f"[{request_id}] {request.method} {request.url.path} - Completed in {process_time:.3f}s - Status: {response.status_code}")
        return response
    except Exception as e:
        process_time = time.time() - start_time
        logger.error(f"[{request_id}] {request.method} {request.url.path} - Failed in {process_time:.3f}s - Error: {str(e)}")
        raise

# Enable CORS for all origins. In production you might restrict this.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Simple health check
@app.get("/")
def root() -> dict:
    return {"message": "AutonoMind backend running"}

# Lightweight ping for health checks
@app.get("/ping")
def ping() -> dict:
    return {"status": "ok", "timestamp": time.time()}

# Return the runtime backend URL to verify environment propagation
@app.get("/debug-env")
def debug_env() -> dict:
    return {
        "NEXT_PUBLIC_FASTAPI_URL": settings.NEXT_PUBLIC_FASTAPI_URL,
        "message": "FastAPI is reachable via proxy",
        "timestamp": time.time()
    }

# Debug upload endpoint for troubleshooting
@app.post("/debug-upload")
async def debug_upload(file: UploadFile = File(...), session_id: str = ""):
    """Debug endpoint to log incoming file size and session_id."""
    try:
        file_size = len(await file.read())
        logger.info(f"DEBUG: File upload - name: {file.filename}, size: {file_size}, session_id: {session_id}")
        return {
            "filename": file.filename,
            "size": file_size,
            "session_id": session_id,
            "content_type": file.content_type,
            "message": "Debug upload successful",
            "timestamp": time.time()
        }
    except Exception as e:
        logger.error(f"Debug upload failed: {str(e)}", exc_info=True)
        raise

# Debug chat endpoint for troubleshooting
@app.post("/debug-chat")
async def debug_chat():
    """Debug endpoint to verify chat routing."""
    return {
        "message": "Chat endpoint is reachable",
        "timestamp": time.time()
    }

# Connection test endpoint
@app.get("/debug-connection")
async def debug_connection(request: Request):
    """Test endpoint to verify connection details."""
    return {
        "client_host": request.client.host if request.client else "unknown",
        "headers": dict(request.headers),
        "method": request.method,
        "url": str(request.url),
        "timestamp": time.time()
    }

# Session debug endpoint
@app.get("/debug-session/{session_id}")
async def debug_session(session_id: str):
    """Debug endpoint to check session context and upload history."""
    from agents.rag_agent import session_store
    session_info = session_store.get(session_id, {})
    return {
        "session_id": session_id,
        "session_info": session_info,
        "has_session": session_id in session_store,
        "timestamp": time.time()
    }

# Register routers
app.include_router(upload.router)
app.include_router(chat.router)
