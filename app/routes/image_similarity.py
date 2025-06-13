"""Image similarity search endpoint."""
from fastapi import APIRouter, UploadFile, File, HTTPException
from pydantic import BaseModel
from agents.clip_faiss import search_text, search_image

router = APIRouter(prefix="/search", tags=["search"])

class ImageQuery(BaseModel):
    text: str | None = None
    session_id: str | None = None


@router.post("/image-similarity")
async def image_similarity(
    query: ImageQuery = None,
    file: UploadFile | None = File(None),
) -> dict:
    if file is None and (query is None or not query.text):
        raise HTTPException(status_code=400, detail="text or file required")
    namespace = f"image_{query.session_id}" if query and query.session_id else "image"
    if file is not None:
        data = await file.read()
        results = search_image(data, namespace=namespace)
    else:
        results = search_text(query.text, namespace=namespace)
    return {"results": results}
