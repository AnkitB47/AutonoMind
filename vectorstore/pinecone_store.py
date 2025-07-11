# --- vectorstore/pinecone_store.py ---
import os
import logging
import fitz
from app.config import Settings
from pinecone import Pinecone
from langchain_pinecone import PineconeVectorStore
from langchain_openai import OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document

logger = logging.getLogger(__name__)

# Load environment settings
settings = Settings()

# Init Pinecone client using config
pc = Pinecone(api_key=settings.PINECONE_API_KEY)

index_name = settings.PINECONE_INDEX_NAME
default_namespace = os.getenv("PINECONE_NAMESPACE", "default")
embedding_model = OpenAIEmbeddings(api_key=settings.OPENAI_API_KEY)
# Match FAISS chunk strategy for consistency
text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)


def search_pinecone(query, namespace=None):
    """Search Pinecone and return the best matching chunk."""
    vectorstore = PineconeVectorStore.from_existing_index(
        index_name=index_name,
        embedding=embedding_model,
        namespace=namespace or default_namespace
    )
    docs_and_scores = vectorstore.similarity_search_with_score(query, k=5)
    if not docs_and_scores:
        return "No match found"

    best_doc, _ = min(docs_and_scores, key=lambda x: x[1])
    return best_doc.page_content.strip()


def search_pinecone_with_score(query, namespace=None, k: int = 3):
    """Return concatenated top ``k`` texts and confidence score from Pinecone."""
    vectorstore = PineconeVectorStore.from_existing_index(
        index_name=index_name,
        embedding=embedding_model,
        namespace=namespace or default_namespace
    )
    docs_and_scores = vectorstore.similarity_search_with_score(query, k=k)
    if not docs_and_scores:
        return None, 0.0

    # Assume results are ordered by similarity (lower score is better)
    top_text = "\n".join(doc.page_content for doc, _ in docs_and_scores[:k])
    best_score = docs_and_scores[0][1]
    confidence = 1 / (1 + best_score)
    return top_text.strip(), confidence


def upsert_document(text, namespace=None, metadata=None):
    docs = [Document(page_content=chunk, metadata=metadata or {})
            for chunk in text_splitter.split_text(text)]

    vectorstore = PineconeVectorStore.from_existing_index(
        index_name=index_name,
        embedding=embedding_model,
        namespace=namespace or default_namespace
    )
    vectorstore.add_documents(documents=docs)
    stats = pc.Index(index_name).describe_index_stats()
    logger.info("Pinecone count: %s", stats['total_vector_count'])


def ingest_pdf_text_to_pinecone(text, namespace=None, source=""):
    upsert_document(text, namespace=namespace, metadata={"source": source})


def ingest_pdf_file_to_pinecone(file_path, namespace=None):
    doc = fitz.open(file_path)
    text = "\n".join(page.get_text() for page in doc)
    source = os.path.basename(file_path)
    ingest_pdf_text_to_pinecone(text, namespace=namespace, source=source)
