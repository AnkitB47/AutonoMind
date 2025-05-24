# --- vectorstore/pinecone_store.py ---
from langchain.vectorstores import Pinecone
from langchain.embeddings import OpenAIEmbeddings
import pinecone
import os

pinecone.init(api_key=os.getenv("PINECONE_API_KEY"), environment="gcp-starter")
index = pinecone.Index("autono-index")

def search_pinecone(query):
    return Pinecone.from_existing_index("autono-index", OpenAIEmbeddings()).similarity_search(query, k=3)[0].page_content
