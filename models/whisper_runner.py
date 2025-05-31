# --- models/whisper_runner.py ---
import whisper
model = whisper.load_model("base")


def transcribe_audio(audio_bytes):
    import tempfile
    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
        tmp.write(audio_bytes)
        path = tmp.name
    result = model.transcribe(path)
    return result["text"]
