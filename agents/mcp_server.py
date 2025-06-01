# --- agents/mcp_server.py ---
from typing import TypedDict
from langgraph.graph import StateGraph
from langchain.schema.runnable import RunnableLambda
from agents import search_agent, rag_agent, translate_agent, plugin_loader
from app.config import Settings
from langfuse import Langfuse

settings = Settings()


lf = Langfuse(
    public_key=settings.LANGFUSE_PUBLIC_KEY,
    secret_key=settings.LANGFUSE_SECRET_KEY,
    host=settings.LANGFUSE_HOST
)


class InputState(TypedDict):
    input: str
    lang: str


def route_with_langgraph(text: str, lang: str = "en"):
    trace = lf.trace(name="AutonoMind Agentic Query")
    trace.input = {"query": text, "lang": lang}

    graph = StateGraph(InputState)


    def classify_and_route(state: InputState):
        query = state.get("input", "")
        with trace.span() as span:
            span.name = "Classify & Route"
            span.input = {"user_query": query}

            if any(word in query.lower() for word in ["pdf", "document", "image"]):
                span.output = {"agent": "RAG"}
                result = rag_agent.handle_text(query)
            else:
                span.output = {"agent": "Search"}
                result = search_agent.handle_query(query)

        return {"input": result, "lang": state.get("lang")}


    def translate_output(state: InputState):
        with trace.span() as span:
            span.name = "Translate Output"
            result = translate_agent.translate_response(state["input"], state["lang"])
            span.output = {"translated_response": result}
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

    return graph.compile().invoke({"input": text, "lang": lang})
