from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.routes import chat, upload
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

# Return the runtime backend URL to verify environment propagation
@app.get("/debug-env")
def debug_env() -> dict:
    return {"NEXT_PUBLIC_FASTAPI_URL": settings.NEXT_PUBLIC_FASTAPI_URL}

# Register routers
app.include_router(upload.router)
app.include_router(chat.router)
