import streamlit as st

from streamlit_app.core import ui

ui.page_header("About", "The project behind CropDoc.", "ℹ️")

ui.card_open()
st.markdown(
    """
CropDoc is a final year project built to help farmers and gardeners get a fast, explainable
diagnosis of crop leaf diseases — and a straightforward way to ask follow-up questions about
what to do next.

**The vision model** is a ResNet9 convolutional network trained from scratch on a 38-class,
87,000+ image plant-disease dataset. Every prediction comes with a Grad-CAM heatmap so the
diagnosis isn't a black box — you can see which part of the leaf the model actually looked at.

**The assistant** is a small multi-agent system: a Planner decides whether a question needs
grounding in the disease knowledge base or your own uploaded documents, a Research agent runs
the retrieval, a Tool/API agent exposes internal lookups and a live weather forecast, a Memory
agent keeps track of the conversation, and a Response agent streams the final answer.

This application was originally built as a FastAPI + Next.js web app and was rebuilt as this
Streamlit application to consolidate the UI, chatbot, and document Q&A into a single deployable
product.
"""
)
ui.card_close()
