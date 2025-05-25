# --- agents/mcp_server.py ---
import os
from langgraph.graph import StateGraph
from langchain.schema.runnable import RunnableLambda
from agents import search_agent, rag_agent, translate_agent, plugin_loader
import langfuse

# Initialize Langfuse client
lf = langfuse.Langfuse(
    public_key=os.getenv("LANGFUSE_PUBLIC_KEY"),
    secret_key=os.getenv("LANGFUSE_SECRET_KEY"),
    host=os.getenv("LANGFUSE_HOST", "https://cloud.langfuse.com")
)

def route_with_langgraph(query: str, lang: str = "en"):
    trace = lf.trace(name="AutonoMind Agentic Query")
    trace.update(input={"query": query, "lang": lang})

    graph = StateGraph()

    def classify_and_route(x):
        text = x if isinstance(x, str) else x.get("input", "")
        trace.log_event(level="INFO", message="Classifying input")

        if any(ext in text.lower() for ext in ["pdf", "document", "image"]):
            trace.log_event(level="INFO", message="Dispatched to RAG Agent")
            return rag_agent.handle_text(text)
        else:
            trace.log_event(level="INFO", message="Dispatched to Search Agent")
            return search_agent.handle_query(text)

    def translate_output(x):
        trace.log_event(level="INFO", message="Translating response")
        result = translate_agent.translate_response(x, lang)
        trace.update(output={"translated_response": result})
        return result

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

    compiled = graph.compile()
    return compiled.invoke(query)
