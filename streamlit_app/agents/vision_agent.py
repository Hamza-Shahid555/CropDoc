"""Vision Agent: elaborates on a ResNet9 diagnosis with an OpenAI-generated
narrative. It does not re-classify the image from raw pixels — the trained
CNN (backend.models.resnet9) already did that, with Grad-CAM to show its
work, and that result is treated as ground truth here. This agent's only job
is producing the fields the knowledge base doesn't have (explanation of the
prediction, likely causes, a severity rating, fertilizer tips, expert notes)
grounded in the KB's real symptoms/measures — kept separate from the exact
symptoms/treatment text, which stays sourced straight from the knowledge base
so it's never at risk of being rephrased or hallucinated."""

import json

from openai import OpenAI

from ..config import OPENAI_API_KEY, OPENAI_CHAT_MODEL

SYSTEM_PROMPT = (
    "You are an agricultural expert writing supplementary AI-generated guidance for a "
    "plant-disease diagnosis that a trained computer vision model already made. Do not "
    "second-guess the diagnosis — treat the disease name and confidence as ground truth. "
    "Given the disease, crop, confidence, and its known symptoms/precautions, respond with "
    "strict JSON only, matching this shape:\n"
    "{\n"
    '  "explanation": "1-2 sentences on why these symptoms indicate this disease",\n'
    '  "causes": "likely environmental/biological causes",\n'
    '  "severity": "Healthy" | "Mild" | "Moderate" | "Severe",\n'
    '  "organic_treatment": "organic/non-chemical treatment options, or empty string if not applicable",\n'
    '  "chemical_treatment": "chemical treatment options, or empty string if not applicable",\n'
    '  "fertilizer_recommendation": "fertilizer guidance relevant to recovery/prevention",\n'
    '  "expert_notes": "one practical additional tip an agronomist would add"\n'
    "}\n"
    "If the plant is healthy, severity is \"Healthy\" and treatment fields should focus on "
    "maintenance rather than being left blank. Base severity on the confidence and how "
    "serious the symptoms sound, not on guesswork."
)

_client = None
FALLBACK = {
    "explanation": "",
    "causes": "",
    "severity": "Unknown",
    "organic_treatment": "",
    "chemical_treatment": "",
    "fertilizer_recommendation": "",
    "expert_notes": "",
}


def _get_client() -> OpenAI:
    global _client
    if _client is None:
        _client = OpenAI(api_key=OPENAI_API_KEY)
    return _client


def narrate_diagnosis(kb_entry: dict, confidence: float) -> dict:
    facts = {
        "disease_name": kb_entry.get("disease_name"),
        "affected_crop": kb_entry.get("affected_crop"),
        "is_healthy": kb_entry.get("is_healthy"),
        "confidence_percent": round(confidence, 1),
        "known_symptoms": kb_entry.get("symptoms"),
        "known_precautions": kb_entry.get("precautionary_measures"),
    }
    try:
        resp = _get_client().chat.completions.create(
            model=OPENAI_CHAT_MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": json.dumps(facts)},
            ],
            response_format={"type": "json_object"},
            temperature=0.4,
        )
        data = json.loads(resp.choices[0].message.content or "{}")
        return {**FALLBACK, **data}
    except Exception:
        severity = "Healthy" if kb_entry.get("is_healthy") else "Unknown"
        return {**FALLBACK, "severity": severity}
