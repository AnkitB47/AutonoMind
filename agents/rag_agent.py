# agents/rag_agent.py
from __future__ import annotations
import base64, os, tempfile, time, inspect, logging, json
from uuid import uuid4
from collections import defaultdict
from cachetools import TTLCache
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from agents.clip_faiss import ingest_image as ingest_clip_image, search_by_vector, search_text, search_image
from vectorstore.faiss_embed_and_store import ingest_text_to_faiss
from vectorstore.faiss_store import search_faiss_with_score
from vectorstore.pinecone_store import ingest_pdf_text_to_pinecone, search_pinecone_with_score
from agents import search_agent, translate_agent
from models.gemini_vision import extract_image_text, summarize_text_gemini
from app.config import Settings

# Configure logging
logger = logging.getLogger(__name__)

settings = Settings()
DEFAULT_SESSION_TTL = 3600
session_store: TTLCache[str, dict] = TTLCache(maxsize=128, ttl=DEFAULT_SESSION_TTL)
memory_cache: dict[str, list[str]] = defaultdict(list)

def _session_ns(base: str, sid: str|None) -> str:
    return f"{base}_{sid}" if sid else base

def _clean(txt: str) -> str:
    return txt.replace("<pad>", "").replace("<eos>", "").strip()

def _is_image_query(query: str) -> bool:
    """Detect if a text query should be treated as an image query."""
    image_keywords = [
        'image', 'picture', 'photo', 'look', 'see', 'show', 'display',
        'what is this', 'what does this look like', 'describe this', 'similar',
        'appears', 'contains', 'shows', 'depicts', 'represents', 'illustrates',
        'this image', 'this picture', 'this photo', 'the image', 'the picture'
    ]
    
    lower_query = query.lower()
    return any(keyword in lower_query for keyword in image_keywords)

async def process_file(file, session_id: str|None=None) -> tuple[str,str]:
    """Process uploaded file with comprehensive error handling."""
    temp_path = None
    try:
        sid = session_id or str(uuid4())
        name = getattr(file, "filename", getattr(file, "name", "upload"))
        suffix = name.rsplit(".",1)[-1].lower()

        logger.info(f"Processing file: {name} (suffix: {suffix}) for session: {sid}")

        # Read file data with error handling
        try:
            data = await file.read() if inspect.iscoroutinefunction(file.read) else file.read()
            logger.info(f"Read {len(data)} bytes from file: {name}")
        except Exception as e:
            logger.error(f"Failed to read file {name}: {str(e)}")
            raise Exception(f"File read failed: {str(e)}")

        # Create temporary file
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=f".{suffix}") as tmp:
                tmp.write(data)
                temp_path = tmp.name
            logger.info(f"Created temporary file: {temp_path}")
        except Exception as e:
            logger.error(f"Failed to create temporary file: {str(e)}")
            raise Exception(f"Temporary file creation failed: {str(e)}")

        # Process based on file type
        if suffix == "pdf":
            logger.info(f"Processing PDF: {name}")
            try:
                loader = PyPDFLoader(temp_path)
                docs = loader.load()
                logger.info(f"Loaded {len(docs)} pages from PDF")

                splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=0)
                chunks = [c for d in docs for c in splitter.split_text(d.page_content)]
                logger.info(f"Created {len(chunks)} text chunks")

                for i, chunk in enumerate(chunks):
                    try:
                        ingest_pdf_text_to_pinecone(chunk, namespace=_session_ns("pdf", sid))
                        ingest_text_to_faiss(chunk, namespace=_session_ns("pdf", sid))
                        if i % 10 == 0:  # Log progress every 10 chunks
                            logger.info(f"Processed {i+1}/{len(chunks)} chunks")
                    except Exception as e:
                        logger.error(f"Failed to ingest chunk {i}: {str(e)}")
                        # Continue with other chunks

                msg = "✅ PDF ingested"
                logger.info(f"PDF processing completed: {msg}")

            except Exception as e:
                logger.error(f"PDF processing failed: {str(e)}")
                raise Exception(f"PDF processing failed: {str(e)}")

        elif suffix in {"png", "jpg", "jpeg", "gif", "webp"}:
            logger.info(f"Processing image: {name}")
            try:
                text = extract_image_text(temp_path)
                logger.info(f"Extracted text from image: {len(text)} characters")

                ingest_text_to_faiss(text, namespace=_session_ns("image", sid))
                logger.info("Text ingested to FAISS")

                stored = ingest_clip_image(temp_path, namespace=_session_ns("image", sid))
                logger.info("Image ingested to CLIP")

                msg = "✅ Image ingested"
                logger.info(f"Image processing completed: {msg}")

            except Exception as e:
                logger.error(f"Image processing failed: {str(e)}")
                raise Exception(f"Image processing failed: {str(e)}")
        else:
            logger.warning(f"Unsupported file format: {suffix}")
            raise Exception(f"Unsupported format: {suffix}")

        # Store session with upload context
        session_store[sid] = {
            "text": "",
            "last_upload_type": "pdf" if suffix == "pdf" else "image",
            "last_upload_name": name
        }
        logger.info(f"Session stored: {sid} with upload type: {session_store[sid]['last_upload_type']}")

        return msg, sid

    except Exception as e:
        logger.error(f"process_file failed: {str(e)}", exc_info=True)
        raise
    finally:
        # Clean up temporary file
        if temp_path and os.path.exists(temp_path):
            try:
                os.remove(temp_path)
                logger.info(f"Cleaned up temporary file: {temp_path}")
            except Exception as e:
                logger.warning(f"Failed to clean up temporary file {temp_path}: {str(e)}")

