from __future__ import annotations

import os
import json
from typing import Tuple, List, Optional

import numpy as np
import faiss
from langchain_openai import OpenAIEmbeddings
from app.config import Settings

settings = Settings()
FAISS_INDEX_PATH = settings.FAISS_INDEX_PATH
META_PATH = FAISS_INDEX_PATH + ".json"
embedding_model = OpenAIEmbeddings(api_key=settings.OPENAI_API_KEY)

_index: faiss.IndexIDMap | None = None
_meta: List[dict] = []


def _embed_query(text: str) -> List[float]:
    func = getattr(embedding_model, "embed_query", None)
    if callable(func):
        return func(text)
    return [0.0]


def _embed_docs(texts: List[str]) -> List[List[float]]:
    func = getattr(embedding_model, "embed_documents", None)
    if callable(func):
        return func(texts)
    dim = len(_embed_query("x"))
    return [[0.0] * dim for _ in texts]


def _emb_dim() -> int:
    return len(_embed_query("dim"))


def _load() -> None:
    global _index, _meta
    if _index is not None:
        return
    dirpath = os.path.dirname(FAISS_INDEX_PATH)
    if dirpath:
        os.makedirs(dirpath, exist_ok=True)
    dim = _emb_dim()
    if os.path.exists(FAISS_INDEX_PATH):
        _index = faiss.read_index(FAISS_INDEX_PATH)
        if not isinstance(_index, faiss.IndexIDMap):
            _index = faiss.IndexIDMap(_index)
        if _index.d != dim:
            _index = faiss.IndexIDMap(faiss.IndexFlatIP(dim))
            _meta = []
        if os.path.exists(META_PATH):
            with open(META_PATH, "r") as f:
                _meta = json.load(f)
    else:
        _index = faiss.IndexIDMap(faiss.IndexFlatIP(dim))
        _meta = []


def _save() -> None:
    if _index is None:
        return
    faiss.write_index(_index, FAISS_INDEX_PATH)
    with open(META_PATH, "w") as f:
        json.dump(_meta, f)


def add_texts(texts: List[str], namespace: Optional[str] = None) -> None:
    if not texts:
        return
    _load()
    vecs = _embed_docs(texts)
    vecs = np.array(vecs, dtype="float32")
    start = len(_meta)
    ids = np.arange(start, start + len(texts), dtype="int64")
    _index.add_with_ids(vecs, ids)
    for t in texts:
        _meta.append({"text": t, "source": namespace or "generic"})
    _save()


def _search_vec(vec: np.ndarray, namespace: Optional[str], k: int = 50) -> Tuple[Optional[str], float]:
    _load()
    if _index.ntotal == 0:
        return None, 0.0
    # search a larger window then filter by namespace to avoid missing hits
    D, I = _index.search(vec[np.newaxis, :], min(k, _index.ntotal))
    best_text = None
    best_score = -1.0
    for idx, score in zip(I[0], D[0]):
        if idx == -1:
            continue
        meta = _meta[idx]
        if namespace and meta.get("source") != namespace:
            continue
        if score > best_score:
            best_text = meta.get("text", "")
            best_score = float(score)
    if best_text is None:
        return None, 0.0
    return best_text, best_score


def search_faiss(query: str, namespace: Optional[str] = None) -> str:
    vec = np.array(_embed_query(query), dtype="float32")
    text, _ = _search_vec(vec, namespace, k=50)
    return text.strip() if text else "No FAISS match found"


def search_faiss_with_score(query: str, namespace: Optional[str] = None) -> Tuple[Optional[str], float]:
    vec = np.array(_embed_query(query), dtype="float32")
    text, score = _search_vec(vec, namespace, k=50)
    return (text.strip(), score) if text else (None, 0.0)
