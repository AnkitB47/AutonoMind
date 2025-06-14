import os
import sys
import unittest
from unittest.mock import patch
import types

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
os.environ.setdefault("ENV", "dev")
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
    "google.generativeai": types.SimpleNamespace(configure=lambda **_: None),
    "langchain_openai": types.SimpleNamespace(ChatOpenAI=object, OpenAIEmbeddings=lambda *a, **k: object()),
    "sentence_transformers": types.SimpleNamespace(SentenceTransformer=lambda *a, **k: types.SimpleNamespace(get_sentence_embedding_dimension=lambda:1, encode=lambda *a, **k: [0.0])),
    "faiss": types.SimpleNamespace(IndexFlatIP=lambda *a, **k: None, read_index=lambda *a, **k: None, write_index=lambda *a, **k: None),
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
    def test_clip_fallback(self, _1, _2):
        ans, conf, src = __import__("agents.rag_agent", fromlist=["query_pdf_image"]).query_pdf_image("q")
        self.assertIsInstance(ans, str)

if __name__ == "__main__":
    unittest.main()