def _search_all(text:str, sid:str, include_mem:bool) -> tuple[str,float,str|None]:
    ranked = []
    # PDF/text
    for fn in (search_pinecone_with_score, search_faiss_with_score):
        ans,conf=fn(text, namespace=_session_ns("pdf", sid), k=3)
        if ans: ranked.append((_clean(ans), conf, "pdf"))
    # memory
    if include_mem:
        ans,conf=search_faiss_with_score(text, namespace=_session_ns("memory", sid), k=3)
        if ans: ranked.append((_clean(ans), conf, "memory"))
    # CLIP-image
    clip_hits = search_text(text, namespace=_session_ns("image", sid), k=1)
    if clip_hits:
        ranked.append((clip_hits[0]["url"], clip_hits[0]["score"], "image"))

    if not ranked:
        return "No match found", 0.0, None
    # best
    ranked.sort(key=lambda x: x[1], reverse=True)
    return ranked[0]

def query_pdf_image(text:str, session_id:str|None=None) -> tuple[str,float,str|None]:
    if not session_id: raise ValueError("session_id required")
    return _search_all(text, session_id, include_mem=False)

def query_with_confidence(text:str, session_id:str|None=None) -> tuple[str,float,str|None]:
    if not session_id: raise ValueError("session_id required")
    return _search_all(text, session_id, include_mem=True)

def rewrite_answer(excerpts:str, question:str, lang:str)->str:
    prompt = f"You are a friendly assistant. The user asked: '{question}'.\nExcerpts:\n{excerpts}"
    try:
        return summarize_text_gemini(excerpts, question)
    except:
        from langchain_openai import ChatOpenAI
        llm = ChatOpenAI(temperature=0.2)
        return llm.predict(prompt)

def save_memory(q:str, a:str, session_id:str|None=None):
    entry=f"Q:{q}\nA:{a}"
    ingest_text_to_faiss(entry, namespace=_session_ns("memory",session_id))
    if session_id: memory_cache[session_id].append(entry)

def search_similar_images_by_image(data: bytes, session_id: str, k: int = 3):
    """Search the FAISS index using the image embedding."""
    hits = search_image(data, namespace=_session_ns("image", session_id), k=k)
    return hits

def handle_query(mode:str, content:str, session_id:str, lang:str="en") -> tuple[str,float,str|None]:
    logger.info(f"handle_query: mode={mode}, session_id={session_id}, content_length={len(content)}")
    
    # 1) image mode → CLIP first then OCR
    if mode=="image":
        logger.info("Processing as image query")
        try:
            data=base64.b64decode(content)
            # CLIP image-to-image search
            clip_hits = search_similar_images_by_image(data, session_id, k=3)
            if clip_hits:
                logger.info(f"CLIP image search found {len(clip_hits)} results")
                response_data = {
                    "results": [
                        {"image_url": hit["url"], "score": hit["score"]}
                        for hit in clip_hits
                    ],
                    "description": f"Top {len(clip_hits)} similar images found."
                }
                return json.dumps(response_data), clip_hits[0]["score"], "image"
            # OCR fallback
            logger.info("No CLIP image results, using OCR fallback")
            with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as tmp:
                tmp.write(data)
                temp_path = tmp.name
            ocr_text = extract_image_text(temp_path)
            response_data = {
                "description": ocr_text,
                "fallback": "No similar images found, showing OCR text instead"
            }
            return json.dumps(response_data), 1.0, "ocr"
        except Exception as e:
            logger.error(f"Image query processing failed: {str(e)}")
            mode = "text"
    # 2) voice = text
    if mode=="voice":
        # assume content already transcribed upstream
        pass

    # 3) text/search/pdf → RAG with smart routing
    logger.info("Processing as text query")
    
    # Check if this should be treated as an image query based on content and session context
    session_info = session_store.get(session_id, {})
    last_upload_type = session_info.get("last_upload_type")
    
    should_use_image_search = (
        last_upload_type == "image" and 
        _is_image_query(content)
    )
    
    if should_use_image_search:
        logger.info("Detected image-related query, prioritizing image search")
        # Search image content first
        image_hits = search_text(content, namespace=_session_ns("image", session_id), k=3)
        if image_hits:
            logger.info(f"Image search found {len(image_hits)} results")
            # Return the best image match as structured JSON
            best_hit = max(image_hits, key=lambda x: x["score"])
            response_data = {
                "image_url": best_hit["url"],
                "description": f"Similar image found for query: '{content}' with confidence: {best_hit['score']:.2f}"
            }
            return json.dumps(response_data), best_hit["score"], "image"
    
    # Standard RAG processing
    raw = session_info.get("text","")
    combined = f"{raw}\nUser: {content}"
    excerpts, conf, src = query_with_confidence(combined, session_id)
    if excerpts == "No match found":
        # Fallback to Wikipedia/Arxiv/Semantic Scholar, then web search
        logger.info("PDF RAG found no answer, falling back to Wikipedia/Arxiv/Semantic Scholar/web search")
        fallback_answer = search_agent.handle_query(content)
        # Optionally, you can tag the source as 'fallback' or 'web'
        return fallback_answer, 0.0, "fallback"
    answer = rewrite_answer(excerpts, content, lang)
    # update memory + session
    save_memory(content, answer, session_id)
    session_store[session_id] = {"text": combined + f"\nBot: {answer}", "last_upload_type": last_upload_type}
    return answer, conf, src
