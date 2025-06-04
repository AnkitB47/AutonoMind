# --- models/gemini_vision.py ---

import os
import base64
import requests
from io import BytesIO
from PIL import Image
import mimetypes
from app.config import Settings
import google.generativeai as genai

# Load environment settings
settings = Settings()

# Configure the Gemini SDK once globally
genai.configure(api_key=settings.GEMINI_API_KEY)


def extract_image_text(data: bytes | str) -> str:
    """Extract visible text from an image using Gemini Pro Vision."""
    api_key = settings.GEMINI_API_KEY
    if not api_key:
        return "Error: GEMINI_API_KEY not set."

    if isinstance(data, str):
        if not os.path.exists(data):
            return f"Error: File not found - {data}"
        with open(data, "rb") as f:
            image_bytes = f.read()
        mime_type = mimetypes.guess_type(data)[0]
    else:
        image_bytes = data
        mime_type = None

    if not mime_type:
        try:
            img = Image.open(BytesIO(image_bytes))
            mime_type = Image.MIME.get(img.format)
        except Exception:
            mime_type = "application/octet-stream"

    encoded_image = base64.b64encode(image_bytes).decode("utf-8")

    endpoint = (
        "https://generativelanguage.googleapis.com/v1/models/"
        "gemini-1.5-pro:generateContent"
    )
    headers = {"Content-Type": "application/json"}
    payload = {
        "contents": [
            {
                "parts": [
                    {"text": "Extract any visible text from this image."},
                    {
                        "inlineData": {
                            "mimeType": mime_type,
                            "data": encoded_image
                        }
                    }
                ]
            }
        ]
    }

    try:
        response = requests.post(f"{endpoint}?key={settings.GEMINI_API_KEY}", json=payload, headers=headers)
        if response.status_code == 200:
            data = response.json()
            return data["candidates"][0]["content"]["parts"][0]["text"]
        else:
            return f"❌ Gemini API {response.status_code} - {response.text}"
    except Exception as e:
        return f"❌ Exception during OCR: {str(e)}"


def describe_image(path: str) -> str:
    """Describe objects and scenes in the image using Gemini Vision."""
    api_key = settings.GEMINI_API_KEY
    if not api_key:
        return "Error: GEMINI_API_KEY not set."

    try:
        image = Image.open(path)
        model = genai.GenerativeModel("gemini-1.5-pro")
        response = model.generate_content(["Describe this image in detail.", image])
        return response.text
    except Exception as e:
        return f"Exception during image description: {e}"


def summarize_text_gemini(text: str, query: str = "") -> str:
    """Summarize text using Gemini Pro."""
    api_key = settings.GEMINI_API_KEY
    if not api_key:
        return "❌ GEMINI_API_KEY not set."

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
        return f"❌ Gemini summarization failed: {str(e)}"

