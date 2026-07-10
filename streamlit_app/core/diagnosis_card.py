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


def _render_verification_banner(meta: dict) -> None:
    """Always-visible AI-verification result — never buried, since the vision model
    (38 fixed classes, no 'unknown' option) can be confidently wrong on its own."""
    agrees = meta.get("agrees_with_model")
    note = meta.get("agreement_note")

    if agrees is False:
        alt = meta.get("alternative_diagnosis")
        st.error(
            f"⚠️ **AI verification disagrees with the vision model.** {note or ''}"
            + (f" Possible alternative: **{alt}**" if alt else ""),
            icon="⚠️",
        )
    elif agrees is True:
        st.success(f"✅ AI verification agrees with this diagnosis. {note or ''}", icon="✅")
    elif note:
        st.warning(note, icon="ℹ️")

    if not meta.get("image_quality_ok", True):
        issue = meta.get("image_quality_issue")
        st.warning(
            f"📸 **Image quality issue:** {issue or 'This photo may be too unclear to diagnose confidently.'} "
            "Try a clearer, closer, well-lit photo for a more reliable diagnosis.",
            icon="📸",
        )


def render_diagnosis_card(meta: dict) -> None:
    severity = meta.get("severity", "Unknown")
    badge_kind = _SEVERITY_BADGE.get(severity, "info")
    disagrees = meta.get("agrees_with_model") is False

    ui.card_open()

    # Show the verification verdict FIRST — if it disagrees, the warning must be seen
    # before the (likely wrong) name/confidence, not read as a contradiction after them.
    _render_verification_banner(meta)

    if disagrees:
        st.markdown(f"##### 🔬 Vision model's guess (unverified): {meta.get('disease_name', meta.get('class_name'))}")
        st.caption(
            f"Crop it guessed: **{meta.get('affected_crop', '—')}** · "
            f"Model's own confidence in that guess: {meta.get('confidence', 0):.1f}% "
            "(this is the CNN's certainty in its own answer, not a verified accuracy score)"
        )
    else:
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

    if disagrees:
        st.warning(
            "The symptoms, causes, and treatment details below are grounded in the knowledge base entry "
            "for the vision model's guess above — which AI verification just flagged as likely wrong. "
            "Treat everything below as reference material for that guess only, not as advice for your actual plant.",
            icon="⚠️",
        )

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
