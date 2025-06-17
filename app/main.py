from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes import upload, chat, image_similarity, input_handler

app = FastAPI(title="AutonoMind API", version="2.0")

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

# Register routers
app.include_router(upload.router)
app.include_router(chat.router)
app.include_router(image_similarity.router)
app.include_router(input_handler.router)
