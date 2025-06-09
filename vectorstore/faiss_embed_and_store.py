# --- vectorstore/faiss_embed_and_store.py ---
import os
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from app.config import Settings

# Load environment settings
settings = Settings()

FAISS_INDEX_PATH = settings.FAISS_INDEX_PATH
embedding_model = OpenAIEmbeddings(api_key=settings.OPENAI_API_KEY)
# Use slightly larger chunks with overlap for better contextual retrieval
splitter = RecursiveCharacterTextSplitter(chunk_size=800, chunk_overlap=200)

def ingest_text_to_faiss(text: str, namespace: str = None):
    """Embed ``text`` and persist to the FAISS index.

    The FAISS store used for retrieval is cached globally in
    :mod:`vectorstore.faiss_store`. Importing within this function avoids
    circular imports when updating that cache.
    """
    # Import here to prevent circular dependency at module load time
    from vectorstore import faiss_store
    if not text.strip():
        return

    chunks = splitter.split_text(text)
    docs = [Document(page_content=chunk, metadata={"source": namespace or "generic"}) for chunk in chunks]

    if os.path.exists(FAISS_INDEX_PATH):
        db = FAISS.load_local(FAISS_INDEX_PATH, embedding_model, allow_dangerous_deserialization=True)
        db.add_documents(docs)
    else:
        db = FAISS.from_documents(docs, embedding_model)

    db.save_local(FAISS_INDEX_PATH)
    # Update the global FAISS cache so new docs are immediately searchable
    faiss_store.store = db
    print(f"FAISS count: {db.index.ntotal}")
