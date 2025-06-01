# --- agents/mcp_server.py ---
from typing import TypedDict
from langgraph.graph import StateGraph
from langchain.schema.runnable import RunnableLambda
from agents import search_agent, rag_agent, translate_agent, plugin_loader
import langfuse
from app.config import Settings

settings = Settings()


lf = langfuse.Langfuse(
    public_key=settings.LANGFUSE_PUBLIC_KEY,
    secret_key=settings.LANGFUSE_SECRET_KEY,
    host=settings.LANGFUSE_HOST
)


class InputState(TypedDict):
    input: str
    lang: str


def route_with_langgraph(text: str, lang: str = "en"):
    trace = lf.trace(name="AutonoMind Agentic Query")
    trace.update(input={"query": text, "lang": lang})

    graph = StateGraph(InputState)


    def classify_and_route(state: InputState):
        query = state.get("input", "")
        with trace.step("Classify & Route"):
            if any(word in query.lower() for word in ["pdf", "document", "image"]):
                result = rag_agent.handle_text(query)
            else:
                result = search_agent.handle_query(query)
        return {"input": result, "lang": state.get("lang")}


    def translate_output(state: InputState):
        with trace.step("Translate Output"):
            result = translate_agent.translate_response(state["input"], state["lang"])
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

    return graph.compile().invoke({"input": text, "lang": lang})
