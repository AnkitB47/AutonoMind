# --- vectorstore/pinecone_store.py ---
import os
import fitz  # PyMuPDF
from langchain_pinecone import PineconeVectorStore
from langchain_openai import OpenAIEmbeddings
from pinecone import Pinecone
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_core.documents import Document

# Initialize Pinecone client and config
pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
index_name = "multiagentrag" 
default_namespace = os.getenv("PINECONE_NAMESPACE", "default")

embedding_model = OpenAIEmbeddings()
text_splitter = RecursiveCharacterTextSplitter(chunk_size=512, chunk_overlap=64)


def search_pinecone(query, namespace=None):
    """Search a Pinecone namespace."""
    vectorstore = PineconeVectorStore.from_existing_index(
        index_name=index_name,
        embedding=embedding_model,
        namespace=namespace or default_namespace
    )
    results = vectorstore.similarity_search(query, k=3)
    return results[0].page_content if results else "No match found"


def upsert_document(text, namespace=None, metadata=None):
    """Ingest raw text to Pinecone with optional namespace and metadata."""
    docs = [Document(page_content=chunk, metadata=metadata or {}) 
            for chunk in text_splitter.split_text(text)]
    
    vectorstore = PineconeVectorStore.from_existing_index(
        index_name=index_name,
        embedding=embedding_model,
        namespace=namespace or default_namespace
    )
    vectorstore.add_documents(documents=docs)


def ingest_pdf_text_to_pinecone(text, namespace=None, source=""):
    """Ingest pre-extracted PDF text (used by RAG agent)."""
    upsert_document(text, namespace=namespace, metadata={"source": source})
    

def ingest_pdf_file_to_pinecone(file_path, namespace=None):
    """Extract text from a PDF file and ingest to Pinecone."""
    doc = fitz.open(file_path)
    text = "\n".join(page.get_text() for page in doc)
    source = os.path.basename(file_path)
    ingest_pdf_text_to_pinecone(text, namespace=namespace, source=source)
