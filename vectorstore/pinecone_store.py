# --- vectorstore/pinecone_store.py ---
from langchain.vectorstores import Pinecone
from langchain.embeddings import OpenAIEmbeddings
import pinecone
import os

pinecone.init(api_key=os.getenv("PINECONE_API_KEY"))
index = pinecone.Index(
    host=os.getenv("PINECONE_INDEX_HOST"),
    index_name=os.getenv("PINECONE_INDEX_NAME")
)


def search_pinecone(query):
    return Pinecone.from_existing_index("autono-index", OpenAIEmbeddings()).similarity_search(query, k=3)[0].page_content
