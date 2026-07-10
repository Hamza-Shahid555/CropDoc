"""
CropDoc - ResNet9 architecture, checkpoint loading, inference, Grad-CAM.

Ported from local_inference.py so the FastAPI backend and the CLI script
share the exact same model definition and pre/post-processing.
"""

import cv2
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from PIL import Image, ImageOps
from torchvision import transforms


def conv_block(in_channels, out_channels, pool=False):
    layers = [
        nn.Conv2d(in_channels, out_channels, kernel_size=3, padding=1),
        nn.BatchNorm2d(out_channels),
        nn.ReLU(inplace=True),
    ]
    if pool:
        layers.append(nn.MaxPool2d(4))
    return nn.Sequential(*layers)


class ResNet9(nn.Module):
    def __init__(self, in_channels=3, num_classes=38):
        super().__init__()
        self.conv1 = conv_block(in_channels, 64)
        self.conv2 = conv_block(64, 128, pool=True)
        self.res1 = nn.Sequential(conv_block(128, 128), conv_block(128, 128))
        self.conv3 = conv_block(128, 256, pool=True)
        self.conv4 = conv_block(256, 512, pool=True)
        self.res2 = nn.Sequential(conv_block(512, 512), conv_block(512, 512))
        self.classifier = nn.Sequential(
            nn.MaxPool2d(4),
            nn.Flatten(),
            nn.Dropout(0.5),
            nn.Linear(512, num_classes),
        )

    def forward(self, xb):
        out = self.conv1(xb)
        out = self.conv2(out)
        out = self.res1(out) + out
        out = self.conv3(out)
        out = self.conv4(out)
        out = self.res2(out) + out
        out = self.classifier(out)
        return out


class GradCAM:
    """Gradient-weighted Class Activation Mapping for a specified target layer."""

    def __init__(self, model, target_layer):
        self.model = model
        self.gradients = None
        self.activations = None
        self._fwd = target_layer.register_forward_hook(self._save_activation)
        self._bwd = target_layer.register_full_backward_hook(self._save_gradient)

    def _save_activation(self, module, inp, output):
        self.activations = output.detach()

    def _save_gradient(self, module, grad_in, grad_out):
        self.gradients = grad_out[0].detach()

    def remove_hooks(self):
        self._fwd.remove()
        self._bwd.remove()

    def generate(self, input_tensor, class_idx):
        self.model.zero_grad()
        logits = self.model(input_tensor)
        logits[0, class_idx].backward()

        weights = self.gradients.mean(dim=[0, 2, 3])
        cam = self.activations[0]
        for i, w in enumerate(weights):
            cam[i] = cam[i] * w

        cam = cam.mean(dim=0).cpu().numpy()
        cam = np.maximum(cam, 0)
        if cam.max() > 0:
            cam /= cam.max()
        return cam


TRANSFORM = transforms.Compose([
    transforms.Resize(256),
    transforms.CenterCrop(256),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
])


def load_model(checkpoint_path, device):
    ckpt = torch.load(checkpoint_path, map_location=device)
    class_to_idx = ckpt["class_to_idx"]
    idx_to_class = {v: k for k, v in class_to_idx.items()}
    model = ResNet9(in_channels=3, num_classes=len(class_to_idx))
    model.load_state_dict(ckpt["model_state_dict"])
    model.to(device).eval()
    return model, idx_to_class


def preprocess_image(pil_image):
    """PIL image -> (1, 3, 256, 256) tensor.

    Expects `pil_image` to already be EXIF-orientation-corrected (see
    `normalize_orientation`) — done once by the caller so the tensor here and
    the Grad-CAM overlay in `get_gradcam_pil` agree on the same upright image.
    """
    return TRANSFORM(pil_image.convert("RGB")).unsqueeze(0)


def normalize_orientation(pil_image):
    """Applies EXIF-orientation correction: phone cameras store photos in the
    sensor's native (often sideways/upside-down) orientation and rely on an
    EXIF tag for viewers to rotate them for display. PIL doesn't apply that
    automatically, so without this the model — trained on upright leaf
    photos — would silently see a rotated image and misclassify it. Call
    this once right after opening an uploaded image, before anything else
    touches it."""
    return ImageOps.exif_transpose(pil_image)


def predict(model, tensor, idx_to_class, device):
    tensor = tensor.to(device)
    with torch.no_grad():
        probs = F.softmax(model(tensor), dim=1)
    conf, idx = probs.max(dim=1)
    return idx_to_class[idx.item()], conf.item() * 100.0


def get_gradcam_pil(model, tensor, class_idx, pil_image, device):
    """Return (original, heatmap, overlay) as 256x256 PIL Images."""
    t = tensor.clone().to(device).requires_grad_(True)
    gc = GradCAM(model, model.res2)
    try:
        model.train()
        cam = gc.generate(t, class_idx)
        model.eval()

        size = (256, 256)
        orig = pil_image.convert("RGB").resize(size)
        orig_bgr = cv2.cvtColor(np.array(orig), cv2.COLOR_RGB2BGR)

        cam_up = cv2.resize(cam, size)
        heatmap_bgr = cv2.applyColorMap(np.uint8(255 * cam_up), cv2.COLORMAP_JET)
        overlay_bgr = cv2.addWeighted(orig_bgr, 0.5, heatmap_bgr, 0.5, 0)

        def to_pil(bgr):
            return Image.fromarray(cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB))

        return orig, to_pil(heatmap_bgr), to_pil(overlay_bgr)
    finally:
        gc.remove_hooks()
