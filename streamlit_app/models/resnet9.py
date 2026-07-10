"""Re-exports the existing, already-tested ResNet9 + Grad-CAM implementation
from backend.models.resnet9 so the Streamlit app and the (still-deployed)
FastAPI backend share one definition instead of two copies drifting apart."""

from backend.models.resnet9 import (  # noqa: F401
    ResNet9,
    GradCAM,
    load_model,
    preprocess_image,
    normalize_orientation,
    predict,
    get_gradcam_pil,
)
