import os
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from app.config import Settings


class ConfigTest(unittest.TestCase):
    def setUp(self):
        os.environ["ENV"] = "dev"
        self.required_keys = [
            "OPENAI_API_KEY",
            "PINECONE_API_KEY",
            "PINECONE_INDEX_HOST",
            "PINECONE_INDEX_NAME",
            "PINECONE_REGION",
            "LANGCHAIN_API_KEY",
            "LANGCHAIN_PROJECT",
            "GEMINI_API_KEY",
            "HF_TOKEN",
            "GROQ_API_KEY",
            "LANGFUSE_PUBLIC_KEY",
            "LANGFUSE_SECRET_KEY",
            "LANGFUSE_HOST",
            "SERPAPI_API_KEY",
            "MODEL_PATH",
            "FAISS_INDEX_PATH",
        ]
        for key in self.required_keys:
            os.environ.pop(key, None)

    def test_settings_defaults(self):
        settings = Settings()
        self.assertEqual(settings.env, "dev")
        for key in self.required_keys:
            value = getattr(settings, key)
            self.assertTrue(value.startswith("DUMMY_"))
