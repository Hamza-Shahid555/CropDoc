"""Vision Agent: diagnoses a leaf photo DIRECTLY with a vision-capable LLM.

This is the primary diagnosis engine — the LLM looks at the actual photo and
forms its own open-set judgment (not constrained to any fixed class list).
The local ResNet9 CNN (backend.models.resnet9) is a secondary signal only:
it was trained on just 38 specific crop-disease classes with no "unknown"
option, so treating its output as ground truth meant any other plant got
confidently force-fit into the closest wrong class, with nothing ever
looking at the actual image to catch it. It's now used only to (a) offer a
second, independent data point for comparison and (b) drive the Grad-CAM
visualization, pointed at whichever of its 38 classes best matches the LLM's
diagnosis (via knowledge-base fuzzy matching) rather than blindly at its own
top guess."""

import base64
import json

from openai import OpenAI

from ..config import OPENAI_API_KEY, OPENAI_CHAT_MODEL

SYSTEM_PROMPT = (
    "You are an expert plant pathologist. Examine this leaf photo directly and give your own "
    "independent diagnosis — do not assume the plant or disease belongs to any fixed list; name "
    "whatever you actually see. Respond with strict JSON only, matching this shape:\n"
    "{\n"
    '  "plant_species": "the plant/crop shown",\n'
    '  "disease_name": "the disease name, or \\"Healthy\\" if no disease is visible",\n'
    '  "is_healthy": true | false,\n'
    '  "confidence": 0-100,\n'
    '  "severity": "Healthy" | "Mild" | "Moderate" | "Severe",\n'
    '  "symptoms": "visible symptoms you observe in the photo",\n'
    '  "explanation": "1-2 sentences on why these symptoms indicate this disease",\n'
    '  "causes": "likely environmental/biological causes",\n'
    '  "organic_treatment": "organic/non-chemical treatment options, or empty string if not applicable",\n'
    '  "chemical_treatment": "chemical treatment options, or empty string if not applicable",\n'
    '  "fertilizer_recommendation": "fertilizer guidance relevant to recovery/prevention",\n'
    '  "expert_notes": "one practical additional tip an agronomist would add",\n'
    '  "image_quality_ok": true | false,\n'
    '  "image_quality_issue": "empty string if ok, else briefly describe the issue (blurry/dark/distant/etc.)"\n'
    "}\n"
    "Rules:\n"
    "- Never invent a confidence score you can't justify from what's actually visible.\n"
    "- If the photo is too blurry, dark, distant, or obstructed to diagnose confidently, set "
    "image_quality_ok to false, describe the issue, and keep confidence low rather than guessing.\n"
    "- If the plant is healthy, severity is \"Healthy\" and treatment fields should focus on "
    "maintenance rather than being left blank."
)

_client = None
FALLBACK = {
    "plant_species": "Unknown",
    "disease_name": "Unable to analyze",
    "is_healthy": False,
    "confidence": 0,
    "severity": "Unknown",
    "symptoms": "",
    "explanation": "AI diagnosis was unavailable for this photo.",
    "causes": "",
    "organic_treatment": "",
    "chemical_treatment": "",
    "fertilizer_recommendation": "",
    "expert_notes": "",
    "image_quality_ok": True,
    "image_quality_issue": "",
}


def _get_client() -> OpenAI:
    global _client
    if _client is None:
        _client = OpenAI(api_key=OPENAI_API_KEY)
    return _client


def diagnose_from_image(image_bytes: bytes) -> dict:
    """Primary diagnosis path: the vision LLM analyzes the photo directly, with
    no CNN prediction anchoring or biasing its answer."""
    b64_image = base64.standard_b64encode(image_bytes).decode("ascii")
    try:
        resp = _get_client().chat.completions.create(
            model=OPENAI_CHAT_MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "Diagnose this leaf photo."},
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64_image}"}},
                    ],
                },
            ],
            response_format={"type": "json_object"},
            temperature=0.3,
        )
        if resp.choices[0].finish_reason == "length":
            raise RuntimeError("Diagnosis response was truncated (hit token limit).")
        data = json.loads(resp.choices[0].message.content or "{}")
        return {**FALLBACK, **data}
    except Exception:
        return {**FALLBACK, "explanation": "AI diagnosis failed unexpectedly for this photo — please try again."}
