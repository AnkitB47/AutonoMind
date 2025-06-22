"""Image similarity search endpoint."""
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from agents.clip_faiss import search_text, search_image

router = APIRouter(prefix="/search", tags=["search"])


@router.post("/image")
async def image_search(
    text: str | None = Form(None),
    file: UploadFile | None = File(None),
    session_id: str | None = Form(None),
) -> dict:
    try:
        if file is None and not text:
            raise HTTPException(status_code=400, detail="text or file required")
        if not session_id:
            raise HTTPException(status_code=400, detail="session_id required")
        namespace = f"image_{session_id}" if session_id else "image"
        if file is not None:
            data = await file.read()
            results = search_image(data, namespace=namespace)
        else:
            results = search_text(text, namespace=namespace)
        return {"results": results}
    except HTTPException as exc:
        raise exc
    except Exception as e:  # pragma: no cover - defensive
        return {"error": str(e)}
