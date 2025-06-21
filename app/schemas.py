from pydantic import BaseModel
from typing import Optional

class TextInput(BaseModel):
    query: str
    lang: str = "en"
    session_id: Optional[str] = None

class SearchInput(BaseModel):
    query: str
    lang: str = "en"
    session_id: Optional[str] = None

class ChatRequest(BaseModel):
    message: str
    lang: str = "en"
    session_id: str
