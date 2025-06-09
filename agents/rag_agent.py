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
from langchain_community.document_loaders import PyPDFLoader
from models.gemini_vision import extract_image_text, describe_image
import tempfile
import inspect
import os


async def process_file(file):
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
        ingest_pdf_to_pinecone(text, namespace="pdf")
        ingest_text_to_faiss(text, namespace="pdf")
        os.remove(path)
        return "✅ PDF ingested into Pinecone & FAISS."

    elif suffix in ["jpg", "jpeg", "png"]:
        extracted = extract_image_text(path)
        if extracted and len(extracted.split()) > 5:
            ingest_text_to_faiss(extracted, namespace="image")
            os.remove(path)
            return "✅ Image description ingested into FAISS."
        else:
            description = describe_image(path)
            ingest_text_to_faiss(description, namespace="image")
            os.remove(path)
            return "✅ Gemini description ingested into FAISS."

    return "❌ Unsupported file format."


def handle_text(text: str, namespace: str | None = None):
    """Search uploaded content via FAISS/Pinecone.

    The optional ``namespace`` argument limits FAISS results to a specific
    namespace (e.g. ``"image"`` or ``"pdf"``). Pinecone is only queried when the
    namespace is ``None`` or ``"pdf"`` since it currently stores PDF data only.
    """

    result_pc = "No match found"
    if namespace in (None, "pdf"):
        # Query PDF namespace by default so uploaded files are considered
        result_pc = search_pinecone(text, namespace="pdf")

    result_faiss = search_faiss(text, namespace=namespace)

    pc_no_match = "no match found" in result_pc.lower()
    faiss_no_match = "no faiss match found" in result_faiss.lower()

    if pc_no_match and faiss_no_match:
        # Full multi‐engine fallback: ArXiv → Semantic Scholar → Web
        return search_agent.handle_query(text)

    return (
        f"Pinecone:\n{result_pc or 'No match found'}"
        f"\n\nFAISS:\n{result_faiss or 'No match found'}"
    )


def query_with_confidence(text: str):
    """Return best RAG answer and confidence across all namespaces."""
    best_answer = None
    best_conf = 0.0

    pc_ans, pc_conf = search_pinecone_with_score(text, namespace="pdf")
    if pc_conf > best_conf:
        best_answer, best_conf = pc_ans, pc_conf

    for ns in ["pdf", "image", "memory"]:
        ans, conf = search_faiss_with_score(text, namespace=ns)
        if conf > best_conf:
            best_answer, best_conf = ans, conf

    if not best_answer:
        return "No match found", 0.0

    return best_answer, best_conf


def save_memory(question: str, answer: str):
    """Persist Q&A pair into FAISS memory namespace."""
    ingest_text_to_faiss(f"Q: {question}\nA: {answer}", namespace="memory")
