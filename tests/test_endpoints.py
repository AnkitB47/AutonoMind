import os
import sys
import unittest
from unittest.mock import patch
import types

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
os.environ.setdefault("ENV", "dev")
os.environ.setdefault("GEMINI_API_KEY", "testkey")
class DummyFAISS:
    def __init__(self, docs=None):
        self.docs = docs or []

    @classmethod
    def from_documents(cls, docs, embeddings):
        return cls(docs)

    @classmethod
    def load_local(cls, *a, **k):
        return cls()

    def similarity_search_with_score(self, query, k=5):
        return []

    def save_local(self, path):
        pass

mods = {
    "langchain_community.document_loaders": types.SimpleNamespace(PyPDFLoader=lambda *a, **k: None),
    "langchain": types.ModuleType("langchain"),
"langchain.chains": types.ModuleType("chains"),
"langchain.chains": types.SimpleNamespace(LLMChain=object),
"whisper": types.ModuleType("whisper"),
    "langchain_community.llms": types.SimpleNamespace(OpenAI=object),
    "langchain_core.prompts": types.SimpleNamespace(PromptTemplate=object),
    "google": types.ModuleType("google"),
    "google.generativeai": types.SimpleNamespace(
        configure=lambda **_: None,
        GenerativeModel=lambda *a, **k: types.SimpleNamespace(generate_content=lambda *a, **k: types.SimpleNamespace(text=""))
    ),
    "langchain_openai": types.SimpleNamespace(ChatOpenAI=object, OpenAIEmbeddings=lambda *a, **k: object()),
    "sentence_transformers": types.SimpleNamespace(SentenceTransformer=lambda *a, **k: types.SimpleNamespace(get_sentence_embedding_dimension=lambda:1, encode=lambda *a, **k: [0.0])),
    "faiss": types.SimpleNamespace(
        IndexFlatIP=lambda *a, **k: types.SimpleNamespace(d=1, search=lambda *a, **k: ([0.0], [[-1]])),
        IndexIDMap=lambda x: types.SimpleNamespace(d=1, ntotal=0, add_with_ids=lambda *a, **k: None, search=lambda *a, **k: ([0.0], [[-1]])),
        read_index=lambda *a, **k: types.SimpleNamespace(d=1, ntotal=0, add_with_ids=lambda *a, **k: None, search=lambda *a, **k: ([0.0], [[-1]])),
        write_index=lambda *a, **k: None,
    ),
    "langchain_community.vectorstores": types.SimpleNamespace(FAISS=DummyFAISS),
    "langchain_core.documents": types.SimpleNamespace(Document=lambda *a, **k: types.SimpleNamespace(page_content=a[0] if a else "", metadata=k.get("metadata", {}))),
    "langchain_text_splitters": types.SimpleNamespace(RecursiveCharacterTextSplitter=lambda *a, **k: object()),
    "fitz": types.ModuleType("fitz"),
    "pinecone": types.SimpleNamespace(Pinecone=lambda *a, **k: None),
    "langchain_pinecone": types.SimpleNamespace(PineconeVectorStore=object),
}
for n,m in mods.items():
    sys.modules.setdefault(n,m)

from fastapi.testclient import TestClient
from app.main import app
import base64

client = TestClient(app)

class EndpointStubs(unittest.TestCase):
    @patch("app.routes.chat.rag_agent.handle_query", return_value=("hi", 0.0, None))
    def test_chat_text(self, mock_hq):
        res = client.post("/chat", json={"session_id": "sid", "mode": "text", "content": "q"})
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.text.strip(), "hi")
        mock_hq.assert_called_with("text", "q", "sid", "en")
        self.assertEqual(res.headers.get("X-Session-ID"), "sid")
        self.assertIn("X-Confidence", res.headers)
        self.assertIn("X-Source", res.headers)

    @patch("app.routes.chat._transcribe", return_value="hello")
    @patch("app.routes.chat.rag_agent.handle_query", return_value=("ok", 0.0, None))
    def test_chat_voice(self, mock_hq, mock_trans):
        audio_b64 = base64.b64encode(b"123").decode()
        res = client.post("/chat", json={"session_id": "sid", "mode": "voice", "content": audio_b64})
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.text.strip(), "ok")
        mock_trans.assert_called()
        mock_hq.assert_called_with("text", "hello", "sid", "en")
        self.assertEqual(res.headers.get("X-Session-ID"), "sid")
        self.assertIn("X-Confidence", res.headers)
        self.assertIn("X-Source", res.headers)

    @patch("agents.rag_agent.search_pinecone_with_score", return_value=("", 0.0))
    @patch("agents.clip_faiss.search_text", return_value=[])
    @patch("agents.clip_faiss._load_model", return_value=(None, types.SimpleNamespace(projection_dim=1)))
    def test_clip_fallback(self, _1, _2, _3):
        ans, conf, src = __import__("agents.rag_agent", fromlist=["query_pdf_image"]).query_pdf_image("q", session_id="s")
        self.assertIsInstance(ans, str)

    @patch("models.whisper_runner.whisper")
    @patch("models.whisper_runner.os.remove")
    def test_transcribe_cleanup(self, mock_rm, mock_whisper):
        mock_whisper.load_model.return_value = type(
            "D", (), {"transcribe": lambda self, p: {"text": "ok"}}
        )()
        from models.whisper_runner import transcribe_audio

        text = transcribe_audio(b"123")
        self.assertEqual(text, "ok")
        self.assertTrue(mock_rm.called)

if __name__ == "__main__":
    unittest.main()
