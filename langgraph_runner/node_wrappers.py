# --- langgraph_runner/node_wrappers.py ---
from langchain_core.runnables import RunnableLambda
import requests
import os

RUNPOD_URL = os.getenv("RUNPOD_URL", "")


class RemoteWhisperNode(RunnableLambda):
    def __init__(self, endpoint: str = RUNPOD_URL):
        self.endpoint = endpoint

    def invoke(self, input, config=None):
        files = {'file': input['audio']}
        res = requests.post(f"{self.endpoint}/transcribe", files=files)
        return {"text": res.json().get("text", "")}


class RemoteImageNode(RunnableLambda):
    def __init__(self, endpoint: str = RUNPOD_URL):
        self.endpoint = endpoint

    def invoke(self, input, config=None):
        files = {'file': input['image']}
        res = requests.post(f"{self.endpoint}/vision", files=files)
        return {"text": res.json().get("text", "")}
    