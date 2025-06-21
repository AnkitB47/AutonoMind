# whisper_runner.py
import whisper
import os

model = None  # Global model reference

def transcribe_audio(audio_bytes):
    if not audio_bytes:
        raise ValueError("Empty audio data")
    global model
    if model is None:
        model = whisper.load_model("base")

    import tempfile
    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
        tmp.write(audio_bytes)
        path = tmp.name

    try:
        result = model.transcribe(path)
    finally:
        try:
            os.remove(path)
        except Exception:
            pass
    return result["text"]
