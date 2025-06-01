# --- agents/mcp_server.py ---
import os
from typing import TypedDict
from langgraph.graph import StateGraph
from langchain.schema.runnable import RunnableLambda
from agents import search_agent, rag_agent, translate_agent, plugin_loader
import langfuse
from app.config import Settings

# Load environment settings
settings = Settings()


# Initialize Langfuse client
lf = langfuse.Langfuse(
    public_key=settings.LANGFUSE_PUBLIC_KEY,
    secret_key=settings.LANGFUSE_SECRET_KEY,
    host=settings.LANGFUSE_HOST
)


# Define the input schema for LangGraph
class InputState(TypedDict):
    input: str
    lang: str


def route_with_langgraph(text: str, lang: str = "en"):
    trace = lf.trace(name="AutonoMind Agentic Query")
    trace.update(input={"query": text, "lang": lang})

    graph = StateGraph(InputState)


    def classify_and_route(state: InputState):
        query = state.get("input", "")
        trace.log_event(level="INFO", message="Classifying input")

        if any(word in query.lower() for word in ["pdf", "document", "image"]):
            trace.log_event(level="INFO", message="Dispatched to RAG Agent")
            return {"input": rag_agent.handle_text(query), "lang": state.get("lang")}
        else:
            trace.log_event(level="INFO", message="Dispatched to Search Agent")
            return {"input": search_agent.handle_query(query), "lang": state.get("lang")}


    def translate_output(state: InputState):
        trace.log_event(level="INFO", message="Translating response")
        result = translate_agent.translate_response(state["input"], state["lang"])
        trace.update(output={"translated_response": result})
        return result

    graph.add_node("route", RunnableLambda(classify_and_route))
    graph.add_node("translate", RunnableLambda(translate_output))

    # Add any dynamic plugin nodes
    for plugin in plugin_loader.load_plugins():
        if hasattr(plugin, "get_langgraph_node"):
            node_id, node_fn = plugin.get_langgraph_node()
            graph.add_node(node_id, node_fn)
            graph.add_edge("route", node_id)
            graph.add_edge(node_id, "translate")

    graph.set_entry_point("route")
    graph.set_finish_point("translate")

    compiled = graph.compile()
    return compiled.invoke({"input": text, "lang": lang})
