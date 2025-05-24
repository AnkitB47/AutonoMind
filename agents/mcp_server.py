# --- agents/mcp_server.py ---
from agents import search_agent, rag_agent, translate_agent, plugin_loader
from langchain.schema.runnable import RunnableLambda
from langgraph.graph import StateGraph

def route_with_langgraph(query: str, lang: str = "en"):
    graph = StateGraph()

    def classify_and_route(x):
        if any(ext in x.lower() for ext in ["pdf", "document", "image"]):
            return rag_agent.handle_text(x)
        return search_agent.handle_query(x)

    def translate_output(x):
        return translate_agent.translate_response(x, lang)

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
