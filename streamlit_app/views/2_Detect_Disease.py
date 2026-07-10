import io

from PIL import Image
import streamlit as st

from backend.agent.tools import lookup_disease
from streamlit_app.agents.vision_agent import narrate_diagnosis
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
    status = st.status("🔍 Identifying plant species...", expanded=True)

    model, idx_to_class = get_model()
    tensor = preprocess_image(pil_image)
    status.update(label="🦠 Detecting disease...")
    class_name, confidence = run_predict(model, tensor, idx_to_class, DEVICE)
    class_to_idx = {v: k for k, v in idx_to_class.items()}
    orig, heatmap, overlay = get_gradcam_pil(model, tensor, class_to_idx[class_name], pil_image, DEVICE)

    status.update(label="📚 Searching knowledge base...")
    kb_entry = lookup_disease(class_name)

    status.update(label="🧠 Consulting AI expert..." if openai_configured() else "🧠 (Skipping AI narrative — no API key)")
    narrative = narrate_diagnosis(kb_entry, confidence) if openai_configured() else {}

    status.update(label="💡 Preparing recommendations...")
    meta = {
        "class_name": class_name,
        "disease_name": kb_entry.get("disease_name", class_name),
        "affected_crop": kb_entry.get("affected_crop"),
        "is_healthy": kb_entry.get("is_healthy"),
        "confidence": confidence,
        "symptoms": kb_entry.get("symptoms"),
        "precautionary_measures": kb_entry.get("precautionary_measures"),
        "original_b64": pil_to_b64(orig),
        "heatmap_b64": pil_to_b64(heatmap),
        "overlay_b64": pil_to_b64(overlay),
        **narrative,
    }

    db.log_prediction(
        user_id=user["id"],
        class_name=class_name,
        disease_name=meta["disease_name"],
        confidence=confidence,
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
