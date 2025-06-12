import os
import sys
import unittest
from io import BytesIO
from unittest.mock import patch, MagicMock
from PIL import Image

os.environ["ENV"] = "dev"

# Stub heavy deps before importing app
sys.modules.setdefault("whisper", MagicMock())
sys.modules.setdefault("transformers", MagicMock())
sys.modules.setdefault("tiktoken", MagicMock())
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.main_fastapi import app
from fastapi.testclient import TestClient
from app.routes.chat_api import chat_logic
from agents import rag_agent

class TestChatFlow(unittest.TestCase):
    def test_text_fallback_order(self):
        client = TestClient(app)
        with patch("agents.rag_agent.query_pdf_image", return_value=("",0.2,"pdf")) as qpi, \
             patch("agents.search_agent.search_arxiv", return_value="") as arxiv, \
             patch("agents.search_agent.search_semantic_scholar", return_value="") as sem, \
             patch("agents.search_agent.search_web", return_value="web") as web, \
             patch("agents.translate_agent.translate_response", side_effect=lambda a,l: a) as trans, \
             patch("agents.rag_agent.save_memory"):
            resp = client.post("/chat", json={"message": "q"})
            self.assertEqual(resp.json()["reply"], "web")
            arxiv.assert_called_once()
            sem.assert_called_once()
            web.assert_called_once()
            qpi.assert_called_once_with("q", session_id=None)

    def test_image_and_audio_once(self):
        client = TestClient(app)
        img = Image.new("RGB", (5,5))
        buf = BytesIO(); img.save(buf, format="PNG")
        with patch("app.routes.chat_api.extract_image_text", return_value="ocr") as ocr, \
             patch("app.routes.chat_api.transcribe_audio") as tr, \
             patch("agents.rag_agent.query_pdf_image", return_value=("ans",0.7,"image")) as qpi, \
             patch("agents.translate_agent.translate_response", side_effect=lambda a,l:a), \
             patch("agents.rag_agent.save_memory"):
            resp = client.post("/chat", files={"file": ("i.png", buf.getvalue(), "image/png")})
            self.assertEqual(resp.json()["reply"], "ans")
            ocr.assert_called_once()
            tr.assert_not_called()
            qpi.assert_called_once_with("ocr", session_id=None)

        with patch("app.routes.chat_api.transcribe_audio", return_value="voice") as tr, \
             patch("app.routes.chat_api.extract_image_text") as ocr, \
             patch("agents.rag_agent.query_pdf_image", return_value=("ans",0.7,"pdf")) as qpi, \
             patch("agents.translate_agent.translate_response", side_effect=lambda a,l:a), \
             patch("agents.rag_agent.save_memory"):
            resp = client.post("/chat", files={"file": ("a.wav", b"data", "audio/wav")})
            self.assertEqual(resp.json()["reply"], "ans")
            tr.assert_called_once()
            ocr.assert_not_called()
            qpi.assert_called_once_with("voice", session_id=None)

    def test_memory_roundtrip(self):
        rag_agent.memory_cache.clear()
        with patch("agents.rag_agent.ingest_text_to_faiss"):
            rag_agent.save_memory("Q1", "A1", session_id="s")
            rag_agent.save_memory("Q2", "A2", session_id="s")
        mem = rag_agent.load_memory("s", limit=1)
        self.assertEqual(mem, ["Q: Q2\nA: A2"])

if __name__ == "__main__":
    unittest.main()
