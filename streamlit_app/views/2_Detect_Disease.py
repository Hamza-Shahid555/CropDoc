import io
from concurrent.futures import ThreadPoolExecutor

from PIL import Image
import streamlit as st

from backend.agent.tools import lookup_disease, match_disease_name
from streamlit_app.agents import claude_agent, vision_agent
from streamlit_app.agents.claude_agent import synthesize_diagnosis
from streamlit_app.agents.vision_agent import diagnose_from_image
from streamlit_app.config import anthropic_configured, openai_configured
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


def _run_cnn(model, tensor, idx_to_class) -> dict:
    class_name, confidence = run_predict(model, tensor, idx_to_class, DEVICE)
    return {"class_name": class_name, "confidence": confidence}


def _cnn_only_meta(cnn: dict, model, tensor, class_to_idx, pil_image, reason: str) -> dict:
    """Fallback used when no AI key is configured, or every AI call failed."""
    orig, heatmap, overlay = get_gradcam_pil(model, tensor, class_to_idx[cnn["class_name"]], pil_image, DEVICE)
    # Exact lookup by the CNN's own class name — not the fuzzy match_disease_name(), which is
    # for grounding an LLM's free-text guess and requires a separately-known crop hint.
    kb_entry = lookup_disease(cnn["class_name"])
    if kb_entry.get("error"):
        kb_entry = {}
    label = cnn["class_name"].replace("___", " — ").replace("_", " ")
    return {
        "class_name": cnn["class_name"],
        "disease_name": kb_entry.get("disease_name", cnn["class_name"]),
        "affected_crop": kb_entry.get("affected_crop"),
        "is_healthy": kb_entry.get("is_healthy"),
        "confidence": cnn["confidence"],
        "symptoms": kb_entry.get("symptoms"),
        "precautionary_measures": kb_entry.get("precautionary_measures"),
        "explanation": (
            f"{reason} Showing the specialist CNN's own guess, unverified by AI. It only recognizes 38 "
            "specific crop-disease classes and can be confidently wrong for any other plant."
        ),
        "severity": "Unknown",
        "diagnosis_source": "cnn_only",
        "specialist_model_class": label,
        "specialist_model_confidence": cnn["confidence"],
        "gradcam_class_label": label,
        "gradcam_matched_kb": True,
        "original_b64": pil_to_b64(orig),
        "heatmap_b64": pil_to_b64(heatmap),
        "overlay_b64": pil_to_b64(overlay),
    }


