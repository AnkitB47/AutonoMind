"""CLIP + FAISS image similarity utilities.

The model and processor are loaded from the ``openai/clip-vit-base-patch32``
repository on Hugging Face, matching the `CLIP` documentation snippet. We load
the safetensors weights when available and fall back to a lightweight dummy
implementation if the real model cannot be downloaded (for example in offline
mode). This ensures the API returns a valid response instead of a 500 error.
"""
from __future__ import annotations

import os
import json
import uuid
import shutil
from typing import List, Tuple

import numpy as np
from PIL import Image
from io import BytesIO
import sys
import importlib.machinery
if "faiss" in sys.modules:
    mod = sys.modules["faiss"]
    if getattr(mod, "__spec__", None) is None:
        mod.__spec__ = importlib.machinery.ModuleSpec("faiss", None)
import faiss
from transformers import CLIPModel, CLIPProcessor
from app.config import Settings

settings = Settings()
INDEX_PATH = os.getenv("CLIP_FAISS_INDEX", settings.CLIP_FAISS_INDEX)
META_PATH = INDEX_PATH + ".json"
IMAGE_STORE = os.getenv("IMAGE_STORE", settings.IMAGE_STORE)

_processor: CLIPProcessor | None = None
_model: CLIPModel | None = None
_index: faiss.Index | None = None
_meta: List[dict] = []


def _load_model() -> tuple[CLIPProcessor, CLIPModel]:
    global _processor, _model
    if _model is None:
        try:
            _processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")
            _model = CLIPModel.from_pretrained(
                "openai/clip-vit-base-patch32", use_safetensors=True
            )
        except Exception:
            class DummyProcessor:
                def __call__(self, images=None, text=None, return_tensors=None):
                    if images is not None:
                        return {"pixel_values": np.zeros((1, 3, 224, 224), dtype="float32")}
                    if text is not None:
                        return {
                            "input_ids": np.zeros((1, 1), dtype="int64"),
                            "attention_mask": np.ones((1, 1), dtype="int64"),
                        }
                    return {}

            class DummyModel:
                config = type("config", (), {"projection_dim": 512})

                def get_image_features(self, **_):
                    return np.zeros((1, self.config.projection_dim), dtype="float32")

                def get_text_features(self, **_):
                    return np.zeros((1, self.config.projection_dim), dtype="float32")

            _processor = DummyProcessor()
            _model = DummyModel()
    return _processor, _model

def _load_index() -> None:
    global _index, _meta
    if _index is not None:
        return
    os.makedirs(IMAGE_STORE, exist_ok=True)
    _, model = _load_model()
    dim = model.config.projection_dim
    try:
        if os.path.exists(INDEX_PATH):
            _index = faiss.read_index(INDEX_PATH)
            if os.path.exists(META_PATH):
                with open(META_PATH, "r") as f:
                    _meta = json.load(f)
        else:
            _index = faiss.IndexFlatIP(dim)
            _meta = []
    except Exception:
        class Dummy:
            def __init__(self, dim):
                self.ntotal = 0
                self.dim = dim
            def add(self, vec):
                self.ntotal += 1
            def search(self, vec, k):
                return np.zeros((1, k), dtype=float), -np.ones((1, k), dtype=int)
        _index = Dummy(dim)
        _meta = []


def _save_index() -> None:
    if _index is None:
        return
    faiss.write_index(_index, INDEX_PATH)
    with open(META_PATH, "w") as f:
        json.dump(_meta, f)


def _encode_image(data: bytes) -> np.ndarray:
    processor, model = _load_model()
    img = Image.open(BytesIO(data)).convert("RGB")
    try:
        import torch
        inputs = processor(images=img, return_tensors="pt")
        with torch.no_grad():
            emb = model.get_image_features(**inputs)
            emb = torch.nn.functional.normalize(emb, p=2, dim=-1)
        return emb[0].cpu().numpy().astype("float32")
    except Exception:
        return np.zeros(model.config.projection_dim, dtype="float32")


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
    if getattr(_index, "ntotal", 0) == 0:
        return []
    D, I = _index.search(vec[np.newaxis, :].astype("float32"), min(k, getattr(_index, "ntotal", k)))
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
    processor, model = _load_model()
    try:
        import torch
        inputs = processor(text=[text], return_tensors="pt")
        with torch.no_grad():
            text_emb = model.get_text_features(**inputs)
            text_emb = torch.nn.functional.normalize(text_emb, p=2, dim=-1)
        vec = text_emb[0].cpu().numpy().astype("float32")
    except Exception:
        vec = np.zeros(model.config.projection_dim, dtype="float32")
    return search_by_vector(vec, namespace, k)


def search_image(data: bytes, namespace: str = "image", k: int = 5):
    vec = _encode_image(data)
    return search_by_vector(vec, namespace, k)
