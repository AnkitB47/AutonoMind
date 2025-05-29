# --- vectorstore/faiss_store.py ---
import os
from langchain.vectorstores import FAISS
from langchain.embeddings import OpenAIEmbeddings
from app.config import settings

FAISS_INDEX_PATH = os.getenv("FAISS_INDEX_PATH", "faiss_db")
embedding_model = OpenAIEmbeddings(api_key=settings.OPENAI_API_KEY)

if not os.path.exists(FAISS_INDEX_PATH):
    raise FileNotFoundError(f"❌ FAISS index not found at: {FAISS_INDEX_PATH}")

store = FAISS.load_local(FAISS_INDEX_PATH, embedding_model)

def search_faiss(query: str):
    results = store.similarity_search(query, k=3)
    return results[0].page_content if results else "No FAISS match found"
