# agents/rag_agent.py
from __future__ import annotations
import base64, os, tempfile, time, inspect
from uuid import uuid4
from collections import defaultdict
from cachetools import TTLCache
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from agents.clip_faiss import ingest_image as ingest_clip_image, search_by_vector, search_text
from vectorstore.faiss_embed_and_store import ingest_text_to_faiss
from vectorstore.faiss_store import search_faiss_with_score
from vectorstore.pinecone_store import ingest_pdf_text_to_pinecone, search_pinecone_with_score
from agents import search_agent, translate_agent
from models.gemini_vision import extract_image_text, summarize_text_gemini
from app.config import Settings

settings = Settings()
DEFAULT_SESSION_TTL = 3600
session_store: TTLCache[str, dict] = TTLCache(maxsize=128, ttl=DEFAULT_SESSION_TTL)
memory_cache: dict[str, list[str]] = defaultdict(list)

def _session_ns(base: str, sid: str|None) -> str:
    return f"{base}_{sid}" if sid else base

def _clean(txt: str) -> str:
    return txt.replace("<pad>", "").replace("<eos>", "").strip()

async def process_file(file, session_id: str|None=None) -> tuple[str,str]:
    sid = session_id or str(uuid4())
    name = getattr(file, "filename", getattr(file, "name", "upload"))
    suffix = name.rsplit(".",1)[-1].lower()
    data = await file.read() if inspect.iscoroutinefunction(file.read) else file.read()
    with tempfile.NamedTemporaryFile(delete=False, suffix=f".{suffix}") as tmp:
        tmp.write(data); path = tmp.name

    if suffix=="pdf":
        loader = PyPDFLoader(path); docs = loader.load()
        splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=0)
        chunks = [c for d in docs for c in splitter.split_text(d.page_content)]
        for chunk in chunks:
            ingest_pdf_text_to_pinecone(chunk, namespace=_session_ns("pdf", sid))
            ingest_text_to_faiss(chunk, namespace=_session_ns("pdf", sid))
        msg="✅ PDF ingested"
    elif suffix in {"png","jpg","jpeg","gif","webp"}:
        text = extract_image_text(path)
        ingest_text_to_faiss(text, namespace=_session_ns("image", sid))
        stored = ingest_clip_image(path, namespace=_session_ns("image", sid))
        msg="✅ Image ingested"
    else:
        os.remove(path); return "❌ Unsupported format", sid

    os.remove(path)
    session_store[sid] = {"text": ""}
    return msg, sid

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

def handle_query(mode:str, content:str, session_id:str, lang:str="en") -> tuple[str,float,str|None]:
    # 1) image mode → CLIP first then OCR
    if mode=="image":
        data=base64.b64decode(content)
        # CLIP
        clip_hits = search_text("", namespace=_session_ns("image", session_id), k=1)
        if clip_hits:
            return clip_hits[0]["url"], clip_hits[0]["score"], "image"
        # OCR fallback
        return extract_image_text(tempfile.NamedTemporaryFile(delete=False).name), 1.0, "ocr"

    # 2) voice = text
    if mode=="voice":
        # assume content already transcribed upstream
        pass

    # 3) text/search/pdf → RAG
    raw = session_store.get(session_id, {}).get("text","")
    combined = f"{raw}\nUser: {content}"
    excerpts,conf,src = query_pdf_image(combined, session_id)
    answer = rewrite_answer(excerpts, content, lang)
    # update memory + session
    save_memory(content, answer, session_id)
    session_store[session_id]={"text": combined + f"\nBot: {answer}"}
    return answer, conf, src
