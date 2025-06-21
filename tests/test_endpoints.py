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

client = TestClient(app)

class EndpointStubs(unittest.TestCase):
    @patch("app.routes.chat.extract_image_text", return_value="ok")
    def test_ocr_stub(self, _):
        res = client.post("/ocr", files={"file": ("x.png", b"1", "image/png")})
        self.assertEqual(res.status_code, 200)
        self.assertIn("text", res.json())

    @patch("app.routes.chat.transcribe_audio", return_value="hi")
    def test_transcribe_stub(self, _):
        res = client.post("/transcribe", files={"file": ("a.wav", b"1", "audio/wav")})
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["text"], "hi")

    @patch("agents.rag_agent.search_pinecone_with_score", return_value=("", 0.0))
    @patch("agents.clip_faiss.search_text", return_value=[])
    @patch("agents.clip_faiss._load_model", return_value=(None, types.SimpleNamespace(projection_dim=1)))
    def test_clip_fallback(self, _1, _2, _3):
        ans, conf, src = __import__("agents.rag_agent", fromlist=["query_pdf_image"]).query_pdf_image("q", session_id="s")
        self.assertIsInstance(ans, str)

    @patch("app.routes.input_handler.chat_logic", return_value=("ok", 0.0))
    @patch("app.routes.input_handler.is_runpod_live", return_value=False)
    @patch("app.routes.input_handler.os.remove")
    @patch("app.routes.input_handler.extract_image_text", return_value="txt")
    def test_image_tempfile(self, mock_extract, mock_rm, _live, _chat):
        res = client.post(
            "/input/image",
            files={"file": ("img.png", b"123", "image/png")},
        )
        self.assertEqual(res.status_code, 200)
        path = mock_extract.call_args[0][0]
        mock_rm.assert_called_with(path)

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
