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

# In-memory session tracking for uploaded files
session_store: dict[str, dict] = {}


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

    # ✅ Handle Streamlit (sync) or FastAPI (async)
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
        if extracted and len(extracted.split()) > 5:
            ns = _session_ns("image", session_id)
            ingest_text_to_faiss(extracted, namespace=ns)
            if session_id:
                session_store[session_id] = {"type": "image", "text": extracted}
            os.remove(path)
            return "✅ Image description ingested into FAISS."
        else:
            description = describe_image(path)
            ns = _session_ns("image", session_id)
            ingest_text_to_faiss(description, namespace=ns)
            if session_id:
                session_store[session_id] = {"type": "image", "text": description}
            os.remove(path)
            return "✅ Gemini description ingested into FAISS."

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

    pc_no_match = "no match" in result_pc.lower()
    faiss_no_match = "no faiss" in result_faiss.lower()

    if pc_no_match and faiss_no_match:
        # Full multi‐engine fallback: ArXiv → Semantic Scholar → Web
        return search_agent.handle_query(text)

    return (
        f"Pinecone:\n{result_pc or 'No match found'}"
        f"\n\nFAISS:\n{result_faiss or 'No match found'}"
    )


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

    if not best_answer:
        return "No match found", 0.0

    return best_answer, best_conf


def save_memory(question: str, answer: str, session_id: str | None = None):
    """Persist Q&A pair into a session-scoped FAISS memory namespace."""
    ingest_text_to_faiss(
        f"Q: {question}\nA: {answer}",
        namespace=_session_ns("memory", session_id),
    )
