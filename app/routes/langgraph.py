# --- app/routes/langgraph.py ---
from fastapi import APIRouter
from agents import mcp_server

router = APIRouter(prefix="/graph", tags=["langgraph"])

@router.post("/run")
async def run_graph(payload: dict):
    input_text = payload.get("input")
    lang = payload.get("lang", "en")
    result = mcp_server.route_with_langgraph(input_text, lang)
    return {"response": result}