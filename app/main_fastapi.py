# --- app/main_fastapi.py ---
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes import input_handler, file_upload, chat_api

app = FastAPI(
    title="AutonoMind API",
    description="Handles /input endpoints for text, voice, image",
    version="1.0.0",
)

# Allow frontend applications to call this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    return {"message": "AutonoMind FastAPI is running"}


# Include routes
app.include_router(input_handler.router)
app.include_router(file_upload.router)
app.include_router(chat_api.router)
