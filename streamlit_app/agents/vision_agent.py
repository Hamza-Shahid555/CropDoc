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
import logging

from openai import OpenAI

from ..config import OPENAI_API_KEY, OPENAI_CHAT_MODEL

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = (
    "You are an expert plant pathologist identifying a plant and its disease from a leaf photo. "
    "Respond with strict JSON only, matching this shape:\n"
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
    "}\n\n"
    "How to identify plant_species — always commit to your single best specific guess, e.g. "
    "\"Soybean\", \"Grape\", \"Bell Pepper\", \"Corn (maize)\", using leaf shape (ovate/lobed/compound), "
    "margin (smooth/serrated/toothed), venation pattern, and leaflet arrangement, the same way a "
    "botanist would from a clear leaf photo alone. Only answer \"Unknown\" if the leaf is so "
    "cropped, obstructed, or generic-looking that even an expert botanist genuinely could not "
    "narrow it past 'broadleaf plant' — this should be rare for a clear, well-lit, full-leaf photo. "
    "A confident-looking but possibly-wrong specific guess (reflected honestly via a lower "
    "confidence score) is far more useful than defaulting to \"Unknown\".\n\n"
    "How to identify disease_name — always name the specific disease or pathogen your visual "
    "evidence points to (e.g. \"Bacterial Blight\", \"Bacterial Pustule\", \"Septoria Brown Spot\", "
    "\"Powdery Mildew\", \"Early Blight\"), reasoning from lesion shape (angular/circular/irregular), "
    "border (whether it's bounded by leaf veins), color pattern (halos, concentric rings, pustules), "
    "and distribution across the leaf. Do NOT fall back to a generic category label like \"Leaf Spot "
    "Disease\", \"Fungal Infection\", or \"Leaf Blight\" as your final answer — those are diagnostic "
    "categories, not diagnoses. If you're genuinely torn between 2-3 specific candidates, name your "
    "single best one in disease_name and mention the runner-up(s) in explanation, again using "
    "confidence to reflect the uncertainty rather than vagueness in the name itself.\n\n"
    "Rules:\n"
    "- Never invent a confidence score you can't justify from what's actually visible — a specific, "
    "lower-confidence guess is correct behavior; a vague, evasive answer is not.\n"
    "- If the photo is too blurry, dark, distant, or obstructed to identify anything at all, set "
    "image_quality_ok to false, describe the issue, and keep confidence low rather than guessing — "
    "but a clear, in-focus, well-lit leaf filling the frame is NOT a reason to hedge.\n"
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


def diagnose_from_image(image_bytes: bytes) -> dict | None:
    """Primary diagnosis path: the vision LLM analyzes the photo directly, with
    no CNN prediction anchoring or biasing its answer. Returns None on failure
    (never a fake placeholder result) so the caller can properly fall through
    to another source instead of displaying "Unable to analyze" as if it were
    a real diagnosis."""
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
        logger.exception("OpenAI diagnose_from_image failed")
        return None
