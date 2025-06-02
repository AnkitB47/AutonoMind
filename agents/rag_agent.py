# --- agents/rag_agent.py ---
from vectorstore.pinecone_store import search_pinecone, ingest_pdf_text_to_pinecone as ingest_pdf_to_pinecone
from vectorstore.faiss_store import search_faiss
from vectorstore.faiss_embed_and_store import ingest_text_to_faiss
from langchain_community.document_loaders import PyPDFLoader
from models.gemini_vision import extract_image_text, describe_image
import tempfile
import inspect


async def process_file(file):
    name = getattr(file, "filename", None) or getattr(file, "name", "unknown.unknown")
    suffix = name.split(".")[-1].lower()

    # ✅ Handle Streamlit (sync) or FastAPI (async)
    read_method = file.read
    data = await read_method() if inspect.iscoroutinefunction(read_method) else read_method()

    with tempfile.NamedTemporaryFile(delete=False, suffix=f".{suffix}") as tmp:
        tmp.write(data)
        path = tmp.name

    if suffix == "pdf":
        loader = PyPDFLoader(path)
        docs = loader.load()
        text = docs[0].page_content
        ingest_pdf_to_pinecone(text, namespace="pdf")
        ingest_text_to_faiss(text, namespace="pdf")
        return "✅ PDF ingested into Pinecone & FAISS."

    elif suffix in ["jpg", "jpeg", "png"]:
        extracted = extract_image_text(path)
        if extracted and len(extracted.split()) > 5:
            ingest_text_to_faiss(extracted, namespace="image")
            return "✅ Image description ingested into FAISS."
        else:
            description = describe_image(path)
            ingest_text_to_faiss(description, namespace="image")
            return "✅ Gemini description ingested into FAISS."

    return "❌ Unsupported file format."


def handle_text(text: str):
    result_pc = search_pinecone(text)
    result_faiss = search_faiss(text)
    return f"Pinecone:\n{result_pc or 'No match found'}\n\nFAISS:\n{result_faiss or 'No match found'}"
