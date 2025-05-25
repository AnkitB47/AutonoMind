# --- app/config.py ---
import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
    LANGFUSE_PUBLIC_KEY = os.getenv("LANGFUSE_PUBLIC_KEY")
    LANGFUSE_SECRET_KEY = os.getenv("LANGFUSE_SECRET_KEY")
    MODEL_PATH = os.getenv("MODEL_PATH", "DeepSeek")
    USE_GPU = os.getenv("USE_GPU", "False") == "True"


settings = Settings()
