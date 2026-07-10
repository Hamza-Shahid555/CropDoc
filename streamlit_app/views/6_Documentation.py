import streamlit as st

from streamlit_app.config import BASE_DIR
from streamlit_app.core import ui

ui.page_header("Documentation", "How CropDoc works, under the hood.", "📚")

docs = [
    ("Architecture", "ARCHITECTURE.md"),
    ("Installation", "INSTALLATION.md"),
    ("Project structure", "PROJECT_STRUCTURE.md"),
    ("Agent & tool reference", "API_DOCUMENTATION.md"),
    ("Security", "SECURITY.md"),
    ("Roadmap", "ROADMAP.md"),
]

available = [(label, BASE_DIR / fname) for label, fname in docs if (BASE_DIR / fname).is_file()]

if not available:
    st.info("Documentation files haven't been generated yet.")
else:
    tabs = st.tabs([label for label, _ in available])
    for tab, (label, path) in zip(tabs, available):
        with tab:
            st.markdown(path.read_text(encoding="utf-8"))
