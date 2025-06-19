import os
import requests
from models.gemini_vision import summarize_text_gemini
from langchain_openai import ChatOpenAI
from urllib.parse import quote_plus
import string

# --- Web Search using SerpAPI ---
def search_web(query: str) -> str:
    api_key = os.getenv("SERPAPI_API_KEY")
    if not api_key:
        return "❌ SERPAPI_API_KEY not set."

    params = {
        "engine": "google",
        "q": query,
        "api_key": api_key,
        "num": 3,
    }

    try:
        res = requests.get("https://serpapi.com/search", params=params, timeout=10)
        data = res.json()
        results = data.get("organic_results", [])
        if not results:
            return "🔍 No web results found."
        text = "\n\n".join([f"{r.get('title')}\n{r.get('link')}" for r in results])
        return summarize(text, query, mode="web")
    except Exception as e:
        return f"❌ Web search failed: {str(e)}"


# --- arXiv Scientific Search ---
def search_arxiv(query: str) -> str:
    try:
        sanitized = quote_plus(query.rstrip(string.punctuation).strip())
        url = "http://export.arxiv.org/api/query"
        params = {
            "search_query": f"all:{sanitized}",
            "start": 0,
            "max_results": 3,
        }
        res = requests.get(url, params=params, timeout=10)
        res.raise_for_status()
        entries = res.text.split("<entry>")[1:]
        results = []
        for entry in entries:
            title = entry.split("<title>")[1].split("</title>")[0].strip()
            link = entry.split("<id>")[1].split("</id>")[0].strip()
            results.append(f"{title}\n{link}")
        if not results:
            return "📚 No arXiv results found."
        return summarize("\n\n".join(results), query, mode="arxiv")
    except Exception as e:
        return f"❌ arXiv search failed: {str(e)}"


# --- Fallback: Semantic Scholar API ---
def search_semantic_scholar(query: str) -> str:
    try:
        url = f"https://api.semanticscholar.org/graph/v1/paper/search?query={query}&limit=3&fields=title,url"
        headers = {"User-Agent": "AutonoMind/1.0"}
        res = requests.get(url, headers=headers, timeout=10)
        papers = res.json().get("data", [])
        if not papers:
            return "📘 No results found on Semantic Scholar."
        formatted = "\n\n".join([f"{p['title']}\n{p['url']}" for p in papers])
        return summarize(formatted, query, mode="semantic")
    except Exception as e:
        return f"❌ Semantic Scholar failed: {str(e)}"


# --- Smart Summarizer (Gemini > fallback to OpenAI) ---
def summarize(text: str, query: str, mode: str = "web") -> str:
    try:
        # Gemini-based summarization
        summary = summarize_text_gemini(text, query)
        return f"🔎 {mode.upper()} Summary:\n{summary}"
    except Exception:
        try:
            # Fallback to OpenAI
            llm = ChatOpenAI(temperature=0.3, model_name="gpt-4")
            prompt = f"Summarize the following search results based on the query: '{query}'\n\n{text}"
            summary = llm.predict(prompt)
            return f"🧠 {mode.upper()} Summary (OpenAI):\n{summary}"
        except Exception as e:
            return f"⚠️ Summary failed: {str(e)}\n\nRaw Results:\n{text}"


# --- Entry Point ---
def handle_query(query: str) -> str:
    if not query or not query.strip():
        return "❌ Empty search query"
    query_lower = query.lower()
    if "arxiv" in query_lower:
        return search_arxiv(query)
    if "science" in query_lower or "paper" in query_lower:
        return search_semantic_scholar(query)
    return search_web(query)
