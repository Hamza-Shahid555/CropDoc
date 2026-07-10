import base64
import itertools

import streamlit as st

from streamlit_app.agents import orchestrator
from streamlit_app.config import openai_configured
from streamlit_app.core import chat_sidebar, db, ui
from streamlit_app.core.auth import current_user
from streamlit_app.core.diagnosis_card import render_diagnosis_card

ui.page_header("AI Chat", "Ask CropDoc's assistant anything about a diagnosis or plant health.", "🤖")

if not openai_configured():
    st.warning("OPENAI_API_KEY is not configured — the chat assistant can't respond yet.")
    st.stop()

user = current_user()
session_id = chat_sidebar.render(user)

latest_diagnosis = db.get_latest_diagnosis(session_id)
if latest_diagnosis:
    ui.render_html(f"<div class='context-pill'>Context: {latest_diagnosis['disease_name']}</div>")
else:
    ui.render_html("<div class='context-pill'>No disease detected yet — ask anything, or upload a photo on Disease Detection.</div>")

messages = db.list_chat_messages(session_id)

if not messages:
    ui.render_html(
        """<div class="cd-card" style="text-align:center; padding:2rem 1.5rem;">
            <h2 style="margin:0;">👋 Welcome to CropDoc AI</h2>
            <p style="color:var(--cd-muted);">Upload a leaf image on Disease Detection, or ask me anything about plant diseases.</p>
        </div>"""
    )
    st.markdown("**Try asking:**")
    suggestions = [
        "🌿 Analyze my tomato leaf",
        "🍅 Why are my tomato leaves turning yellow?",
        "🌾 Recommend fertilizer",
        "🦠 Explain powdery mildew",
    ]
    cols = st.columns(len(suggestions))
    for col, suggestion in zip(cols, suggestions):
        if col.button(suggestion, width="stretch"):
            st.session_state["pending_prompt"] = suggestion.split(" ", 1)[1]

for msg in messages:
    with st.chat_message(msg["role"]):
        if msg.get("image_b64"):
            st.image(base64.b64decode(msg["image_b64"]), width="stretch")
        if msg["kind"] == "diagnosis" and msg.get("meta"):
            render_diagnosis_card(msg["meta"])
        else:
            st.markdown(msg["content"])

prompt = st.chat_input("Ask a question about crop diseases, treatment, or prevention...") or \
    st.session_state.pop("pending_prompt", None)

if prompt:
    session = next((s for s in db.list_chat_sessions(user["id"]) if s["id"] == session_id), None)
    if session and session["title"] == "New chat":
        db.rename_chat_session(session_id, prompt[:40] + ("..." if len(prompt) > 40 else ""))

    with st.chat_message("user"):
        st.markdown(prompt)

    detected_disease = latest_diagnosis["class_name"] if latest_diagnosis else None
    with st.chat_message("assistant"):
        gen = orchestrator.run_turn(session_id, prompt, detected_disease=detected_disease)
        with st.spinner("🧠 Consulting AI expert..."):
            try:
                first_chunk = next(gen)
            except StopIteration:
                first_chunk = None
        if first_chunk is not None:
            st.write_stream(itertools.chain([first_chunk], gen))
        else:
            st.write("(no response)")
    st.rerun()
