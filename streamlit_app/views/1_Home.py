import streamlit as st

from streamlit_app.core import ui
from streamlit_app.core.auth import current_user

user = current_user()

ui.render_html(
    """<div class="cd-card hero-card">
        <div style="font-size:3rem;">🌿</div>
        <h1>CropDoc AI</h1>
        <p class="hero-tagline">AI-powered plant disease diagnosis and intelligent crop assistant.</p>
        <p class="hero-sub">
            Upload a leaf image and receive an AI-powered diagnosis, treatment recommendations,
            prevention tips, and expert guidance within seconds.
        </p>
        <div class="hero-badges">
            <span class="cd-badge cd-badge-success">✓ AI Powered</span>
            <span class="cd-badge cd-badge-success">✓ Instant Diagnosis</span>
            <span class="cd-badge cd-badge-success">✓ OpenAI Vision</span>
            <span class="cd-badge cd-badge-success">✓ Smart Crop Assistant</span>
        </div>
    </div>"""
)

st.write("")
c1, c2, c3 = st.columns(3)
with c1:
    ui.render_html(ui.feature_card("🌿", "Disease Detection", "Drop a leaf photo and get an instant ResNet9 diagnosis with a Grad-CAM heatmap — analysis starts automatically."))
    if st.button("Go to Disease Detection", width="stretch"):
        st.switch_page("views/2_Detect_Disease.py")
with c2:
    ui.render_html(ui.feature_card("🤖", "AI Chat", "Continue the same conversation — ask about your diagnosis, treatment, or anything plant-health related."))
    if st.button("Go to AI Chat", width="stretch"):
        st.switch_page("views/3_AI_Chat.py")
with c3:
    ui.render_html(ui.feature_card("📊", "Dashboard", "Model evaluation charts and live usage stats from this deployment."))
    if st.button("Go to Dashboard", width="stretch"):
        st.switch_page("views/4_Dashboard.py")

st.write("")
st.markdown(f"Welcome back, **{user['username']}** 👋" if user else "")
