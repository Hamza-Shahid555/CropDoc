import io

from PIL import Image
import streamlit as st

from backend.agent.tools import match_disease_name
from streamlit_app.agents.vision_agent import diagnose_from_image
from streamlit_app.config import openai_configured
from streamlit_app.core import chat_sidebar, db, ui
from streamlit_app.core.auth import current_user
from streamlit_app.core.diagnosis_card import pil_to_b64, render_diagnosis_card
from streamlit_app.core.model_loader import DEVICE, get_model
from streamlit_app.models.resnet9 import get_gradcam_pil, normalize_orientation, predict as run_predict, preprocess_image

ui.page_header("Disease Detection", "Drop a leaf photo — diagnosis starts automatically.", "🌿")

user = current_user()
session_id = chat_sidebar.render(user)

ui.card_open()
uploaded = st.file_uploader(
    "📷 Drag & Drop Leaf Image — or click to upload (JPG, PNG)",
    type=["jpg", "jpeg", "png"],
    key=f"leaf_uploader_{session_id}",
)
ui.card_close()

processed_key = f"processed_upload_{session_id}"


def _run_pipeline(pil_image: Image.Image) -> dict:
    status = st.status("🧠 AI analyzing the photo directly...", expanded=True)

    model, idx_to_class = get_model()
    tensor = preprocess_image(pil_image)
    class_to_idx = {v: k for k, v in idx_to_class.items()}

    if not openai_configured():
        # No AI key: fall back to the specialist CNN alone, clearly flagged as such.
        status.update(label="🦠 No AI key — using specialist model only...")
        cnn_class, cnn_confidence = run_predict(model, tensor, idx_to_class, DEVICE)
        orig, heatmap, overlay = get_gradcam_pil(model, tensor, class_to_idx[cnn_class], pil_image, DEVICE)
        kb_entry = match_disease_name(cnn_class.replace("___", " ").replace("_", " ")) or {}
        meta = {
            "class_name": cnn_class,
            "disease_name": kb_entry.get("disease_name", cnn_class),
            "affected_crop": kb_entry.get("affected_crop"),
            "is_healthy": kb_entry.get("is_healthy"),
            "confidence": cnn_confidence,
            "symptoms": kb_entry.get("symptoms"),
            "precautionary_measures": kb_entry.get("precautionary_measures"),
            "explanation": (
                "No OPENAI_API_KEY configured, so this is the specialist CNN's own guess, unverified "
                "by AI. It only recognizes 38 specific crop-disease classes and can be confidently "
                "wrong for any other plant."
            ),
            "severity": "Unknown",
            "specialist_model_class": cnn_class.replace("___", " — ").replace("_", " "),
            "specialist_model_confidence": cnn_confidence,
            "gradcam_class_label": cnn_class.replace("___", " — ").replace("_", " "),
            "gradcam_matched_kb": True,
            "original_b64": pil_to_b64(orig),
            "heatmap_b64": pil_to_b64(heatmap),
            "overlay_b64": pil_to_b64(overlay),
        }
    else:
        img_buf = io.BytesIO()
        pil_image.convert("RGB").save(img_buf, format="JPEG", quality=90)
        diagnosis = diagnose_from_image(img_buf.getvalue())

        status.update(label="🔬 Cross-checking with specialist model...")
        cnn_class, cnn_confidence = run_predict(model, tensor, idx_to_class, DEVICE)

        status.update(label="📚 Grounding against knowledge base...")
        matched_kb = match_disease_name(diagnosis.get("disease_name", ""), crop_hint=diagnosis.get("plant_species"))
        if matched_kb:
            gradcam_class = matched_kb["class_name"]
            gradcam_label = matched_kb["disease_name"]
            gradcam_matched = True
        else:
            gradcam_class = cnn_class
            gradcam_label = cnn_class.replace("___", " — ").replace("_", " ")
            gradcam_matched = False
        orig, heatmap, overlay = get_gradcam_pil(model, tensor, class_to_idx[gradcam_class], pil_image, DEVICE)

        status.update(label="💡 Preparing recommendations...")
        meta = {
            "class_name": matched_kb["class_name"] if matched_kb else diagnosis.get("disease_name"),
            "disease_name": diagnosis.get("disease_name"),
            "affected_crop": diagnosis.get("plant_species"),
            "is_healthy": diagnosis.get("is_healthy"),
            "confidence": diagnosis.get("confidence", 0),
            "severity": diagnosis.get("severity"),
            "symptoms": diagnosis.get("symptoms") or (matched_kb or {}).get("symptoms"),
            "precautionary_measures": (matched_kb or {}).get("precautionary_measures"),
            "explanation": diagnosis.get("explanation"),
            "causes": diagnosis.get("causes"),
            "organic_treatment": diagnosis.get("organic_treatment"),
            "chemical_treatment": diagnosis.get("chemical_treatment"),
            "fertilizer_recommendation": diagnosis.get("fertilizer_recommendation"),
            "expert_notes": diagnosis.get("expert_notes"),
            "image_quality_ok": diagnosis.get("image_quality_ok", True),
            "image_quality_issue": diagnosis.get("image_quality_issue", ""),
            "specialist_model_class": cnn_class.replace("___", " — ").replace("_", " "),
            "specialist_model_confidence": cnn_confidence,
            "gradcam_class_label": gradcam_label,
            "gradcam_matched_kb": gradcam_matched,
            "original_b64": pil_to_b64(orig),
            "heatmap_b64": pil_to_b64(heatmap),
            "overlay_b64": pil_to_b64(overlay),
        }

    db.log_prediction(
        user_id=user["id"],
        class_name=meta["class_name"],
        disease_name=meta["disease_name"],
        confidence=meta["confidence"],
        is_healthy=meta["is_healthy"] or False,
    )

    status.update(label="✅ Analysis complete.", state="complete", expanded=False)
    return meta


if uploaded is not None:
    file_key = (uploaded.name, uploaded.size)
    if st.session_state.get(processed_key) != file_key:
        pil_image = normalize_orientation(Image.open(io.BytesIO(uploaded.getvalue())))

        try:
            db.add_chat_message(
                session_id, "user", "Uploaded a leaf photo for diagnosis.",
                image_b64=pil_to_b64(pil_image.convert("RGB")),
            )
            meta = _run_pipeline(pil_image)
            summary = (
                f"Diagnosis: {meta['disease_name']} ({meta['confidence']:.1f}% confidence, "
                f"severity: {meta.get('severity', 'Unknown')})."
            )
            db.add_diagnosis_message(session_id, summary, meta)
            st.session_state[processed_key] = file_key
            st.rerun()
        except FileNotFoundError as e:
            st.error(str(e))

latest = db.get_latest_diagnosis(session_id)
if latest:
    st.markdown("#### Latest diagnosis in this conversation")
    render_diagnosis_card(latest)
    if st.button("💬 Continue the conversation in AI Chat", width="stretch"):
        st.switch_page("views/3_AI_Chat.py")
elif uploaded is None:
    st.info("Upload a leaf photo above — analysis runs automatically, no button needed.")
