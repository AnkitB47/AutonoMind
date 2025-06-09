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
FAISS_INDEX_PATH = settings.FAISS_INDEX_PATH

# Internal store cache
store = None


def load_or_create_faiss():
    """Load FAISS index from disk or create a dummy fallback index."""
    global store
    if store is not None:
        return

    if os.path.exists(FAISS_INDEX_PATH):
        print(f"✅ Loading FAISS index from {FAISS_INDEX_PATH}")
        store = FAISS.load_local(
            FAISS_INDEX_PATH, embedding_model, allow_dangerous_deserialization=True
        )
    else:
        print(f"⚠️  FAISS index not found. Creating dummy index at {FAISS_INDEX_PATH}")
        generate_faiss_index(["This is a fallback document."])


def search_faiss(query: str, namespace: str | None = None):
    """Query the FAISS index and return the best match.

    Args:
        query: The search string.
        namespace: If provided, limit results to documents whose ``source``
            metadata matches this value.
    """
    load_or_create_faiss()
    docs_and_scores = store.similarity_search_with_score(query, k=5)

    if namespace:
        docs_and_scores = [
            (doc, score)
            for doc, score in docs_and_scores
            if doc.metadata.get("source") == namespace
        ]

    if not docs_and_scores:
        return "No FAISS match found"

    best_doc, _ = max(docs_and_scores, key=lambda x: x[1])
    return best_doc.page_content.strip()


def generate_faiss_index(docs: list[str]):
    """Generate and save a new FAISS index from a list of strings."""
    global store
    print(f"⚙️  Generating FAISS index with {len(docs)} documents...")

    documents = [
        Document(page_content=doc, metadata={"source": f"doc_{i}"})
        for i, doc in enumerate(docs)
    ]
    store = FAISS.from_documents(documents, embedding_model)
    store.save_local(FAISS_INDEX_PATH)
    print(f"✅ FAISS index saved at {FAISS_INDEX_PATH}")
