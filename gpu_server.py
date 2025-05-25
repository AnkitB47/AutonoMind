# --- gpu_server.py ---
from fastapi import FastAPI, UploadFile, File
from models.whisper_runner import transcribe_audio
from models.gemini_vision import extract_image_text

app = FastAPI()


@app.get("/")
def health():
    return {"status": "RunPod GPU API running ✅"}


@app.post("/transcribe")
async def transcribe(file: UploadFile = File(...)):
    audio_bytes = await file.read()
    text = transcribe_audio(audio_bytes)
    return {"text": text}


@app.post("/vision")
async def vision(file: UploadFile = File(...)):
    image_bytes = await file.read()
    text = extract_image_text(image_bytes)
    return {"text": text}