def _run_pipeline(pil_image: Image.Image) -> dict:
    status = st.status("🔬 Running specialist model + AI vision analysis...", expanded=True)

    model, idx_to_class = get_model()
    tensor = preprocess_image(pil_image)
    class_to_idx = {v: k for k, v in idx_to_class.items()}

    use_openai = openai_configured()
    use_claude = anthropic_configured()

    if not use_openai and not use_claude:
        status.update(label="🦠 No AI key configured — using specialist model only...")
        cnn = _run_cnn(model, tensor, idx_to_class)
        meta = _cnn_only_meta(cnn, model, tensor, class_to_idx, pil_image, "No OPENAI_API_KEY or ANTHROPIC_API_KEY configured.")
        db.log_prediction(user_id=user["id"], class_name=meta["class_name"], disease_name=meta["disease_name"],
                           confidence=meta["confidence"], is_healthy=meta["is_healthy"] or False)
        status.update(label="✅ Analysis complete.", state="complete", expanded=False)
        return meta

    img_buf = io.BytesIO()
    pil_image.convert("RGB").save(img_buf, format="JPEG", quality=90)
    image_bytes = img_buf.getvalue()

    # CNN + OpenAI are independent of each other — run concurrently to save time.
    # (get_model()/preprocess_image() already ran on the main thread above; these
    # worker functions touch no Streamlit session state, so they're thread-safe.)
    with ThreadPoolExecutor(max_workers=2) as executor:
        cnn_future = executor.submit(_run_cnn, model, tensor, idx_to_class)
        openai_future = executor.submit(diagnose_from_image, image_bytes) if use_openai else None
        cnn = cnn_future.result()
        openai_diagnosis = openai_future.result() if openai_future else None

    final, final_source = None, None
    if use_claude:
        status.update(label="🧠 Claude reviewing and synthesizing the final diagnosis..." if use_openai else "🧠 Claude analyzing the photo...")
        cnn_context = {"class_name": cnn["class_name"].replace("___", " — ").replace("_", " "), "confidence": cnn["confidence"]}
        final = synthesize_diagnosis(image_bytes, cnn_context=cnn_context, openai_context=openai_diagnosis)
        final_source = "claude"

    if final is None and openai_diagnosis is not None:
        final, final_source = openai_diagnosis, "openai"

    if final is None:
        errors = []
        if use_openai and vision_agent.last_error:
            errors.append(f"OpenAI: {vision_agent.last_error}")
        if use_claude and claude_agent.last_error:
            errors.append(f"Claude: {claude_agent.last_error}")
        detail = " — ".join(errors) if errors else "No further detail was captured."
        meta = _cnn_only_meta(cnn, model, tensor, class_to_idx, pil_image, f"AI diagnosis failed: {detail}")
        db.log_prediction(user_id=user["id"], class_name=meta["class_name"], disease_name=meta["disease_name"],
                           confidence=meta["confidence"], is_healthy=meta["is_healthy"] or False)
        status.update(label="✅ Analysis complete (fallback).", state="complete", expanded=False)
        return meta

    status.update(label="📚 Grounding against knowledge base...")
    matched_kb = match_disease_name(final.get("disease_name", ""), crop_hint=final.get("plant_species"))
    if matched_kb:
        gradcam_class, gradcam_label, gradcam_matched = matched_kb["class_name"], matched_kb["disease_name"], True
    else:
        gradcam_class = cnn["class_name"]
        gradcam_label = cnn["class_name"].replace("___", " — ").replace("_", " ")
        gradcam_matched = False
    orig, heatmap, overlay = get_gradcam_pil(model, tensor, class_to_idx[gradcam_class], pil_image, DEVICE)

    status.update(label="💡 Preparing recommendations...")
    meta = {
        "class_name": matched_kb["class_name"] if matched_kb else final.get("disease_name"),
        "disease_name": final.get("disease_name"),
        "affected_crop": final.get("plant_species"),
        "is_healthy": final.get("is_healthy"),
        "confidence": final.get("confidence", 0),
        "severity": final.get("severity"),
        "symptoms": final.get("symptoms") or (matched_kb or {}).get("symptoms"),
        "precautionary_measures": (matched_kb or {}).get("precautionary_measures"),
        "explanation": final.get("explanation"),
        "causes": final.get("causes"),
        "organic_treatment": final.get("organic_treatment"),
        "chemical_treatment": final.get("chemical_treatment"),
        "fertilizer_recommendation": final.get("fertilizer_recommendation"),
        "expert_notes": final.get("expert_notes"),
        "image_quality_ok": final.get("image_quality_ok", True),
        "image_quality_issue": final.get("image_quality_issue", ""),
        "agreement_note": final.get("agreement_note", ""),
        "diagnosis_source": final_source,
        "specialist_model_class": cnn["class_name"].replace("___", " — ").replace("_", " "),
        "specialist_model_confidence": cnn["confidence"],
        "gradcam_class_label": gradcam_label,
        "gradcam_matched_kb": gradcam_matched,
        "original_b64": pil_to_b64(orig),
        "heatmap_b64": pil_to_b64(heatmap),
        "overlay_b64": pil_to_b64(overlay),
    }

    # Both LLMs ran: surface OpenAI's own independent take too, not just Claude's synthesis of it.
    if final_source == "claude" and openai_diagnosis is not None:
        meta["openai_take"] = {
            "plant_species": openai_diagnosis.get("plant_species"),
            "disease_name": "Healthy" if openai_diagnosis.get("is_healthy") else openai_diagnosis.get("disease_name"),
            "confidence": openai_diagnosis.get("confidence"),
            "symptoms": openai_diagnosis.get("symptoms"),
            "organic_treatment": openai_diagnosis.get("organic_treatment"),
            "chemical_treatment": openai_diagnosis.get("chemical_treatment"),
            "fertilizer_recommendation": openai_diagnosis.get("fertilizer_recommendation"),
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
