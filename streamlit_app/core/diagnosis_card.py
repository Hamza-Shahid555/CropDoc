"""Renders a diagnosis result as a card: badges, confidence bar, Grad-CAM
thumbnails, grounded symptoms/treatment (from the knowledge base) and the
Vision Agent's AI-generated explanation/causes/severity/fertilizer notes.
Used by both Disease Detection (right after analysis) and AI Chat (rendering
a past diagnosis turn) so it looks identical wherever it appears.

The AI's own direct-from-photo diagnosis is the primary result now (see
agents/vision_agent.py) — the specialist CNN's independent guess is shown
separately as a labeled secondary comparison, never as the headline, since
it's confined to 38 training classes and can be confidently wrong for
anything else."""

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

    if not meta.get("image_quality_ok", True):
        issue = meta.get("image_quality_issue")
        st.warning(
            f"📸 **Image quality issue:** {issue or 'This photo may be too unclear to diagnose confidently.'} "
            "Try a clearer, closer, well-lit photo for a more reliable diagnosis.",
            icon="📸",
        )

    st.markdown(
        f"### {meta.get('disease_name', meta.get('class_name'))} &nbsp; {ui.badge(severity, badge_kind)}",
        unsafe_allow_html=True,
    )
    st.caption(f"Crop: **{meta.get('affected_crop', '—')}**")

    source_label = {"claude": "Claude", "openai": "OpenAI", "cnn_only": "Specialist model (unverified)"}.get(
        meta.get("diagnosis_source"), "AI"
    )
    st.progress(
        min(max(meta.get("confidence", 0) / 100, 0.0), 1.0),
        text=f"{source_label} confidence: {meta.get('confidence', 0):.1f}%",
    )

    if meta.get("agreement_note"):
        st.info(f"🧭 {meta['agreement_note']}", icon="🧭")

    specialist_class = meta.get("specialist_model_class")
    if specialist_class:
        st.caption(
            f"🔬 Specialist CNN's independent guess (secondary, unverified): **{specialist_class}** "
            f"({meta.get('specialist_model_confidence', 0):.1f}% — its own certainty in that specific "
            "guess, not an accuracy score)"
        )

    openai_take = meta.get("openai_take")
    if openai_take:
        with st.expander(f"👁️ OpenAI's independent take: {openai_take.get('disease_name', '—')} ({openai_take.get('confidence', 0):.0f}%)"):
            st.caption(f"Crop it identified: **{openai_take.get('plant_species', '—')}**")
            if openai_take.get("symptoms"):
                st.markdown("**Symptoms it noted**")
                st.write(openai_take["symptoms"])
            oc1, oc2 = st.columns(2)
            with oc1:
                if openai_take.get("organic_treatment"):
                    st.markdown("**Organic treatment (OpenAI)**")
                    st.write(openai_take["organic_treatment"])
            with oc2:
                if openai_take.get("chemical_treatment"):
                    st.markdown("**Chemical treatment (OpenAI)**")
                    st.write(openai_take["chemical_treatment"])
            if openai_take.get("fertilizer_recommendation"):
                st.markdown("**Fertilizer recommendation (OpenAI)**")
                st.write(openai_take["fertilizer_recommendation"])

    orig = _b64_to_bytes(meta.get("original_b64"))
    heatmap = _b64_to_bytes(meta.get("heatmap_b64"))
    overlay = _b64_to_bytes(meta.get("overlay_b64"))
    if orig or heatmap or overlay:
        gradcam_label = meta.get("gradcam_class_label")
        if gradcam_label:
            if meta.get("gradcam_matched_kb"):
                st.caption(f"🔥 Heat map shows visual evidence for: **{gradcam_label}**")
            else:
                st.caption(
                    f"🔥 Heat map shows the specialist CNN's own focus area for its guess (**{gradcam_label}**) "
                    "— this may not correspond to the AI diagnosis above."
                )
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
            "<div class='ai-generated-tag'>✨ Diagnosed directly from the photo by AI. Symptoms/prevention "
            "are cross-referenced with the CropDoc knowledge base where a close match was found.</div>",
            unsafe_allow_html=True,
        )
    ui.card_close()
