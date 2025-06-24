from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.routes import upload, chat, image_search, input_handler
from app.config import Settings

settings = Settings()
app = FastAPI(title="AutonoMind API", version="2.0")
app.mount("/images", StaticFiles(directory=settings.IMAGE_STORE), name="images")

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
    return {"status": "ok"}

# Register routers
app.include_router(upload.router, prefix="/api")
app.include_router(chat.router, prefix="/api")
app.include_router(image_search.router, prefix="/api")
app.include_router(input_handler.router, prefix="/api")
