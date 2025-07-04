# --- agents/rag_agent.py ---
"""RAG helpers with per-session storage."""

from __future__ import annotations

from collections import defaultdict
from uuid import uuid4
import inspect
import os
import tempfile
import time

from cachetools import TTLCache
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from agents import search_agent, translate_agent
import base64
from app.config import Settings

settings = Settings()

from models.gemini_vision import extract_image_text, summarize_text_gemini
from agents.clip_faiss import (
    ingest_image as ingest_clip_image,
    search_text as search_images,
    search_image,
)
from vectorstore.faiss_embed_and_store import ingest_text_to_faiss
from vectorstore.faiss_store import search_faiss, search_faiss_with_score
from vectorstore.pinecone_store import (
    ingest_pdf_text_to_pinecone as ingest_pdf_to_pinecone,
    search_pinecone,
    search_pinecone_with_score,
)

__all__ = [
    "process_file",
    "query_pdf_image",
    "query_with_confidence",
    "save_memory",
    "load_memory",
    "search_clip_image",
    "rewrite_answer",
    "handle_query",
]

# Session caches
DEFAULT_SESSION_TTL = 3600  # 1 hour
session_store: TTLCache[str, dict] = TTLCache(maxsize=128, ttl=DEFAULT_SESSION_TTL)
memory_cache: dict[str, list[str]] = defaultdict(list)


def _session_ns(base: str, sid: str | None) -> str:
    return f"{base}_{sid}" if sid else base


def _clean(text: str) -> str:
    return text.replace("<pad>", "").replace("<eos>", "").replace("<EOS>", "").strip()


async def process_file(file, session_id: str | None = None) -> tuple[str, str]:
    """Ingest a PDF or image and return a session id."""
    sid = session_id or str(uuid4())
    name = getattr(file, "filename", getattr(file, "name", "upload"))
    suffix = name.split(".")[-1].lower()
    read = file.read
    data = await read() if inspect.iscoroutinefunction(read) else read()
    with tempfile.NamedTemporaryFile(delete=False, suffix=f".{suffix}") as tmp:
        tmp.write(data)
        path = tmp.name
    success = False

    if suffix == "pdf":
        loader = PyPDFLoader(path)
        docs = loader.load()
        splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=0)
        chunks: list[str] = []
        for d in docs:
            chunks.extend(splitter.split_text(d.page_content))
        text = "\n".join(chunks)
        for chunk in chunks:
            ingest_pdf_to_pinecone(chunk, namespace=_session_ns("pdf", sid))
            ingest_text_to_faiss(chunk, namespace=_session_ns("pdf", sid))
        msg = "✅ PDF ingested"
        meta = {"type": "pdf", "text": text, "timestamp": time.time()}
        success = True
    elif suffix in {"png", "jpg", "jpeg", "gif", "webp"}:
        text = extract_image_text(path)
        ingest_text_to_faiss(text, namespace=_session_ns("image", sid))
        stored_path = ingest_clip_image(path, namespace=_session_ns("image", sid))
        msg = "✅ Image ingested"
        meta = {"type": "image", "text": text, "path": stored_path, "timestamp": time.time()}
        success = True
    else:
        if os.path.exists(path):
            os.remove(path)
        return "❌ Unsupported file format", sid

    if success and os.path.exists(path):
        os.remove(path)
    session_store[sid] = meta
    return msg, sid


def _search_all(text: str, sid: str | None, include_memory: bool) -> tuple[str, float, str | None]:
    def _norm(x: float) -> float:
        return max(0.0, min(1.0, x))

    ranked: list[tuple[str, float, str]] = []

    # gather pdf results from both stores
    for func in (search_pinecone_with_score, search_faiss_with_score):
        ans, raw_conf = func(text, namespace=_session_ns("pdf", sid), k=3)
        if ans:
            ranked.append((_clean(ans), _norm(raw_conf), "pdf"))

    # image and optional memory namespaces via FAISS
    for ns in ["image"] + (["memory"] if include_memory else []):
        ans, raw_conf = search_faiss_with_score(text, namespace=_session_ns(ns, sid), k=3)
        if ans:
            ranked.append((_clean(ans), _norm(raw_conf), ns))

    # CLIP fallback always considered
    matches = search_images(text, namespace=_session_ns("image", sid), k=1)
    if matches:
        match = matches[0]
        ranked.append((match["url"], _norm(match.get("score", 0.0)), "image"))

    if not ranked:
        return "No match found", 0.0, None

    ranked.sort(key=lambda x: x[1], reverse=True)
    best_ans, best_conf, best_src = ranked[0]

    if best_src == "pdf":
        excerpts = [text for text, _, src in ranked if src == "pdf"][:3]
        best_ans = "\n".join(excerpts)

    return best_ans, best_conf, best_src


