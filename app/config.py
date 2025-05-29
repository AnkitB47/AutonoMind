# --- app/config.py ---
import os
from dotenv import load_dotenv

load_dotenv()  # Optional on local. Fly.io already sets env vars.

class Settings:
    def __init__(self):
        self.OPENAI_API_KEY = self._get("OPENAI_API_KEY")
        self.PINECONE_API_KEY = self._get("PINECONE_API_KEY")
        self.PINECONE_INDEX_NAME = self._get("PINECONE_INDEX_NAME")
        self.PINECONE_INDEX_HOST = self._get("PINECONE_INDEX_HOST")
        self.LANGFUSE_PUBLIC_KEY = self._get("LANGFUSE_PUBLIC_KEY")
        self.LANGFUSE_SECRET_KEY = self._get("LANGFUSE_SECRET_KEY")
        self.GEMINI_API_KEY = self._get("GEMINI_API_KEY")
        self.MODEL_PATH = os.getenv("MODEL_PATH", "DeepSeek")
        self.USE_GPU = os.getenv("USE_GPU", "False").lower() == "true"

    def _get(self, key: str):
        value = os.getenv(key)
        if value is None:
            raise EnvironmentError(f"❌ Environment variable `{key}` is not set.")
        return value

settings = Settings()
