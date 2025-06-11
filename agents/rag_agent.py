# --- agents/rag_agent.py ---
from vectorstore.pinecone_store import (
    search_pinecone,
    search_pinecone_with_score,
    ingest_pdf_text_to_pinecone as ingest_pdf_to_pinecone,
)
from vectorstore.faiss_store import (
    search_faiss,
    search_faiss_with_score,
)
from agents import search_agent
from vectorstore.faiss_embed_and_store import ingest_text_to_faiss
from vectorstore.clip_store import ingest_image as ingest_clip_image, search_images
from cachetools import TTLCache

# In-memory session tracking for uploaded files
# Entries expire ``DEFAULT_SESSION_TTL`` seconds after creation.
DEFAULT_SESSION_TTL = 3600  # 1 hour
session_store: TTLCache[str, dict] = TTLCache(maxsize=128, ttl=DEFAULT_SESSION_TTL)


def _session_ns(base: str, session_id: str | None) -> str:
    """Helper to build a namespace string scoped by ``session_id``."""
    return f"{base}_{session_id}" if session_id else base

from langchain_community.document_loaders import PyPDFLoader
from models.gemini_vision import extract_image_text, describe_image
import tempfile
import inspect
import os


async def process_file(file, session_id: str | None = None):
    name = getattr(file, "filename", None) or getattr(file, "name", "unknown.unknown")
    suffix = name.split(".")[-1].lower()

    # Handle both sync (file-like) and async uploads
    read_method = file.read
    data = (
        await read_method()
        if inspect.iscoroutinefunction(read_method)
        else read_method()
    )

    with tempfile.NamedTemporaryFile(delete=False, suffix=f".{suffix}") as tmp:
        tmp.write(data)
        path = tmp.name

    if suffix == "pdf":
        loader = PyPDFLoader(path)
        docs = loader.load()
        text = "\n".join(page.page_content for page in docs)
        ns = _session_ns("pdf", session_id)
        ingest_pdf_to_pinecone(text, namespace=ns)
        ingest_text_to_faiss(text, namespace=ns)
        if session_id:
            session_store[session_id] = {"type": "pdf", "text": text}
        os.remove(path)
        return "✅ PDF ingested into Pinecone & FAISS."

    elif suffix in ["jpg", "jpeg", "png"]:
        extracted = extract_image_text(path)
        ns = _session_ns("image", session_id)
        if extracted and len(extracted.split()) > 5:
            ingest_text_to_faiss(extracted, namespace=ns)
            ingest_clip_image(path, namespace=ns)
            if session_id:
                session_store[session_id] = {"type": "image", "text": extracted}
            os.remove(path)
            return "✅ Image description ingested into FAISS & CLIP."
        else:
            description = describe_image(path)
            ingest_text_to_faiss(description, namespace=ns)
            ingest_clip_image(path, namespace=ns)
            if session_id:
                session_store[session_id] = {"type": "image", "text": description}
            os.remove(path)
            return "✅ Gemini description ingested into FAISS & CLIP."

    return "❌ Unsupported file format."


def handle_text(
    text: str,
    namespace: str | None = None,
    session_id: str | None = None,
):
    """Search uploaded content via FAISS/Pinecone.

    The optional ``namespace`` argument limits FAISS results to a specific
    namespace (e.g. ``"image"`` or ``"pdf"``). Pinecone is only queried when the
    namespace is ``None`` or ``"pdf"`` since it currently stores PDF data only.
    """

    result_pc = "No match found"
    if namespace in (None, "pdf"):
        ns = _session_ns("pdf", session_id)
        result_pc = search_pinecone(text, namespace=ns)
        if "no match" in result_pc.lower() and session_id:
            result_pc = search_pinecone(text, namespace="pdf")

    result_faiss = search_faiss(text, namespace=_session_ns(namespace, session_id) if namespace else None)
    if "no faiss" in result_faiss.lower() and session_id:
        result_faiss = search_faiss(text, namespace=namespace)

    result_clip = "No image match found"
    if namespace == "image":
        result_clip = search_images(text, namespace=_session_ns("image", session_id))

    def _clean(text: str) -> str:
        return text.replace("<pad>", "").replace("<eos>", "").replace("<EOS>", "").strip()

    result_pc = _clean(result_pc)
    result_faiss = _clean(result_faiss)
    result_clip = _clean(result_clip)

    pc_no_match = "no match" in result_pc.lower()
    faiss_no_match = "no faiss" in result_faiss.lower()
    clip_no_match = "no image" in result_clip.lower()

    if pc_no_match and faiss_no_match and (namespace != "image" or clip_no_match):
        if namespace:
            return "No match found"
        # Full multi‐engine fallback: ArXiv → Semantic Scholar → Web
        return search_agent.handle_query(text)

    parts = [
        f"Pinecone:\n{result_pc or 'No match found'}",
        f"FAISS:\n{result_faiss or 'No match found'}",
    ]
    if namespace == "image":
        parts.append(f"CLIP:\n{result_clip or 'No match found'}")
    return "\n\n".join(parts)


def query_with_confidence(text: str, session_id: str | None = None):
    """Return best RAG answer and confidence across all namespaces."""
    best_answer = None
    best_conf = 0.0

    pc_ns = _session_ns("pdf", session_id)
    pc_ans, pc_conf = search_pinecone_with_score(text, namespace=pc_ns)
    if pc_conf == 0.0 and session_id:
        pc_ans, pc_conf = search_pinecone_with_score(text, namespace="pdf")
    if pc_conf > best_conf:
        best_answer, best_conf = pc_ans, pc_conf

    for ns in ["pdf", "image", "memory"]:
        ans, conf = search_faiss_with_score(text, namespace=_session_ns(ns, session_id))
        if conf == 0.0 and session_id:
            ans, conf = search_faiss_with_score(text, namespace=ns)
        if conf > best_conf:
            best_answer, best_conf = ans, conf

    clip_ans = search_images(text, namespace=_session_ns("image", session_id))
    if "no image" not in clip_ans.lower() and best_conf < 0.5:
        best_answer, best_conf = clip_ans, 0.5

    if not best_answer:
        return "No match found", 0.0

    return best_answer, best_conf


def save_memory(question: str, answer: str, session_id: str | None = None):
    """Persist Q&A pair into a session-scoped FAISS memory namespace."""
    ingest_text_to_faiss(
        f"Q: {question}\nA: {answer}",
        namespace=_session_ns("memory", session_id),
    )
