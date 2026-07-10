"""Cached singleton loader for the ResNet9 checkpoint — st.cache_resource keeps
one copy of the model in memory across reruns/sessions instead of reloading
it on every script execution."""

import torch
import streamlit as st

from ..config import CHECKPOINT_PATH
from ..models.resnet9 import load_model

DEVICE = torch.device("cpu")


@st.cache_resource(show_spinner="Loading CropDoc vision model...")
def get_model():
    if not CHECKPOINT_PATH.is_file():
        raise FileNotFoundError(
            f"Checkpoint not found at {CHECKPOINT_PATH}. "
            "Copy cropdoc_resnet9.pth into the project root."
        )
    model, idx_to_class = load_model(str(CHECKPOINT_PATH), DEVICE)
    return model, idx_to_class
