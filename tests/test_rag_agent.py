import os
import sys
import types
import unittest

os.environ["ENV"] = "dev"
from unittest.mock import patch, MagicMock

# Stub heavy deps
sys.modules.setdefault("transformers", MagicMock())
sys.modules.setdefault("whisper", MagicMock())
sys.modules.setdefault("pinecone", MagicMock())
sys.modules.setdefault("langchain_openai", MagicMock())
sys.modules.setdefault("langchain_pinecone", MagicMock())
sys.modules.setdefault("langchain", MagicMock())
sys.modules.setdefault("fitz", MagicMock())
langchain_core_mod = types.ModuleType("langchain_core")
langchain_core_mod.__path__ = []
langchain_core_mod.prompts = MagicMock()
langchain_core_mod.documents = MagicMock()
sys.modules.setdefault("langchain_core", langchain_core_mod)
sys.modules.setdefault("langchain_core.prompts", langchain_core_mod.prompts)
sys.modules.setdefault("langchain_core.documents", langchain_core_mod.documents)
sys.modules.setdefault("langchain.chains", MagicMock())
fake_comm = types.ModuleType("langchain_community")
fake_comm.llms = MagicMock()
fake_comm.vectorstores = MagicMock()
sys.modules.setdefault("langchain_community", fake_comm)
sys.modules.setdefault("langchain_community.llms", fake_comm.llms)
sys.modules.setdefault("langchain_community.vectorstores", fake_comm.vectorstores)
sys.modules.setdefault("langchain_community.document_loaders", MagicMock())
sys.modules.setdefault("langchain_community.embeddings", MagicMock())
fake_split = types.ModuleType("langchain_text_splitters")
fake_split.RecursiveCharacterTextSplitter = MagicMock()
sys.modules.setdefault("langchain_text_splitters", fake_split)
sys.modules.setdefault("langchain_text_splitters.RecursiveCharacterTextSplitter", fake_split.RecursiveCharacterTextSplitter)

# ensure modules can be imported
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from agents.rag_agent import handle_text

class TestRagAgent(unittest.TestCase):
    @patch("agents.rag_agent.search_agent.search_web")
    @patch("agents.rag_agent.search_faiss")
    @patch("agents.rag_agent.search_pinecone")
    def test_handle_text_web_fallback(self, mock_pc, mock_faiss, mock_web):
        mock_pc.return_value = "No match found"
        mock_faiss.return_value = "No FAISS match found"
        mock_web.return_value = "web summary"
        result = handle_text("test query")
        self.assertEqual(result, "web summary")
        mock_web.assert_called_once_with("test query")

if __name__ == "__main__":
    unittest.main()
