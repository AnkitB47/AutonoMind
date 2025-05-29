# --- vectorstore/faiss_store.py ---
from langchain.vectorstores import FAISS
from langchain.embeddings import OpenAIEmbeddings

store = FAISS.load_local("faiss_db", OpenAIEmbeddings())


def search_faiss(query):
    return store.similarity_search(query, k=3)[0].page_content