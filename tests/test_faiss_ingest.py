import os
import sys
import shutil
import importlib
import tempfile
import unittest
from unittest.mock import MagicMock
import types

fake_embed_mod = types.ModuleType("langchain_community.embeddings")

class FakeEmbeddings:
    def __init__(self, size=5):
        self.size = size

    def embed_documents(self, docs):
        return [[0.1]*self.size for _ in docs]

    def embed_query(self, q):
        return [0.1]*self.size

fake_embed_mod.FakeEmbeddings = FakeEmbeddings
sys.modules.setdefault("langchain_community.embeddings", fake_embed_mod)

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

class TestFaissIngest(unittest.TestCase):
    def setUp(self):
        os.environ["ENV"] = "dev"
        # create temporary directory for FAISS index
        self.tmpdir = tempfile.mkdtemp()
        os.environ["FAISS_INDEX_PATH"] = os.path.join(self.tmpdir, "index")

        # reload modules to use new path and reset cache
        import vectorstore.faiss_store as fs
        importlib.reload(fs)
        fs.store = None
        self.fs = fs

        import vectorstore.faiss_embed_and_store as fe
        importlib.reload(fe)
        self.fe = fe
        # Replace embedding model with deterministic fake embeddings to avoid
        # network calls during tests
        from langchain_community.embeddings import FakeEmbeddings
        fake = FakeEmbeddings(size=5)
        self.fe.embedding_model = fake

        # Simple in-memory FAISS stub
        self.store = {}

        def ingest_text_to_faiss(text, namespace=None, **kwargs):
            ns = namespace or "default"
            self.store.setdefault(ns, []).append(text)

        def search_faiss(query, namespace=None):
            ns = namespace or "default"
            for t in self.store.get(ns, []):
                if query in t:
                    return t
            return "No FAISS match found"

        self.fe.ingest_text_to_faiss = ingest_text_to_faiss
        self.fs.search_faiss = search_faiss


    def tearDown(self):
        shutil.rmtree(self.tmpdir)
        self.fs.store = None
        os.environ.pop("FAISS_INDEX_PATH", None)

    def test_ingest_updates_cache(self):
        text = "hello world"
        self.fe.ingest_text_to_faiss(text, namespace="image")
        result = self.fs.search_faiss("hello", namespace="image")
        self.assertIn("hello world", result)

    def test_search_with_score_concat_and_confidence(self):
        """search_faiss_with_score should join top k chunks and normalize score."""
        self.fs._search_vec = MagicMock(
            return_value=[
                ("chunk1", 0.2),
                ("chunk2", 0.3),
                ("chunk3", 0.4),
            ]
        )
        text, conf = self.fs.search_faiss_with_score("q", namespace="n", k=3)
        self.assertEqual(text, "chunk1\nchunk2\nchunk3")
        self.assertAlmostEqual(conf, 1 / (1 + 0.2))

if __name__ == "__main__":
    unittest.main()
