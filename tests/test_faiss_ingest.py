import os
import sys
import shutil
import importlib
import tempfile
import unittest

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

    def tearDown(self):
        shutil.rmtree(self.tmpdir)
        self.fs.store = None
        os.environ.pop("FAISS_INDEX_PATH", None)

    def test_ingest_updates_cache(self):
        text = "hello world"
        self.fe.ingest_text_to_faiss(text, namespace="image")
        result = self.fs.search_faiss("hello", namespace="image")
        self.assertIn("hello world", result)

if __name__ == "__main__":
    unittest.main()
