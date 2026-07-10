"""Tools the chat agent can call. Keeping the knowledge base behind a tool
(instead of pasting it into the prompt) is what makes the agent "agentic":
the model decides when it needs grounded facts and asks for them."""

import json
import re
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


def _normalize_for_match(text: str) -> str:
    text = re.sub(r"\(.*?\)", " ", text)  # strip parenthetical pathogen names, e.g. "(Exserohilum turcicum)"
    text = re.sub(r"[^a-z0-9\s]", " ", text.lower())
    return re.sub(r"\s+", " ", text).strip()


def _token_jaccard(a: str, b: str) -> float:
    a_tokens, b_tokens = set(a.split()), set(b.split())
    if not a_tokens or not b_tokens:
        return 0.0
    return len(a_tokens & b_tokens) / len(a_tokens | b_tokens)


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
    relying on the similarity score to sort it out.

    Uses the better of a character-sequence ratio and a word-set (order-independent)
    score: an LLM saying "Northern Corn Leaf Blight (Exserohilum turcicum)" against
    the KB's "Corn Northern Leaf Blight" is the same disease in different word order
    plus an extra pathogen name — character-sequence matching alone scores that too
    low to trust (verified: 0.55, below a safe threshold) even though it's a correct
    match once reordering and the parenthetical are accounted for.

    When the crop is unknown, we don't attempt a match at all — not even at a high
    threshold. A short generic phrase like "leaf blight" is a near-exact substring
    of some specific crop's full disease name (e.g. "Grape Leaf Blight") purely by
    coincidence, which scores deceptively high regardless of the threshold chosen
    (verified empirically), and there's no crop-gating safety net to catch it when
    the crop itself is unknown."""
    if not free_text_name:
        return None
    crop_target = (crop_hint or "").strip().lower()
    crop_known = bool(crop_target) and crop_target not in ("unknown", "n/a", "none")
    if not crop_known:
        return None

    target = _normalize_for_match(free_text_name)
    same_crop = [
        e for e in _KB
        if (e.get("affected_crop") or "").lower() in crop_target
        or crop_target in (e.get("affected_crop") or "").lower()
    ]
    if not same_crop:
        return None  # named a crop we don't have any KB entries for at all

    best_entry, best_score = None, 0.0
    for entry in same_crop:
        for candidate in (entry["disease_name"], entry["class_name"].replace("___", " ").replace("_", " ")):
            candidate_norm = _normalize_for_match(candidate)
            score = max(
                SequenceMatcher(None, target, candidate_norm).ratio(),
                _token_jaccard(target, candidate_norm),
            )
            if score > best_score:
                best_score, best_entry = score, entry
    return best_entry if best_score >= threshold else None


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
