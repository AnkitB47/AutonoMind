# --- agents/mcp_server.py ---
from typing import TypedDict
from langgraph.graph import StateGraph
from langchain_core.runnables import RunnableLambda
from agents import search_agent, rag_agent, translate_agent, plugin_loader
from app.config import Settings

settings = Settings()


# ✅ LangGraph input state type
class InputState(TypedDict):
    input: str
    lang: str
    session_id: str | None


# ✅ LangGraph routing logic
def route_with_langgraph(text: str, lang: str = "en", session_id: str | None = None):
    graph = StateGraph(InputState)

    # --- Node 1: Classify and route query ---
    def classify_and_route(state: InputState):
        query = state.get("input", "")
        session = state.get("session_id")
        lower = query.lower()

        if "image" in lower:
            result = rag_agent.handle_text(query, namespace="image", session_id=session)
        elif any(word in lower for word in ["pdf", "document"]):
            result = rag_agent.handle_text(query, namespace="pdf", session_id=session)
        else:
            result = search_agent.handle_query(query)
        return {"input": result, "lang": state.get("lang"), "session_id": session}

    # --- Node 2: Translate response ---
    def translate_output(state: InputState):
        return translate_agent.translate_response(state["input"], state["lang"])

    # --- Build LangGraph ---
    graph.add_node("route", RunnableLambda(classify_and_route))
    graph.add_node("translate", RunnableLambda(translate_output))

    for plugin in plugin_loader.load_plugins():
        if hasattr(plugin, "get_langgraph_node"):
            node_id, node_fn = plugin.get_langgraph_node()
            graph.add_node(node_id, node_fn)
            graph.add_edge("route", node_id)
            graph.add_edge(node_id, "translate")

    graph.set_entry_point("route")
    graph.set_finish_point("translate")

    return graph.compile().invoke({"input": text, "lang": lang, "session_id": session_id})
