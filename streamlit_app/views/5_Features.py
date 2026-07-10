import streamlit as st

from streamlit_app.core import ui

ui.page_header("Features", "Everything CropDoc can do.", "✨")

features = [
    ("🔍", "Instant disease detection", "A ResNet9 CNN trained on 38 crop/disease classes classifies a leaf photo in under a second, with a confidence score."),
    ("🔥", "Grad-CAM explainability", "Every prediction ships with a visual heatmap showing exactly which part of the leaf drove the diagnosis — not a black box."),
    ("🧠", "Multi-agent assistant", "Planner, Research, Tool, API, Memory, and Response agents work together instead of one monolithic prompt: the planner decides what grounding is needed, tools fetch facts, and the response agent streams the answer."),
    ("📚", "Knowledge-grounded answers", "The assistant always checks the disease knowledge base (and any documents you upload) before answering symptom/treatment questions, instead of guessing."),
    ("📎", "Document Q&A (RAG)", "Upload PDFs, Word docs, text, markdown, or CSV files and ask questions grounded in your own material — isolated per chat session."),
    ("🌦️", "Weather-aware advice", "The API agent can pull a live 3-day forecast to inform spray timing and disease-spread risk in humid conditions."),
    ("💬", "Multiple chat sessions", "Keep separate conversations for different fields or crops, each with its own history and uploaded documents."),
    ("📊", "Usage dashboard", "See model evaluation charts from training alongside live usage stats for this deployment."),
    ("🔐", "Simple built-in accounts", "Lightweight username/password accounts — no external services required to try it out."),
]

cols = st.columns(3)
for i, (icon, title, body) in enumerate(features):
    with cols[i % 3]:
        ui.render_html(ui.feature_card(icon, title, body))
