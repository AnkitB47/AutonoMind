# --- vectorstore/faiss_embed_and_store.py ---
import os
from langchain.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings
from langchain.docstore.document import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter
from app.config import Settings

# Load environment settings
settings = Settings()

FAISS_INDEX_PATH = os.getenv("FAISS_INDEX_PATH", "faiss_db")
embedding_model = OpenAIEmbeddings(api_key=settings.OPENAI_API_KEY)
splitter = RecursiveCharacterTextSplitter(chunk_size=512, chunk_overlap=64)

def ingest_text_to_faiss(text: str, namespace: str = None):
    if not text.strip():
        return

    chunks = splitter.split_text(text)
    docs = [Document(page_content=chunk, metadata={"source": namespace or "generic"}) for chunk in chunks]

    if os.path.exists(FAISS_INDEX_PATH):
        db = FAISS.load_local(FAISS_INDEX_PATH, embedding_model)
        db.add_documents(docs)
    else:
        db = FAISS.from_documents(docs, embedding_model)

    db.save_local(FAISS_INDEX_PATH)
