# --- agents/rag_agent.py ---
from vectorstore.pinecone_store import search_pinecone
from vectorstore.faiss_store import search_faiss
from langchain.document_loaders import PyPDFLoader
from models.gemini_vision import extract_image_text
import tempfile


async def process_file(file):
    suffix = file.filename.split(".")[-1]
    with tempfile.NamedTemporaryFile(delete=False, suffix=f".{suffix}") as tmp:
        tmp.write(await file.read())
        path = tmp.name
    if suffix in ["pdf"]:
        loader = PyPDFLoader(path)
        docs = loader.load()
        return search_pinecone(docs[0].page_content)
    elif suffix in ["jpg", "png"]:
        return search_faiss(extract_image_text(path))
    return "Unsupported file"


def handle_text(text):
    return search_pinecone(text)
