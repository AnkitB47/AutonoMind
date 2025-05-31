# --- app/routes/langgraph.py ---
import streamlit as st
from fastapi import APIRouter
from langgraph.graph import StateGraph
from langgraph_runner.node_wrappers import RemoteWhisperNode, RemoteImageNode
from langchain_core.runnables import RunnableLambda
from app.config import Settings

settings = Settings()
RUNPOD_URL = settings.RUNPOD_URL
router = APIRouter(prefix="/graph", tags=["langgraph"])


@router.post("/run")
async def run_graph(payload: dict):
    input_text = payload.get("input", "")
    lang = payload.get("lang", "en")
    input_type = payload.get("type", "text")

    builder = StateGraph()
    if input_type == "image":
        builder.add_node("image_proc", RemoteImageNode(RUNPOD_URL))
        builder.set_entry_point("image_proc")
    elif input_type == "audio":
        builder.add_node("audio_proc", RemoteWhisperNode(RUNPOD_URL))
        builder.set_entry_point("audio_proc")
    else:
        builder.add_node("echo", RunnableLambda(lambda x: {"text": x.get("input")}))
        builder.set_entry_point("echo")

    graph = builder.compile()
    return graph.invoke({"input": input_text, "lang": lang})


def render():
    st.subheader("🧠 LangGraph Controls")
    input_text = st.text_input("Input Text")
    input_type = st.radio("Input Type", ["text", "image", "audio"])
    lang = st.text_input("Language", value="en")

    if st.button("Run LangGraph"):
        result = run_graph({"input": input_text, "type": input_type, "lang": lang})
        st.json(result)
