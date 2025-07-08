# agents/rag_agent.py
from __future__ import annotations
import base64, os, tempfile, time, inspect, logging, json
from uuid import uuid4
from collections import defaultdict
from cachetools import TTLCache
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from vectorstore.faiss_embed_and_store import ingest_text_to_faiss
from vectorstore.faiss_store import search_faiss_with_score
from vectorstore.pinecone_store import ingest_pdf_text_to_pinecone, search_pinecone_with_score
from agents import search_agent, translate_agent
from models.gemini_vision import summarize_text_gemini
from app.config import Settings
from typing import Any, Dict

# Configure logging
logger = logging.getLogger(__name__)

settings = Settings()
DEFAULT_SESSION_TTL = 3600

session_store: TTLCache[str, Dict[str, Any]] = TTLCache(maxsize=128, ttl=DEFAULT_SESSION_TTL)

memory_cache: dict[str, list[str]] = defaultdict(list)
MIN_CONFIDENCE = 0.3

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

def _sanitize_b64(content: str) -> bytes:
    import base64, re, urllib.parse
    # Remove data:image/...;base64, prefix
    content = re.sub(r"^data:image/[^;]+;base64,", "", content)
    # URL decode
    content = urllib.parse.unquote(content)
    # Remove whitespace
    content = content.strip().replace("\n", "").replace(" ", "")
    # Pad to multiple of 4
    missing_padding = len(content) % 4
    if missing_padding:
        content += "=" * (4 - missing_padding)
    # Validate base64
    try:
        return base64.b64decode(content, validate=True)
    except Exception as e:
        raise ValueError(f"Invalid base64 image data: {str(e)}")

async def process_file(file, session_id: str|None=None) -> tuple[str,str]:
    """Process uploaded file with comprehensive error handling (PDF only)."""
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
        else:
            logger.warning(f"Unsupported file format: {suffix}")
            raise Exception(f"Unsupported format: {suffix}")

        # Store session with upload context
        session_store[sid] = {
            "text": "",
            "last_upload_type": "pdf" if suffix == "pdf" else "other",
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

async def handle_query(mode: str, content: str, session_id: str, lang: str = "en") -> tuple[str, float, str | None]:
    logger.info(f"handle_query: mode={mode}, session_id={session_id}, content_length={len(content)}")
    session_info = session_store.get(session_id, {})
    last_upload_type = session_info.get("last_upload_type")
    last_upload_name = session_info.get("last_upload_name")
    raw = session_info.get("text", "")

    # Ensure session exists
    if not session_info:
        logger.warning(f"Session {session_id} not found. Creating new session context.")
        session_store[session_id] = {"text": "", "last_upload_type": None, "last_upload_name": None}
        last_upload_type = None
        raw = ""

    # 1) Image mode: CLIP image-to-image, else OCR fallback
    if mode == "image":
        try:
            data = _sanitize_b64(content)
            with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as tmp:
                tmp.write(data)
                temp_path = tmp.name
            # OCR fallback
            ocr_text = summarize_text_gemini(content, content) # Assuming summarize_text_gemini can handle image text
            response_data = {"ocr_text": ocr_text}
            if temp_path and os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                except Exception:
                    pass
            save_memory("[image upload]", ocr_text, session_id)
            session_store[session_id] = {
                "text": raw + f"\nUser: [image upload]\nBot: {ocr_text}",
                "last_upload_type": "image",
                "last_upload_name": last_upload_name
            }
            return json.dumps(response_data), 1.0, "ocr"
        except ValueError as e:
            logger.error(f"Image query processing failed (base64): {str(e)}")
            return f"Image query processing failed: {str(e)}", 0.0, None
        except Exception as e:
            logger.error(f"Image query processing failed: {str(e)}")
            return f"Image query processing failed: {str(e)}", 0.0, None
    # 2) Voice mode: treat as text (already transcribed)
    if mode == "voice":
        pass
    # 3) Text mode: route to image or PDF RAG
    if mode == "text":
        combined = f"{raw}\nUser: {content}"
        excerpts, conf, src = query_with_confidence(combined, session_id)
        if conf < MIN_CONFIDENCE:
            for fn, tag in [
                (search_agent.search_arxiv, "arxiv"),
                (search_agent.search_semantic_scholar, "semantic_scholar"),
                (search_agent.search_web, "web"),
            ]:
                res = fn(content)
                if res and "no" not in res.lower():
                    save_memory(content, res, session_id)
                    session_store[session_id] = {
                        "text": raw + f"\nUser: {content}\nBot: {res}",
                        "last_upload_type": last_upload_type,
                        "last_upload_name": last_upload_name
                    }
                    return res, 0.0, tag
            save_memory(content, "No answer found", session_id)
            session_store[session_id] = {
                "text": raw + f"\nUser: {content}\nBot: No answer found",
                "last_upload_type": last_upload_type,
                "last_upload_name": last_upload_name
            }
            return "No answer found", 0.0, None
        answer = rewrite_answer(excerpts, content, lang)
        save_memory(content, answer, session_id)
        session_store[session_id] = {
            "text": raw + f"\nUser: {content}\nBot: {answer}",
            "last_upload_type": last_upload_type,
            "last_upload_name": last_upload_name
        }
        return answer, conf, src
    # fallback: treat as text
    answer = f"[Unhandled mode: {mode}]"
    save_memory(content, answer, session_id)
    session_store[session_id] = {
        "text": raw + f"\nUser: {content}\nBot: {answer}",
        "last_upload_type": last_upload_type,
        "last_upload_name": last_upload_name
    }
    return answer, 0.0, None
