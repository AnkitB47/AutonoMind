# --- app/pages/LangfuseDashboard.py ---
import streamlit as st

st.set_page_config(page_title="Langfuse Logs", layout="wide")
st.title("📊 Langfuse Monitoring Dashboard")

st.markdown("""
This is a placeholder. To embed a Langfuse dashboard:
- Go to your [Langfuse project dashboard](https://cloud.langfuse.com/projects)
- Click Share > Copy Embed Link
- Paste into iframe below
""")

langfuse_dashboard_url = st.text_input("🔗 Paste Langfuse iframe URL:", "https://cloud.langfuse.com/public/share/...iframe")

st.components.v1.iframe(src=langfuse_dashboard_url, height=800, scrolling=True)
