"""Shared chat-session sidebar: session list / New Conversation / document
upload / download / clear. Used identically by both Disease Detection and AI
Chat so a conversation started on one page continues seamlessly on the other
— they render the same underlying sqlite session, not two separate ones."""

import streamlit as st

from . import db
from ..rag import ingest, vector_store
from ..rag.loaders import SUPPORTED_EXTENSIONS


def ensure_active_session(user_id: int) -> int:
    if "active_session_id" not in st.session_state:
        sessions = db.list_chat_sessions(user_id)
        st.session_state["active_session_id"] = (
            sessions[0]["id"] if sessions else db.create_chat_session(user_id)
        )
    return st.session_state["active_session_id"]


def render(user: dict) -> int:
    """Renders the sidebar and returns the active session id."""
    session_id = ensure_active_session(user["id"])

    with st.sidebar:
        st.markdown("### 💬 Conversations")
        if st.button("🆕 New Conversation", width="stretch"):
            st.session_state["active_session_id"] = db.create_chat_session(user["id"])
            st.rerun()

        for s in db.list_chat_sessions(user["id"]):
            cols = st.columns([4, 1])
            label = ("📍 " if s["id"] == session_id else "") + s["title"]
            if cols[0].button(label, key=f"switch_{s['id']}", width="stretch"):
                st.session_state["active_session_id"] = s["id"]
                st.rerun()
            if cols[1].button("🗑️", key=f"del_{s['id']}"):
                db.delete_chat_session(s["id"])
                vector_store.delete_collection(vector_store.session_collection_name(s["id"]))
                if st.session_state.get("active_session_id") == s["id"]:
                    st.session_state.pop("active_session_id", None)
                st.rerun()

        st.markdown("---")
        st.markdown("### 📎 Add documents")
        st.caption("PDF, DOCX, TXT, MD, or CSV — used to ground answers in this conversation only.")
        uploaded_docs = st.file_uploader(
            "Upload documents",
            type=[ext.lstrip(".") for ext in SUPPORTED_EXTENSIONS],
            accept_multiple_files=True,
            label_visibility="collapsed",
            key=f"doc_uploader_{session_id}",
        )
        ingested_key = f"ingested_files_{session_id}"
        st.session_state.setdefault(ingested_key, set())
        for f in uploaded_docs or []:
            if f.name in st.session_state[ingested_key]:
                continue
            with st.spinner(f"Ingesting {f.name}..."):
                n_chunks = ingest.ingest_document(
                    vector_store.session_collection_name(session_id), f.name, f.getvalue()
                )
            st.session_state[ingested_key].add(f.name)
            st.success(f"{f.name}: {n_chunks} chunks indexed")

        st.markdown("---")
        messages = db.list_chat_messages(session_id)
        chat_md = "\n\n".join(f"**{m['role'].title()}:** {m['content']}" for m in messages)
        st.download_button(
            "⬇️ Download conversation",
            data=chat_md or "(empty conversation)",
            file_name=f"cropdoc_chat_{session_id}.md",
            mime="text/markdown",
            width="stretch",
            disabled=not messages,
        )
        if st.button("🧹 Clear conversation", width="stretch", disabled=not messages):
            db.clear_chat_messages(session_id)
            st.rerun()

    return session_id
