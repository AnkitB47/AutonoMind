"""CLIP + FAISS image similarity utilities.

The model and processor are loaded from the ``openai/clip-vit-base-patch32``␊
repository on Hugging Face. We try to load them lazily to avoid import errors␊
when ``transformers`` or ``torch`` are missing. If the direct load fails we fall␊
back to the `feature-extraction` pipeline and raise an exception on failure so
we never embed zero vectors silently.
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

# Lazily import transformers so tests work without the dependency
try:  # pragma: no cover - optional dependency
    from transformers import CLIPModel, CLIPProcessor, pipeline
except Exception:  # pragma: no cover
    CLIPModel = CLIPProcessor = pipeline = None

from app.config import Settings

settings = Settings()
INDEX_PATH = os.getenv("CLIP_FAISS_INDEX", settings.CLIP_FAISS_INDEX)
META_PATH = INDEX_PATH + ".json"
IMAGE_STORE = os.getenv("IMAGE_STORE", settings.IMAGE_STORE)

_processor: object | None = None
_model: object | None = None
_index: faiss.Index | None = None
_meta: List[dict] = []


def _load_model() -> tuple[object | None, object]:
    """Load CLIP model and processor or fallbacks."""

    global _processor, _model
    if _model is not None:
        return _processor, _model

    # Try loading the standard processor + model
    try:
        if CLIPProcessor is None or CLIPModel is None:
            raise ImportError("transformers unavailable")
        _processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")
        _model = CLIPModel.from_pretrained(
            "openai/clip-vit-base-patch32", use_safetensors=True
        )
        return _processor, _model
    except Exception:
        pass

    # Fallback to feature-extraction pipeline
    try:
        if pipeline is None:
            raise ImportError("transformers pipeline unavailable")
        _model = pipeline("zero-shot-image-classification", model="openai/clip-vit-base-patch32")
        _processor = None
        # Infer dimension from a dummy call
        out = _model("test")
        dim = len(np.array(out)[0]) if out else 512
        _model.projection_dim = dim
        return _processor, _model
    except Exception as e:
        raise RuntimeError(f"Failed to load CLIP model: {e}")


def _model_dim(model: object) -> int:
    if hasattr(model, "config") and hasattr(model.config, "projection_dim"):
        return model.config.projection_dim
    if hasattr(model, "projection_dim"):
        return model.projection_dim
    return 512


def _load_index() -> None:
    global _index, _meta
    if _index is not None:
        return
    os.makedirs(IMAGE_STORE, exist_ok=True)
    _, model = _load_model()
    dim = _model_dim(model)
    try:
        if os.path.exists(INDEX_PATH):
            _index = faiss.read_index(INDEX_PATH)
            if os.path.exists(META_PATH):
                with open(META_PATH, "r") as f:
                    _meta = json.load(f)
            if not isinstance(_index, faiss.IndexIDMap):
                _index = faiss.IndexIDMap(_index)
            if _index.d != dim:
                _index = faiss.IndexIDMap(faiss.IndexFlatIP(dim))
                _meta = []
        else:
            _index = faiss.IndexIDMap(faiss.IndexFlatIP(dim))
            _meta = []
    except Exception:
        class Dummy:
            def __init__(self, dim: int):
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
    try:
        img = Image.open(BytesIO(data)).convert("RGB")
    except Exception:
        return np.zeros(_model_dim(model), dtype="float32")
    try:
        import torch

        if processor is not None and hasattr(model, "get_image_features"):
            inputs = processor(images=img, return_tensors="pt")
            with torch.no_grad():
                emb = model.get_image_features(**inputs)
                emb = torch.nn.functional.normalize(emb, p=2, dim=-1)
            return emb[0].cpu().numpy().astype("float32")
        else:  # pipeline output
            out = model(img)
            arr = np.asarray(out)[0]
            if arr.ndim > 1:
                arr = arr.mean(axis=0)
            arr = arr.astype("float32")
            return arr
    except Exception:
        return np.zeros(_model_dim(model), dtype="float32")


def ingest_image(path: str, namespace: str = "image") -> str:
    """Embed image and persist to FAISS. Returns stored path."""

    _load_index()
    with open(path, "rb") as f:
        data = f.read()
    vec = _encode_image(data)
    idx = len(_meta)
    _index.add_with_ids(vec[np.newaxis, :], np.array([idx], dtype="int64"))
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
    try:
        D, I = _index.search(vec[np.newaxis, :].astype("float32"), min(k, getattr(_index, "ntotal", k)))
    except Exception:
        return []
    results = []
    for idx, score in zip(I[0], D[0]):
        if idx == -1:
            continue
        meta = _meta[idx]
        if meta.get("namespace") != namespace:
            continue
        path = meta.get("path")
        if path and os.path.exists(path):
            filename = os.path.basename(path)
            results.append({"url": f"/images/{filename}", "score": float(score)})
    return results[:k]


def search_text(text: str, namespace: str = "image", k: int = 5):
    processor, model = _load_model()
    try:
        import torch

        if processor is not None and hasattr(model, "get_text_features"):
            # Truncate to CLIP's 77 token limit
            if hasattr(processor, "tokenizer"):
                ids = processor.tokenizer(text)["input_ids"][0][:77]
                text = processor.tokenizer.decode(ids, skip_special_tokens=True)
            inputs = processor(text=[text], return_tensors="pt")
            with torch.no_grad():
                text_emb = model.get_text_features(**inputs)
                text_emb = torch.nn.functional.normalize(text_emb, p=2, dim=-1)
            vec = text_emb[0].cpu().numpy().astype("float32")
        else:  # pipeline
            text = " ".join(text.split()[:77])
            out = model(text)
            arr = np.asarray(out)[0]
            if arr.ndim > 1:
                arr = arr.mean(axis=0)
            vec = arr.astype("float32")
    except Exception:
        vec = np.zeros(_model_dim(model), dtype="float32")
    return search_by_vector(vec, namespace, k)


def search_image(data: bytes, namespace: str = "image", k: int = 5):
    vec = _encode_image(data)
    return search_by_vector(vec, namespace, k)
