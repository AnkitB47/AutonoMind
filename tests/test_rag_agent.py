import os
import sys
import unittest
from unittest.mock import patch, MagicMock

# Stub heavy deps
sys.modules.setdefault("transformers", MagicMock())
sys.modules.setdefault("whisper", MagicMock())

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
