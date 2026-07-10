"""CropDoc — entrypoint: page config, auth gate, sidebar, navigation shell."""

import sys
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # allow `import backend.*`

from streamlit_app.config import APP_NAME, APP_TAGLINE, openai_configured
from streamlit_app.core import auth, db, ui

st.set_page_config(page_title=APP_NAME, page_icon="🌿", layout="wide")

db.init_db()
auth.ensure_demo_user()
ui.inject_css()

user = auth.require_login()  # st.stop()s here until logged in

VIEWS_DIR = Path(__file__).resolve().parent / "views"

pages = {
    "": [
        st.Page(VIEWS_DIR / "1_Home.py", title="Home", icon="🏠", default=True),
    ],
    "Diagnose": [
        st.Page(VIEWS_DIR / "2_Detect_Disease.py", title="Disease Detection", icon="🌿"),
        st.Page(VIEWS_DIR / "3_AI_Chat.py", title="AI Chat", icon="🤖"),
        st.Page(VIEWS_DIR / "4_Dashboard.py", title="Dashboard", icon="📊"),
    ],
    "About": [
        st.Page(VIEWS_DIR / "5_Features.py", title="Features", icon="✨"),
        st.Page(VIEWS_DIR / "6_Documentation.py", title="Documentation", icon="📖"),
        st.Page(VIEWS_DIR / "7_About.py", title="About", icon="ℹ️"),
        st.Page(VIEWS_DIR / "8_Contact.py", title="Contact", icon="✉️"),
    ],
    "Account": [
        st.Page(VIEWS_DIR / "9_Settings.py", title="Settings", icon="⚙️"),
    ],
}

with st.sidebar:
    st.markdown(f"### 🌿 {APP_NAME}")
    st.caption(APP_TAGLINE)
    st.markdown("---")
    st.markdown(f"**{user['username']}**")
    if not openai_configured():
        st.warning("OPENAI_API_KEY not set — AI Chat will be limited.", icon="⚠️")
    if st.button("Log out", width="stretch"):
        auth.logout()
        st.rerun()
    st.markdown("---")

nav = st.navigation(pages)
nav.run()
