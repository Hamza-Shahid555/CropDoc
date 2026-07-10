import streamlit as st

from streamlit_app.config import OPENAI_CHAT_MODEL, OPENAI_EMBEDDING_MODEL, openai_configured
from streamlit_app.core import db, ui
from streamlit_app.core.auth import current_user
from streamlit_app.rag import ingest, vector_store

ui.page_header("Settings", "Profile and app configuration.", "⚙️")

user = current_user()
user_row = db.get_user_by_username(user["username"])

ui.card_open()
st.markdown("### Profile")
st.write(f"**Username:** {user_row['username']}")
st.write(f"**Member since:** {user_row['created_at'][:10]}")
ui.card_close()

ui.card_open()
st.markdown("### AI configuration")
status = ui.badge("Connected", "success") if openai_configured() else ui.badge("Not configured", "danger")
ui.render_html(f"**OpenAI API key:** {status}")
st.write(f"**Chat model:** `{OPENAI_CHAT_MODEL}`")
st.write(f"**Embedding model:** `{OPENAI_EMBEDDING_MODEL}`")
if not openai_configured():
    st.caption("Set OPENAI_API_KEY in backend/.env or a root .env file to enable the AI Chat page.")
ui.card_close()

ui.card_open()
st.markdown("### Knowledge base index")
kb_count = vector_store.get_collection(vector_store.KB_COLLECTION).count()
st.write(f"**Indexed disease knowledge base entries:** {kb_count}")
if st.button("🔄 Rebuild knowledge base index"):
    with st.spinner("Rebuilding..."):
        vector_store.delete_collection(vector_store.KB_COLLECTION)
        n = ingest.ingest_kb_if_empty()
    st.success(f"Rebuilt — {n} entries indexed.")
ui.card_close()

ui.card_open()
st.markdown("### Your chat sessions & documents")
sessions = db.list_chat_sessions(user["id"])
if not sessions:
    st.caption("No chat sessions yet.")
else:
    for s in sessions:
        coll = vector_store.get_collection(vector_store.session_collection_name(s["id"]))
        n_msgs = len(db.list_chat_messages(s["id"]))
        st.write(f"- **{s['title']}** — {n_msgs} messages, {coll.count()} document chunks indexed")
    if st.button("🧹 Clear all uploaded documents (keeps chat history)"):
        for s in sessions:
            vector_store.delete_collection(vector_store.session_collection_name(s["id"]))
        st.success("Cleared uploaded documents from all sessions.")
        st.rerun()
ui.card_close()
