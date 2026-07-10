import base64
import io

from fastapi import APIRouter, File, HTTPException, UploadFile
from PIL import Image

from ..agent.tools import lookup_disease
from ..models.resnet9 import get_gradcam_pil, normalize_orientation, predict as run_predict, preprocess_image
from ..state import device, get_model

router = APIRouter()


def _pil_to_b64(pil_image) -> str:
    buf = io.BytesIO()
    pil_image.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode("ascii")


@router.post("/predict")
async def predict_endpoint(file: UploadFile = File(...)):
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Please upload an image file.")

    raw = await file.read()
    try:
        pil_image = Image.open(io.BytesIO(raw))
        pil_image.load()
        pil_image = normalize_orientation(pil_image)
    except Exception:
        raise HTTPException(status_code=400, detail="Could not read the uploaded image.")

    model, idx_to_class = get_model()
    tensor = preprocess_image(pil_image)
    class_name, confidence = run_predict(model, tensor, idx_to_class, device)

    class_to_idx = {v: k for k, v in idx_to_class.items()}
    orig, heatmap, overlay = get_gradcam_pil(
        model, tensor, class_to_idx[class_name], pil_image, device
    )

    kb_entry = lookup_disease(class_name)

    return {
        "class_name": class_name,
        "confidence": round(confidence, 2),
        "disease_name": kb_entry.get("disease_name", class_name),
        "affected_crop": kb_entry.get("affected_crop"),
        "is_healthy": kb_entry.get("is_healthy"),
        "symptoms": kb_entry.get("symptoms"),
        "precautionary_measures": kb_entry.get("precautionary_measures"),
        "original_image": _pil_to_b64(orig),
        "heatmap_image": _pil_to_b64(heatmap),
        "overlay_image": _pil_to_b64(overlay),
    }