def query_pdf_image(text: str, session_id: str | None = None) -> tuple[str, float, str | None]:
    """Search PDFs and images for ``text`` within ``session_id``."""
    if not session_id:
        raise ValueError("session_id required")
    return _search_all(text, session_id, include_memory=False)


def query_with_confidence(text: str, session_id: str | None = None) -> tuple[str, float, str | None]:
    """Search PDFs, images and memory for ``text``."""
    if not session_id:
        raise ValueError("session_id required")
    return _search_all(text, session_id, include_memory=True)


def save_memory(question: str, answer: str, session_id: str | None = None) -> None:
    """Append Q&A pair to the FAISS memory namespace."""
    entry = f"Q: {question}\nA: {answer}"
    ingest_text_to_faiss(entry, namespace=_session_ns("memory", session_id))
    if session_id:
        memory_cache[session_id].append(entry)


def search_clip_image(data: bytes, session_id: str | None = None) -> tuple[str, float]:
    """Return best CLIP match for ``data`` within ``session_id``."""
    matches = search_image(data, namespace=_session_ns("image", session_id))
    if not matches:
        return "", 0.0
    best = matches[0]
    score = max(0.0, min(1.0, float(best.get("score", 0.0))))
    return best.get("url", ""), score


def load_memory(session_id: str | None, limit: int = 5) -> list[str]:
    if not session_id:
        return []
    return memory_cache.get(session_id, [])[-limit:]


def rewrite_answer(excerpts: str, question: str, lang: str) -> str:
    """Rewrite raw document excerpts into a concise answer."""
    prompt = (
        f"You are a friendly assistant. The user asked: '{question}'.\n"
        f"Here are the most relevant excerpts:\n{excerpts}\n"
        f"Please answer in {lang} in a concise, conversational style."
    )
    try:
        return summarize_text_gemini(excerpts, question)
    except Exception:
        try:
            from langchain_openai import ChatOpenAI
            llm = ChatOpenAI(temperature=0.2)
            return llm.predict(prompt)
        except Exception as e:
            return f"⚠️ LLM failed: {e}\n\n{excerpts}"


def handle_text(text: str, namespace: str | None = None, session_id: str | None = None) -> str:
    """Return search results or fallback web summary."""
    pc_result = "No match found"
    if namespace in (None, "pdf"):
        pc_result = search_pinecone(text, namespace=_session_ns("pdf", session_id))
    faiss_result = search_faiss(text, namespace=_session_ns(namespace, session_id) if namespace else None)
    clip_result = "No image match found"
    if namespace == "image":
        matches = search_images(text, namespace=_session_ns("image", session_id))
        if matches:
            clip_result = matches[0]["url"]

    pc_result = _clean(pc_result)
    faiss_result = _clean(faiss_result)
    clip_result = _clean(clip_result)

    if (
        "no match" in pc_result.lower()
        and "no faiss" in faiss_result.lower()
        and (namespace != "image" or "no image" in clip_result.lower())
    ):
        if namespace:
            return "No match found"
        return search_agent.handle_query(text)

    parts = [f"Pinecone:\n{pc_result or 'No match found'}", f"FAISS:\n{faiss_result or 'No match found'}"]
    if namespace == "image":
        parts.append(f"CLIP:\n{clip_result or 'No match found'}")
    return "\n\n".join(parts)


def handle_query(mode: str, content: str, session_id: str, lang: str = "en") -> tuple[str, float, str | None]:
    """Unified RAG entry point for different input modes."""
    if mode == "search":
        text = search_agent.handle_query(content)
        return translate_agent.translate_response(text, lang), 1.0, "web"

    if mode == "image":
        data = base64.b64decode(content)
        with tempfile.NamedTemporaryFile(delete=False, suffix=".img") as tmp:
            tmp.write(data)
            tmp_path = tmp.name
        try:
            content = extract_image_text(tmp_path)
        finally:
            os.remove(tmp_path)

    text = content if mode != "voice" else content

    raw = session_store.get(session_id, {}).get("text", "")
    combined = f"{raw}\n\nUser question: {text}" if raw else text
    try:
        ans, conf, src = query_pdf_image(combined, session_id=session_id)
    except Exception:
        ans, conf, src = "", 0.0, None

    if src == "image":
        save_memory(text, ans, session_id=session_id)
        return translate_agent.translate_response(ans, lang), conf, src

    if conf < settings.MIN_RAG_CONFIDENCE:
        ans = search_agent.handle_query(text)
        conf = 0.0
        src = "web"

    save_memory(text, ans, session_id=session_id)
    translated = translate_agent.translate_response(ans, lang)
    return translated, conf, src
