# --- app/config.py ---
import os

class Settings:
    def __init__(self):
        self.env = os.getenv("ENV", "production").lower()

        # Required API Keys
        self.OPENAI_API_KEY = self._get("OPENAI_API_KEY")
        self.PINECONE_API_KEY = self._get("PINECONE_API_KEY")
        self.PINECONE_INDEX_HOST = self._get("PINECONE_INDEX_HOST")
        self.PINECONE_INDEX_NAME = self._get("PINECONE_INDEX_NAME")
        self.PINECONE_REGION = self._get("PINECONE_REGION")
        self.LANGCHAIN_API_KEY = self._get("LANGCHAIN_API_KEY")
        self.LANGCHAIN_PROJECT = self._get("LANGCHAIN_PROJECT")
        self.GEMINI_API_KEY = self._get("GEMINI_API_KEY")
        self.HF_TOKEN = self._get("HF_TOKEN")
        self.GROQ_API_KEY = self._get("GROQ_API_KEY")
        self.LANGFUSE_PUBLIC_KEY = self._get("LANGFUSE_PUBLIC_KEY")
        self.LANGFUSE_SECRET_KEY = self._get("LANGFUSE_SECRET_KEY")
        self.LANGFUSE_HOST = self._get("LANGFUSE_HOST")
        self.SERPAPI_API_KEY = self._get("SERPAPI_API_KEY")
        self.MODEL_PATH = self._get("MODEL_PATH")
        self.FAISS_INDEX_PATH = self._get("FAISS_INDEX_PATH")
        self.IMAGE_STORE = os.path.abspath(
            os.getenv("IMAGE_STORE", default_image_store)
        )

        repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        default_image_store = os.path.join(repo_root, "vectorstore", "image_store")
        self.IMAGE_STORE = os.getenv("IMAGE_STORE", default_image_store)

        # Optional values
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
