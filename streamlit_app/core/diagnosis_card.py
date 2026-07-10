"""Renders a diagnosis result as a card: badges, confidence bar, Grad-CAM
thumbnails, grounded symptoms/treatment (from the knowledge base) and the
Vision Agent's AI-generated explanation/causes/severity/fertilizer notes.
Used by both Disease Detection (right after analysis) and AI Chat (rendering
a past diagnosis turn) so it looks identical wherever it appears."""

import base64
import io

import streamlit as st

from . import ui

_SEVERITY_BADGE = {
    "Healthy": "success",
    "Mild": "mild",
    "Moderate": "moderate",
    "Severe": "severe",
}


def _b64_to_bytes(b64: str | None):
    return base64.b64decode(b64) if b64 else None


def pil_to_b64(pil_image) -> str:
    buf = io.BytesIO()
    pil_image.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode("ascii")


def render_diagnosis_card(meta: dict) -> None:
    severity = meta.get("severity", "Unknown")
    badge_kind = _SEVERITY_BADGE.get(severity, "info")

    ui.card_open()
    st.markdown(
        f"### {meta.get('disease_name', meta.get('class_name'))} &nbsp; {ui.badge(severity, badge_kind)}",
        unsafe_allow_html=True,
    )
    st.caption(f"Crop: **{meta.get('affected_crop', '—')}**")

    st.progress(min(max(meta.get("confidence", 0) / 100, 0.0), 1.0), text=f"Confidence: {meta.get('confidence', 0):.1f}%")

    orig = _b64_to_bytes(meta.get("original_b64"))
    heatmap = _b64_to_bytes(meta.get("heatmap_b64"))
    overlay = _b64_to_bytes(meta.get("overlay_b64"))
    if orig or heatmap or overlay:
        g1, g2, g3 = st.columns(3)
        if orig:
            g1.image(orig, caption="Original", width="stretch")
        if heatmap:
            g2.image(heatmap, caption="Heat Map", width="stretch")
        if overlay:
            g3.image(overlay, caption="Overlay", width="stretch")

    if meta.get("explanation"):
        st.markdown(f"**Why this diagnosis?** {meta['explanation']}")

    if meta.get("symptoms"):
        st.markdown("**Symptoms**")
        st.write(meta["symptoms"])

    col_a, col_b = st.columns(2)
    with col_a:
        if meta.get("causes"):
            st.markdown("**Likely causes**")
            st.write(meta["causes"])
        if meta.get("precautionary_measures"):
            st.markdown("**Prevention**")
            for m in meta["precautionary_measures"]:
                st.markdown(f"- {m}")
    with col_b:
        if meta.get("organic_treatment"):
            st.markdown("**Organic treatment**")
            st.write(meta["organic_treatment"])
        if meta.get("chemical_treatment"):
            st.markdown("**Chemical treatment**")
            st.write(meta["chemical_treatment"])
        if meta.get("fertilizer_recommendation"):
            st.markdown("**Fertilizer recommendation**")
            st.write(meta["fertilizer_recommendation"])

    if meta.get("expert_notes"):
        st.markdown(f"💡 **Expert tip:** {meta['expert_notes']}")

    if any(meta.get(k) for k in ("explanation", "causes", "organic_treatment", "chemical_treatment", "fertilizer_recommendation", "expert_notes")):
        st.markdown(
            "<div class='ai-generated-tag'>✨ Explanation, causes, fertilizer and expert notes are "
            "AI-generated guidance. Symptoms and prevention above are grounded in the CropDoc knowledge base.</div>",
            unsafe_allow_html=True,
        )
    ui.card_close()
