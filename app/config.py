# --- app/config.py ---
import os


class Settings:
    def __init__(self):
        self.env = os.getenv("ENV", "production").lower()

        self.OPENAI_API_KEY = self._get("OPENAI_API_KEY")
        self.PINECONE_API_KEY = self._get("PINECONE_API_KEY")
        self.PINECONE_ENVIRONMENT = self._get("PINECONE_ENVIRONMENT")
        self.PINECONE_INDEX_NAME = self._get("PINECONE_INDEX_NAME")
        self.GEMINI_API_KEY = self._get("GEMINI_API_KEY")
        self.RUNPOD_URL = os.getenv("RUNPOD_URL", "")
        self.USE_GPU = os.getenv("USE_GPU", "False").lower() == "true"

    def _get(self, key):
        value = os.getenv(key)
        if not value:
            if self.env != "production":
                print(f"⚠️  [DEV MODE] Using dummy value for `{key}`")
                return f"DUMMY_{key}"
            raise EnvironmentError(f"❌ Environment variable `{key}` is not set.")
        return value
