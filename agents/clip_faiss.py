"""CLIP + FAISS image similarity utilities."""
from __future__ import annotations

import os
import json
import uuid
import shutil
from typing import List, Tuple

import numpy as np
from PIL import Image
from sentence_transformers import SentenceTransformer
import faiss

INDEX_PATH = os.getenv("CLIP_FAISS_INDEX", "clip_faiss.index")
META_PATH = INDEX_PATH + ".json"
IMAGE_STORE = os.getenv("IMAGE_STORE", os.path.join("vectorstore", "image_store"))

_model: SentenceTransformer | None = None
_index: faiss.Index | None = None
_meta: List[dict] = []


def _load_model() -> SentenceTransformer:
    global _model
    if _model is None:
        _model = SentenceTransformer("clip-ViT-B-32")
    return _model


def _load_index() -> None:
    global _index, _meta
    if _index is not None:
        return
    os.makedirs(IMAGE_STORE, exist_ok=True)
    dim = _load_model().get_sentence_embedding_dimension()
    if os.path.exists(INDEX_PATH):
        _index = faiss.read_index(INDEX_PATH)
        if os.path.exists(META_PATH):
            with open(META_PATH, "r") as f:
                _meta = json.load(f)
    else:
        _index = faiss.IndexFlatIP(dim)
        _meta = []


def _save_index() -> None:
    if _index is None:
        return
    faiss.write_index(_index, INDEX_PATH)
    with open(META_PATH, "w") as f:
        json.dump(_meta, f)


def _encode_image(data: bytes) -> np.ndarray:
    model = _load_model()
    img = Image.open(BytesIO(data)).convert("RGB")
    emb = model.encode(img, normalize_embeddings=True)
    return np.asarray(emb, dtype="float32")


from io import BytesIO


def ingest_image(path: str, namespace: str = "image") -> str:
    """Embed image and persist to FAISS. Returns stored path."""
    _load_index()
    with open(path, "rb") as f:
        data = f.read()
    vec = _encode_image(data)
    _index.add(vec[np.newaxis, :])
    ext = os.path.splitext(path)[1]
    dest = os.path.join(IMAGE_STORE, f"{uuid.uuid4().hex}{ext}")
    shutil.copy2(path, dest)
    _meta.append({"path": dest, "namespace": namespace})
    _save_index()
    return dest


def search_by_vector(vec: np.ndarray, namespace: str, k: int = 5) -> List[Tuple[str, float]]:
    _load_index()
    if _index.ntotal == 0:
        return []
    D, I = _index.search(vec[np.newaxis, :].astype("float32"), min(k, _index.ntotal))
    results = []
    for idx, score in zip(I[0], D[0]):
        if idx == -1:
            continue
        meta = _meta[idx]
        if meta.get("namespace") != namespace:
            continue
        path = meta.get("path")
        if path and os.path.exists(path):
            results.append({"url": path, "score": float(score)})
    return results


def search_text(text: str, namespace: str = "image", k: int = 5):
    model = _load_model()
    vec = model.encode(text, normalize_embeddings=True)
    vec = np.asarray(vec, dtype="float32")
    return search_by_vector(vec, namespace, k)


def search_image(data: bytes, namespace: str = "image", k: int = 5):
    vec = _encode_image(data)
    return search_by_vector(vec, namespace, k)
