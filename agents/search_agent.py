# --- agents/search_agent.py ---
import requests

def handle_query(query: str):
    if "arxiv" in query.lower():
        return search_arxiv(query)
    return search_web(query)

def search_web(query: str):
    return f"Web result for: {query}"

def search_arxiv(query: str):
    return f"Arxiv result for: {query}"