# --- vectorstore/faiss_store.py ---
import os
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings
from langchain_core.documents import Document
from app.config import Settings

# Load environment settings
settings = Settings()
embedding_model = OpenAIEmbeddings(api_key=settings.OPENAI_API_KEY)

# Define constant FAISS path
FAISS_INDEX_PATH = "/data/vector.index"

# Internal store cache
store = None

def load_or_create_faiss():
    """Load FAISS index from disk or create a dummy fallback index."""
    global store
    if store is not None:
        return

    if os.path.exists(FAISS_INDEX_PATH):
        print(f"✅ Loading FAISS index from {FAISS_INDEX_PATH}")
        store = FAISS.load_local(FAISS_INDEX_PATH, embedding_model, allow_dangerous_deserialization=True)
    else:
        print(f"⚠️  FAISS index not found. Creating dummy index at {FAISS_INDEX_PATH}")
        generate_faiss_index(["This is a fallback document."])

def search_faiss(query: str):
    """Query the FAISS index."""
    load_or_create_faiss()
    results = store.similarity_search(query, k=3)
    return results[0].page_content if results else "No FAISS match found"

def generate_faiss_index(docs: list[str]):
    """Generate and save a new FAISS index from a list of strings."""
    global store
    print(f"⚙️  Generating FAISS index with {len(docs)} documents...")

    documents = [Document(page_content=doc, metadata={"source": f"doc_{i}"}) for i, doc in enumerate(docs)]
    store = FAISS.from_documents(documents, embedding_model)
    store.save_local(FAISS_INDEX_PATH)
    print(f"✅ FAISS index saved at {FAISS_INDEX_PATH}")
