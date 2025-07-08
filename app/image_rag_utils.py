from models import gemini_vision
from fastapi import HTTPException

def analyze_image_content(image_path: str) -> dict:
    """
    Modular image understanding pipeline:
    1. Try OCR (extract_image_text)
    2. If OCR succeeds and is non-empty, try to summarize (summarize_text_gemini)
    3. If OCR fails or is empty, try describe_image
    4. Return the best available result and which method was used
    """
    ocr_text = None
    summary = None
    description = None
    used = None
    # 1. Try OCR
    try:
        ocr_text = gemini_vision.extract_image_text(image_path)
        if ocr_text and ocr_text.strip():
            used = "ocr"
            # 2. Try summarization
            try:
                summary = gemini_vision.summarize_text_gemini(ocr_text)
                if summary and summary.strip():
                    used = "ocr+summary"
                    return {"caption": summary.strip(), "method": used, "raw_ocr": ocr_text.strip()}
            except Exception:
                pass
            return {"caption": ocr_text.strip(), "method": used}
    except Exception:
        pass
    # 3. Try description
    try:
        description = gemini_vision.describe_image(image_path)
        if description and description.strip():
            used = "describe"
            return {"caption": description.strip(), "method": used}
    except Exception:
        pass
    # 4. Fallback
    return {"caption": "Unable to generate a description for this image.", "method": "none"} 
