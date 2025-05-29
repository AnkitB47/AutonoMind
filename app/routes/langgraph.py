# --- app/routes/langgraph.py ---
import os
from fastapi import APIRouter
from langgraph.graph import StateGraph
from langgraph_runner.node_wrappers import RemoteWhisperNode, RemoteImageNode
from app.config import Settings

# Load environment settings
settings = Settings()

router = APIRouter(prefix="/graph", tags=["langgraph"])
RUNPOD_URL = settings.RUNPOD_URL  


@router.post("/run")
async def run_graph(payload: dict):
    input_text = payload.get("input", "")
    lang = payload.get("lang", "en")
    input_type = payload.get("type", "text")  # text, image, audio

    builder = StateGraph()

    if input_type == "image":
        builder.add_node("image_proc", RemoteImageNode(RUNPOD_URL))
        builder.set_entry_point("image_proc")

    elif input_type == "audio":
        builder.add_node("audio_proc", RemoteWhisperNode(RUNPOD_URL))
        builder.set_entry_point("audio_proc")

    else:
        from langchain_core.runnables import RunnableLambda
        builder.add_node("echo", RunnableLambda(
            lambda x: {"text": x.get("input")}))
        builder.set_entry_point("echo")

    graph = builder.compile()
    return graph.invoke({"input": input_text, "lang": lang})
