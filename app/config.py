# --- app/config.py ---
import os

class Settings:
    def __init__(self):
        self.env = os.getenv("ENV", "production").lower()

        # Required API Keys
        self.OPENAI_API_KEY       = self._get("OPENAI_API_KEY")
        self.PINECONE_API_KEY     = self._get("PINECONE_API_KEY")
        self.PINECONE_INDEX_HOST  = self._get("PINECONE_INDEX_HOST")
        self.PINECONE_INDEX_NAME  = self._get("PINECONE_INDEX_NAME")
        self.PINECONE_REGION      = self._get("PINECONE_REGION")
        self.LANGCHAIN_API_KEY    = self._get("LANGCHAIN_API_KEY")
        self.LANGCHAIN_PROJECT    = self._get("LANGCHAIN_PROJECT")
        self.GEMINI_API_KEY       = self._get("GEMINI_API_KEY")
        self.HF_TOKEN             = self._get("HF_TOKEN")
        self.GROQ_API_KEY         = self._get("GROQ_API_KEY")
        self.LANGFUSE_PUBLIC_KEY  = self._get("LANGFUSE_PUBLIC_KEY")
        self.LANGFUSE_SECRET_KEY  = self._get("LANGFUSE_SECRET_KEY")
        self.LANGFUSE_HOST        = self._get("LANGFUSE_HOST")
        self.SERPAPI_API_KEY      = self._get("SERPAPI_API_KEY")
        self.MODEL_PATH           = self._get("MODEL_PATH")
        self.FAISS_INDEX_PATH     = self._get("FAISS_INDEX_PATH")
        self.CLIP_FAISS_INDEX     = os.getenv("CLIP_FAISS_INDEX", "clip_faiss.index")

        repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        default_image_store = os.path.join(repo_root, "vectorstore", "image_store")
        self.IMAGE_STORE = os.getenv("IMAGE_STORE", default_image_store)

        self.RUNPOD_URL  = os.getenv("RUNPOD_URL", "")
        self.NEXT_PUBLIC_FASTAPI_URL = os.getenv("NEXT_PUBLIC_FASTAPI_URL", "")
        self.USE_GPU     = os.getenv("USE_GPU", "False").lower() == "true"

        # Auto-compute RunPod URL if the pod id is available
        if not self.RUNPOD_URL:
            pod_id = os.getenv("RUNPOD_POD_ID")
            if pod_id:
                self.RUNPOD_URL = f"https://{pod_id}-8000.proxy.runpod.net"

        if self.env == "production" and not (self.RUNPOD_URL or self.NEXT_PUBLIC_FASTAPI_URL):
            raise EnvironmentError("RUNPOD_URL or NEXT_PUBLIC_FASTAPI_URL must be set in production")

        # Safely parse MIN_CONFIDENCE, falling back to 0.4 if missing or empty
        raw = os.getenv("MIN_CONFIDENCE")
        try:
            self.MIN_RAG_CONFIDENCE = float(raw) if raw and raw.strip() else 0.4
        except ValueError:
            if self.env == "production":
                raise RuntimeError(f"Invalid MIN_CONFIDENCE: {raw!r}")
            self.MIN_RAG_CONFIDENCE = 0.4

        # CLIP threshold
        raw_clip = os.getenv("CLIP_MIN_CONFIDENCE")
        try:
            self.MIN_CLIP_CONFIDENCE = float(raw_clip) if raw_clip and raw_clip.strip() else 0.4
        except ValueError:
            if self.env == "production":
                raise RuntimeError(f"Invalid CLIP_MIN_CONFIDENCE: {raw_clip!r}")
            self.MIN_CLIP_CONFIDENCE = 0.4

    def _get(self, key: str) -> str:
        value = os.getenv(key)
        if not value:
            if self.env != "production":
                print(f"⚠️  [DEV MODE] Using dummy value for `{key}`")
                return f"DUMMY_{key}"
            raise EnvironmentError(f"❌ Environment variable `{key}` is not set.")
        return value

    def validate_api_keys(self) -> None:
        """Raise if any critical API key is dummy in production."""
        required = {
            "OPENAI_API_KEY":   self.OPENAI_API_KEY,
            "PINECONE_API_KEY": self.PINECONE_API_KEY,
            "GEMINI_API_KEY":   self.GEMINI_API_KEY,
        }
        for name, val in required.items():
            if not val or val.lower().startswith("dummy"):
                if self.env == "production":
                    raise EnvironmentError(f"{name} is not configured")
                else:
                    print(f"⚠️  {name} is not configured (dev mode)")
