# --- vectorstore/faiss_embed_and_store.py ---
import os
import logging
from langchain_text_splitters import RecursiveCharacterTextSplitter
from app.config import Settings

logger = logging.getLogger(__name__)

# Load environment settings
settings = Settings()

# path retained for backward compatibility
FAISS_INDEX_PATH = settings.FAISS_INDEX_PATH
# Use slightly larger chunks with overlap for better contextual retrieval
splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)

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
    try:
        faiss_store.add_texts(chunks, namespace)
    except Exception as e:
        logger.exception("\u274c FAISS ingest failed: %s", e)
