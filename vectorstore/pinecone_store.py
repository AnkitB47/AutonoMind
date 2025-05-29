# --- vectorstore/pinecone_store.py ---
import os
import fitz  # PyMuPDF
from langchain_community.vectorstores import Pinecone as LangchainPinecone
from langchain.embeddings import OpenAIEmbeddings
from pinecone import Pinecone
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.docstore.document import Document

# Initialize Pinecone client and config
pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
index_name = os.getenv("PINECONE_INDEX_NAME")
index_host = os.getenv("PINECONE_INDEX_HOST")
default_namespace = os.getenv("PINECONE_NAMESPACE", "default")

embedding_model = OpenAIEmbeddings()
text_splitter = RecursiveCharacterTextSplitter(chunk_size=512, chunk_overlap=64)


def search_pinecone(query, namespace=None):
    """Search a Pinecone namespace."""
    vectorstore = LangchainPinecone.from_existing_index(
        index_name=index_name,
        embedding=embedding_model,
        pinecone_client=pc,
        namespace=namespace or default_namespace
    )
    results = vectorstore.similarity_search(query, k=3)
    return results[0].page_content if results else "No match found"


def upsert_document(text, namespace=None, metadata=None):
    """Ingest raw text to Pinecone with optional namespace and metadata."""
    docs = [Document(page_content=chunk, metadata=metadata or {}) for chunk in text_splitter.split_text(text)]
    LangchainPinecone.from_documents(
        documents=docs,
        embedding=embedding_model,
        index_name=index_name,
        pinecone_client=pc,
        namespace=namespace or default_namespace
    )


def ingest_pdf_text_to_pinecone(text, namespace=None, source=""):
    """Ingest pre-extracted PDF text (used by RAG agent)."""
    upsert_document(text, namespace=namespace, metadata={"source": source})


def ingest_pdf_file_to_pinecone(file_path, namespace=None):
    """Extract text from a PDF file and ingest to Pinecone."""
    doc = fitz.open(file_path)
    text = "\n".join(page.get_text() for page in doc)
    source = os.path.basename(file_path)
    ingest_pdf_text_to_pinecone(text, namespace=namespace, source=source)