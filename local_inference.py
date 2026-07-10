"""
CropDoc - Local Inference Script
---------------------------------
Loads a trained ResNet9 checkpoint and runs inference on a single image.
Generates a Grad-CAM heatmap overlay saved alongside the input image.

Usage:
    python local_inference.py --image path/to/leaf.jpg
    python local_inference.py --image path/to/leaf.jpg --model path/to/cropdoc_resnet9.pth
"""

import argparse
import os
import sys

import cv2
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from PIL import Image
from torchvision import transforms


# ---------------------------------------------------------------------------
# ResNet9 architecture — must match the saved checkpoint exactly
# ---------------------------------------------------------------------------

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
        self.res1  = nn.Sequential(conv_block(128, 128), conv_block(128, 128))
        self.conv3 = conv_block(128, 256, pool=True)
        self.conv4 = conv_block(256, 512, pool=True)
        self.res2  = nn.Sequential(conv_block(512, 512), conv_block(512, 512))
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


# ---------------------------------------------------------------------------
# Grad-CAM targeting model.res2
# ---------------------------------------------------------------------------

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
        """Return a (H, W) numpy heatmap normalised to [0, 1]."""
        self.model.zero_grad()
        logits = self.model(input_tensor)
        logits[0, class_idx].backward()

        # Global average pool gradients over spatial dims
        weights = self.gradients.mean(dim=[0, 2, 3])  # (C,)
        cam = self.activations[0]                      # (C, H, W)
        for i, w in enumerate(weights):
            cam[i] = cam[i] * w

        cam = cam.mean(dim=0).cpu().numpy()            # (H, W)
        cam = np.maximum(cam, 0)
        if cam.max() > 0:
            cam /= cam.max()
        return cam

    def overlay(self, pil_image, cam, alpha=0.5):
        """Blend heatmap onto image; returns BGR numpy array for cv2.imwrite."""
        img_rgb = np.array(pil_image.convert("RGB"))
        img_bgr = cv2.cvtColor(img_rgb, cv2.COLOR_RGB2BGR)
        h, w = img_bgr.shape[:2]
        cam_resized = cv2.resize(cam, (w, h))
        heatmap = cv2.applyColorMap(np.uint8(255 * cam_resized), cv2.COLORMAP_JET)
        return cv2.addWeighted(img_bgr, 1 - alpha, heatmap, alpha, 0)


# ---------------------------------------------------------------------------
# Preprocessing
# ---------------------------------------------------------------------------

TRANSFORM = transforms.Compose([
    transforms.Resize(256),
    transforms.CenterCrop(256),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
])


# ---------------------------------------------------------------------------
# Core functions
# ---------------------------------------------------------------------------

def load_model(checkpoint_path, device):
    print(f"Loading model from {checkpoint_path} ...")
    ckpt = torch.load(checkpoint_path, map_location=device)
    class_to_idx = ckpt["class_to_idx"]
    idx_to_class = {v: k for k, v in class_to_idx.items()}
    model = ResNet9(in_channels=3, num_classes=len(class_to_idx))
    model.load_state_dict(ckpt["model_state_dict"])
    model.to(device).eval()
    val_acc = ckpt.get("val_accuracy")
    if val_acc is not None:
        print(f"Model loaded. Val accuracy from checkpoint: {val_acc:.2f}%")
    else:
        print("Model loaded.")
    return model, idx_to_class


def preprocess(image_path):
    img = Image.open(image_path).convert("RGB")
    return TRANSFORM(img).unsqueeze(0), img  # tensor (1,3,256,256), PIL image


def predict(model, tensor, idx_to_class, device):
    tensor = tensor.to(device)
    with torch.no_grad():
        probs = F.softmax(model(tensor), dim=1)
    conf, idx = probs.max(dim=1)
    return idx_to_class[idx.item()], conf.item() * 100.0


def save_gradcam(model, tensor, class_idx, pil_image, image_path, device):
    tensor = tensor.to(device).requires_grad_(True)
    grad_cam = GradCAM(model, model.res2)
    try:
        model.train()               # enable grad flow through BatchNorm / Dropout
        cam = grad_cam.generate(tensor, class_idx)
        model.eval()
        blended = grad_cam.overlay(pil_image, cam)
        stem = os.path.splitext(os.path.abspath(image_path))[0]
        out_path = f"{stem}_gradcam.png"
        cv2.imwrite(out_path, blended)
        print(f"Grad-CAM heatmap saved to: {out_path}")
    finally:
        grad_cam.remove_hooks()


def get_gradcam_pil(model, tensor, class_idx, pil_image, device):
    """Return (original, heatmap, overlay) as 256×256 PIL Images — no file I/O."""
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


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def parse_args():
    parser = argparse.ArgumentParser(description="CropDoc local inference")
    parser.add_argument("--image", required=True, help="Path to leaf image")
    parser.add_argument("--model", default="cropdoc_resnet9.pth",
                        help="Path to trained checkpoint (default: cropdoc_resnet9.pth)")
    return parser.parse_args()


def main():
    args = parse_args()

    if not os.path.isfile(args.image):
        print(f"[ERROR] Image not found: {args.image}", file=sys.stderr)
        sys.exit(1)
    if not os.path.isfile(args.model):
        print(f"[ERROR] Checkpoint not found: {args.model}", file=sys.stderr)
        sys.exit(1)

    device = torch.device("cpu")  # CPU fallback — no GPU required

    model, idx_to_class = load_model(args.model, device)

    print(f"Running inference on: {args.image}")
    tensor, pil_image = preprocess(args.image)

    predicted_class, confidence = predict(model, tensor, idx_to_class, device)
    print("---")
    print(f"Predicted disease : {predicted_class}")
    print(f"Confidence        : {confidence:.2f}%")
    print("---")

    # Build reverse map to get index for Grad-CAM
    class_to_idx = {v: k for k, v in idx_to_class.items()}
    save_gradcam(model, tensor, class_to_idx[predicted_class],
                 pil_image, args.image, device)


if __name__ == "__main__":
    main()
