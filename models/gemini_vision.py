# --- models/gemini_vision.py ---

import os
import base64
import requests
from PIL import Image
from app.config import Settings


try:
    from google.generativeai import GenerativeModel
except ImportError:
    GenerativeModel = None


# Load environment settings
settings = Settings()


def extract_image_text(path: str) -> str:
    """
    Extracts visible text from an image using Gemini Pro Vision API via HTTP.
    Fallback method for OCR-like use cases.
    """
    api_key = settings.GEMINI_API_KEY
    if not api_key:
        return "Error: GEMINI_API_KEY not set."

    if not os.path.exists(path):
        return f"Error: File not found - {path}"

    with open(path, "rb") as f:
        encoded_image = base64.b64encode(f.read()).decode("utf-8")

    endpoint = "https://generativelanguage.googleapis.com/v1beta/models/gemini-pro-vision:generateContent"
    headers = {"Content-Type": "application/json"}
    payload = {
        "contents": [
            {
                "parts": [
                    {"text": "Extract any visible text from this image."},
                    {
                        "inlineData": {
                            "mimeType": "image/png",
                            "data": encoded_image
                        }
                    }
                ]
            }
        ]
    }

    try:
        response = requests.post(
            f"{endpoint}?key={api_key}", json=payload, headers=headers
        )
        if response.status_code == 200:
            data = response.json()
            return data["candidates"][0]["content"]["parts"][0]["text"]
        else:
            return f"Error: Gemini API {response.status_code} - {response.text}"
    except Exception as e:
        return f"Exception during image OCR: {e}"


def describe_image(path: str) -> str:
    """
    Uses the Gemini SDK to describe the content of the image, e.g., objects, scene.
    Requires the google-generativeai library.
    """
    if not GenerativeModel:
        return "Error: google-generativeai not installed."

    api_key = settings.GEMINI_API_KEY
    if not api_key:
        return "Error: GEMINI_API_KEY not set."

    try:
        image = Image.open(path)
        model = GenerativeModel("gemini-pro-vision", api_key=api_key)
        response = model.generate_content(["Describe this image in detail.", image])
        return response.text
    except Exception as e:
        return f"Exception during image description: {e}"
