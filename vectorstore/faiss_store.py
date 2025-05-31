import os
from langchain.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings
from app.config import Settings

settings = Settings()

# Path to FAISS index
FAISS_INDEX_PATH = os.getenv("FAISS_INDEX_PATH", "/data/vector.index")
embedding_model = OpenAIEmbeddings(api_key=settings.OPENAI_API_KEY)

# Auto-generate empty FAISS if in dev mode
if not os.path.exists(FAISS_INDEX_PATH):
    if settings.env != "production":
        print(f"⚠️  [DEV MODE] Creating dummy FAISS index at {FAISS_INDEX_PATH}")
        dummy = FAISS.from_texts(["hello world"], embedding_model)
        dummy.save_local(FAISS_INDEX_PATH)
    else:
        raise FileNotFoundError(f"❌ FAISS index not found at: {FAISS_INDEX_PATH}")


store = FAISS.load_local(FAISS_INDEX_PATH, embedding_model)


def search_faiss(query: str):
    results = store.similarity_search(query, k=3)
    return results[0].page_content if results else "No FAISS match found"
