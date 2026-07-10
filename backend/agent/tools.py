"""Tools the chat agent can call. Keeping the knowledge base behind a tool
(instead of pasting it into the prompt) is what makes the agent "agentic":
the model decides when it needs grounded facts and asks for them."""

import json
from difflib import SequenceMatcher
from pathlib import Path

KB_PATH = Path(__file__).resolve().parent.parent.parent / "disease_knowledge_base.json"

with open(KB_PATH, encoding="utf-8") as f:
    _KB = json.load(f)

_BY_CLASS_NAME = {entry["class_name"]: entry for entry in _KB}


def lookup_disease(class_name: str) -> dict:
    """Return the knowledge-base entry for a disease class, or a not-found marker."""
    entry = _BY_CLASS_NAME.get(class_name)
    if entry is None:
        # fall back to a loose match in case the model passes a human-readable name
        for e in _KB:
            if class_name.lower() in e["disease_name"].lower():
                return e
        return {"error": f"No knowledge base entry found for '{class_name}'"}
    return entry


def match_disease_name(free_text_name: str, crop_hint: str | None = None, threshold: float = 0.6) -> dict | None:
    """Fuzzy-matches a free-text diagnosis (e.g. from a vision LLM that isn't
    constrained to the CNN's 38 classes) to the closest knowledge-base entry, or
    None if nothing is a close enough match. Used to ground an LLM diagnosis in
    real symptoms/precautions text (and to pick a Grad-CAM class) when the LLM's
    wording doesn't exactly match a class name.

    Generic disease names ("leaf blight", "leaf spot") text-match almost as well
    against the WRONG crop's entry as a specific name matches its correct entry —
    plain string similarity alone isn't reliable enough to trust here. When the
    crop is known, entries for other crops are excluded entirely rather than
    relying on the similarity score to sort it out; when the crop is unknown, we
    stay conservative (higher threshold) since there's no way to rule out a
    same-word, wrong-crop coincidence."""
    if not free_text_name:
        return None
    target = free_text_name.strip().lower()
    crop_target = (crop_hint or "").strip().lower()
    crop_known = bool(crop_target) and crop_target not in ("unknown", "n/a", "none")

    candidates_pool = _KB
    if crop_known:
        same_crop = [
            e for e in _KB
            if (e.get("affected_crop") or "").lower() in crop_target
            or crop_target in (e.get("affected_crop") or "").lower()
        ]
        if same_crop:
            candidates_pool = same_crop
        else:
            return None  # named a crop we don't have any KB entries for at all

    effective_threshold = threshold if crop_known else max(threshold, 0.75)

    best_entry, best_score = None, 0.0
    for entry in candidates_pool:
        for candidate in (entry["disease_name"], entry["class_name"].replace("___", " ").replace("_", " ")):
            score = SequenceMatcher(None, target, candidate.lower()).ratio()
            if score > best_score:
                best_score, best_entry = score, entry
    return best_entry if best_score >= effective_threshold else None


TOOL_SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "lookup_disease",
            "description": (
                "Look up symptoms and precautionary/treatment measures for a crop "
                "disease class detected by the vision model. Always call this before "
                "giving disease-specific advice so answers are grounded in the "
                "knowledge base rather than guessed."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "class_name": {
                        "type": "string",
                        "description": (
                            "Exact class name, e.g. 'Tomato___Late_blight', or a "
                            "human-readable disease/crop name if the exact class is unknown."
                        ),
                    }
                },
                "required": ["class_name"],
            },
        },
    }
]

TOOL_FUNCTIONS = {
    "lookup_disease": lookup_disease,
}
