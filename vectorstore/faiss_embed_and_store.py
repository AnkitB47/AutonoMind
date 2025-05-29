# --- vectorstore/faiss_embed_and_store.py ---
import os
from langchain.vectorstores import FAISS
from langchain.embeddings import OpenAIEmbeddings
from langchain.docstore.document import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter

embedding_model = OpenAIEmbeddings()
db_path = "faiss_db"


def ingest_text_to_faiss(text, namespace=None):
    if not text.strip():
        return

    splitter = RecursiveCharacterTextSplitter(chunk_size=512, chunk_overlap=64)
    chunks = splitter.split_text(text)
    docs = [Document(page_content=chunk, metadata={"source": namespace or "generic"}) for chunk in chunks]

    if os.path.exists(db_path):
        db = FAISS.load_local(db_path, embedding_model)
        db.add_documents(docs)
    else:
        db = FAISS.from_documents(docs, embedding_model)
    db.save_local(db_path)
    