# --- models/gemini_vision.py ---

import os
from io import BytesIO
import mimetypes
from fastapi import HTTPException
from PIL import Image
import google.generativeai as genai
from app.config import Settings

# Allowed MIME types for OCR
SUPPORTED_IMAGE_TYPES = {"image/png", "image/jpeg", "image/gif", "image/webp"}

# Load environment settings
settings = Settings()

# Configure the Gemini SDK once globally
genai.configure(api_key=settings.GEMINI_API_KEY)

def extract_image_text(path: str) -> str:
    """Extract visible text from an image using Gemini Pro Vision.

    ``path`` must be a filesystem path to the image file. The function will
    validate the path, ensure the MIME type is supported and then send the
    image bytes to Gemini for OCR.
    """
    api_key = settings.GEMINI_API_KEY
    if not api_key or api_key.lower().startswith("dummy"):
        raise HTTPException(status_code=503, detail="GEMINI_API_KEY not configured")

    if not isinstance(path, str) or not os.path.exists(path):
        raise HTTPException(status_code=400, detail=f"File not found: {path}")
    try:
        with open(path, "rb") as f:
            image_bytes = f.read()
    except Exception:
        raise HTTPException(status_code=400, detail="Unsupported image type")

    mime_type = mimetypes.guess_type(path)[0]

    if not image_bytes:
        raise HTTPException(status_code=400, detail="Empty image data")

    if not mime_type:
        try:
            img = Image.open(BytesIO(image_bytes))
            mime_type = Image.MIME.get(img.format)
        except Exception:
            raise HTTPException(status_code=400, detail="Unsupported image type")

    if mime_type not in SUPPORTED_IMAGE_TYPES:
        raise HTTPException(status_code=400, detail="Unsupported image type")

    try:
        img = Image.open(BytesIO(image_bytes))
        model = genai.GenerativeModel("gemini-1.5-pro")
        resp = model.generate_content([
            "Extract any visible text from this image.",
            img,
        ])
        return resp.text
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Gemini request failed: {e}")


def describe_image(path: str) -> str:
    """Describe objects and scenes in the image using Gemini Vision."""
    api_key = settings.GEMINI_API_KEY
    if not api_key:
        raise HTTPException(status_code=503, detail="GEMINI_API_KEY not set")

    try:
        image = Image.open(path)
        model = genai.GenerativeModel("gemini-1.5-pro")
        response = model.generate_content(["Describe this image in detail.", image])
        return response.text
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Exception during image description: {e}")


def summarize_text_gemini(text: str, query: str = "") -> str:
    """Summarize text using Gemini Pro."""
    api_key = settings.GEMINI_API_KEY
    if not api_key:
        raise HTTPException(status_code=503, detail="GEMINI_API_KEY not set")

    try:
        prompt = (
            f"Summarize the following text relevant to the query: '{query}'\n\n{text}"
            if query else
            f"Summarize the following text:\n\n{text}"
        )

        model = genai.GenerativeModel("gemini-1.5-flash")
        response = model.generate_content(prompt)

        return response.text.strip()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Gemini summarization failed: {str(e)}")
