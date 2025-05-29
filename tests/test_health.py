# --- tests/test_health.py ---
import os
os.environ["ENV"] = "dev"
os.environ["OPENAI_API_KEY"] = "dummy"
os.environ["PINECONE_API_KEY"] = "dummy"
os.environ["PINECONE_ENVIRONMENT"] = "dummy"
os.environ["PINECONE_INDEX_NAME"] = "dummy"
os.environ["GEMINI_API_KEY"] = "dummy"
os.environ["RUNPOD_URL"] = "http://localhost:8080"

import unittest

class BasicTest(unittest.TestCase):
    def test_sanity(self):
        self.assertTrue(True)
