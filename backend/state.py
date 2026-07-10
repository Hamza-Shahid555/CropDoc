"""Process-wide singletons: the loaded vision model and the resolved class map.

Loaded lazily on first /predict call so `uvicorn backend.main:app` starts
instantly and OPENAI_API_KEY / model files are only required when actually used.
"""

from pathlib import Path

import torch

from .models.resnet9 import load_model

BASE_DIR = Path(__file__).resolve().parent.parent  # "New folder" project root
CHECKPOINT_PATH = BASE_DIR / "cropdoc_resnet9.pth"
KB_PATH = BASE_DIR / "disease_knowledge_base.json"

device = torch.device("cpu")

_model = None
_idx_to_class = None


def get_model():
    global _model, _idx_to_class
    if _model is None:
        if not CHECKPOINT_PATH.is_file():
            raise FileNotFoundError(
                f"Checkpoint not found at {CHECKPOINT_PATH}. "
                "Copy cropdoc_resnet9.pth into the project root."
            )
        _model, _idx_to_class = load_model(str(CHECKPOINT_PATH), device)
    return _model, _idx_to_class
