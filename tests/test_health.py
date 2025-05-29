# --- tests/test_health.py ---
import unittest
from app import config

# Mock keys
config.settings.OPENAI_API_KEY = "fake-key"
config.settings.PINECONE_API_KEY = "fake-key"
config.settings.LANGFUSE_PUBLIC_KEY = "fake-key"
config.settings.LANGFUSE_SECRET_KEY = "fake-key"


class BasicHealthTest(unittest.TestCase):
    def test_dummy(self):
        self.assertTrue(True)
