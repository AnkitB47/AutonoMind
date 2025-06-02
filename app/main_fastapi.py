# --- app/main_fastapi.py ---
from fastapi import FastAPI
from app.routes import input_handler, file_upload

app = FastAPI(
    title="AutonoMind API",
    description="Handles /input endpoints for text, voice, image",
    version="1.0.0",
)

# Include routes
app.include_router(input_handler.router)
app.include_router(file_upload.router)
