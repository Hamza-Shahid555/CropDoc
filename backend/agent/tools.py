"""Tools the chat agent can call. Keeping the knowledge base behind a tool
(instead of pasting it into the prompt) is what makes the agent "agentic":
the model decides when it needs grounded facts and asks for them."""

import json
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
