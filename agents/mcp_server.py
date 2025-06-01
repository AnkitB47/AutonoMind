# --- agents/mcp_server.py ---

from typing import TypedDict
from langgraph.graph import StateGraph
from langchain.schema.runnable import RunnableLambda
from agents import search_agent, rag_agent, translate_agent, plugin_loader
from app.config import Settings

from langfuse import Langfuse

settings = Settings()

# ✅ Langfuse instance
lf = Langfuse(
    public_key=settings.LANGFUSE_PUBLIC_KEY,
    secret_key=settings.LANGFUSE_SECRET_KEY,
    host=settings.LANGFUSE_HOST
)


# ✅ LangGraph input schema
class InputState(TypedDict):
    input: str
    lang: str


def route_with_langgraph(text: str, lang: str = "en"):
    trace: Trace = lf.trace(name="AutonoMind Agentic Query")
    trace.update(input={"query": text, "lang": lang})

    graph = StateGraph(InputState)


    # ✅ Node 1: Classify and route
    def classify_and_route(state: InputState):
        query = state.get("input", "")
        trace.log_event(level="INFO", message="Step: Classify & Route")
        trace.update(input={"user_query": query})

        if any(word in query.lower() for word in ["pdf", "document", "image"]):
            trace.log_event(level="INFO", message="→ RAG Agent selected")
            result = rag_agent.handle_text(query)
        else:
            trace.log_event(level="INFO", message="→ Search Agent selected")
            result = search_agent.handle_query(query)

        return {"input": result, "lang": state.get("lang")}


    # ✅ Node 2: Translate final response
    def translate_output(state: InputState):
        trace.log_event(level="INFO", message="Step: Translate Output")
        result = translate_agent.translate_response(state["input"], state["lang"])
        trace.update(output={"translated_response": result})
        return result

    # ✅ LangGraph Wiring
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

    return graph.compile().invoke({"input": text, "lang": lang})
