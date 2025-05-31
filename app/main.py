# --- app/main.py ---

import streamlit as st
from app.routes import input_handler, file_upload, langgraph

# --- Streamlit App Config ---
st.set_page_config(
    page_title="AutonoMind AI",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Header UI ---
st.markdown("<h1 style='text-align: center;'>🤖 AutonoMind AI</h1>", unsafe_allow_html=True)
st.markdown("### Agentic Multimodal Assistant powered by LangGraph, Pinecone, FAISS & Gemini")
st.success("Upload a PDF/Image or ask a query via chat for instant answers!")

# --- Sidebar ---
with st.sidebar:
    st.image("https://i.imgur.com/EdkKp0g.png", caption="AutonoMind", use_column_width=True)
    st.markdown("---")
    st.subheader("📁 Tools")
    st.markdown("- PDF Search (Pinecone)")
    st.markdown("- Image Understanding (Gemini)")
    st.markdown("- Web Search (SerpAPI)")
    st.markdown("- Code/Math (Groq/DeepSeek)")
    st.markdown("- Translation (Gemini/OpenAI)")
    st.markdown("---")
    st.info("Built with ❤️ using LangChain + LangGraph")

# --- Routing Tabs ---
tabs = st.tabs(["📤 Upload", "💬 Chat", "📊 Logs"])

# --- File Upload Tab ---
with tabs[0]:
    file_upload.render()

# --- Chat Interface Tab ---
with tabs[1]:
    input_handler.render()

# --- Logs or Dev Tools ---
with tabs[2]:
    langgraph.render()

# --- Footer ---
st.markdown("---")
st.caption("© 2025 AutonoMind AI • Built by Ankit Bhardwaj")
