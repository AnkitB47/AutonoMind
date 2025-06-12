import os
import json
import numpy as np
from typing import List, Tuple
from transformers import CLIPProcessor, CLIPModel

# Lazy imports to avoid heavy dependencies unless needed
_processor = None
_model = None
_index = None
_meta: List[dict] = []

# Configurable path for FAISS index and metadata
CLIP_INDEX_PATH = os.getenv("CLIP_INDEX_PATH", "clip.index")
META_PATH = CLIP_INDEX_PATH + ".json"


def _load_model():
    global _processor, _model
    if _model is None:
        _processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")
        # Use the safer `safetensors` weights to avoid the torch.load vulnerability
        # check present in older PyTorch versions.
        _model = CLIPModel.from_pretrained(
            "openai/clip-vit-base-patch32", use_safetensors=True
        )
    return _processor, _model


def _load_index():
    global _index, _meta
    if _index is not None:
        return
    try:
        import faiss
    except Exception:
        raise ImportError("faiss is required for CLIP index")
    if os.path.exists(CLIP_INDEX_PATH):
        _index = faiss.read_index(CLIP_INDEX_PATH)
        if os.path.exists(META_PATH):
            with open(META_PATH, "r") as f:
                _meta = json.load(f)
    else:
        _processor, _model = _load_model()
        dim = _model.config.projection_dim
        _index = faiss.IndexFlatIP(dim)
        _meta = []


def _save_index():
    import faiss
    if _index is None:
        return
    faiss.write_index(_index, CLIP_INDEX_PATH)
    with open(META_PATH, "w") as f:
        json.dump(_meta, f)


def ingest_image(path: str, namespace: str = "image"):
    """Embed image via CLIP and store in FAISS."""
    _load_index()
    processor, model = _load_model()
    from PIL import Image
    import torch

    image = Image.open(path).convert("RGB")
    inputs = processor(images=image, return_tensors="pt")
    with torch.no_grad():
        emb = model.get_image_features(**inputs)
        emb = torch.nn.functional.normalize(emb, p=2, dim=-1)
    vec = emb[0].cpu().numpy().astype("float32")
    _index.add(np.expand_dims(vec, 0))
    _meta.append({"source": namespace, "path": path})
    _save_index()


def search_images(query: str, namespace: str = "image", k: int = 1) -> str:
    """Search CLIP image embeddings using a text query."""
    _load_index()
    if _index.ntotal == 0:
        return "No image match found"
    processor, model = _load_model()
    import torch
    inputs = processor(text=[query], return_tensors="pt")
    with torch.no_grad():
        text_emb = model.get_text_features(**inputs)
        text_emb = torch.nn.functional.normalize(text_emb, p=2, dim=-1)
    qvec = text_emb[0].cpu().numpy().astype("float32")
    import numpy as np
    D, I = _index.search(np.expand_dims(qvec, 0), min(k, _index.ntotal))
    for idx in I[0]:
        meta = _meta[idx]
        if meta.get("source") == namespace:
            return meta.get("path", "matched image")
    return "No image match found"
