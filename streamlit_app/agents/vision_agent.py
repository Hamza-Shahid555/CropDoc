"""Vision Agent: independently verifies a ResNet9 diagnosis against the actual
leaf photo using an OpenAI vision-capable model, then elaborates on it.

The CNN (backend.models.resnet9) is trained on only 38 specific crop-disease
classes and has no "unknown" output — given a plant outside that set, it will
always force-fit the image into the closest wrong class, and previously
nothing downstream ever caught that (this agent used to be told to "treat the
disease name and confidence as ground truth" without ever looking at the
image itself). It now receives the photo directly, forms its own independent
judgment, and explicitly flags agreement/disagreement and image-quality
issues instead of blindly endorsing the CNN. Symptoms/treatment text grounded
in the knowledge base is still sourced straight from there, never rephrased,
so the two are never at risk of drifting apart."""

import base64
import json

from openai import OpenAI

from ..config import OPENAI_API_KEY, OPENAI_CHAT_MODEL

SYSTEM_PROMPT = (
    "You are an agricultural expert verifying a plant-disease diagnosis made by a "
    "specialist computer vision model (a CNN trained on only 38 specific crop-disease "
    "classes, with no 'unknown' option — it can be confidently wrong for any other plant). "
    "You are given the actual leaf photo plus the CNN's prediction, confidence, and the "
    "knowledge-base entry it matched. Look at the photo yourself and form an independent "
    "judgment BEFORE deciding whether you agree.\n\n"
    "Respond with strict JSON only, matching this shape:\n"
    "{\n"
    '  "agrees_with_model": true | false,\n'
    '  "agreement_note": "1-2 sentences: what you see, and why you agree or disagree",\n'
    '  "alternative_diagnosis": "your own best guess if you disagree, else empty string",\n'
    '  "image_quality_ok": true | false,\n'
    '  "image_quality_issue": "empty string if ok, else briefly describe the issue (blurry/dark/distant/etc.)",\n'
    '  "explanation": "1-2 sentences on why the visible symptoms indicate this disease",\n'
    '  "causes": "likely environmental/biological causes",\n'
    '  "severity": "Healthy" | "Mild" | "Moderate" | "Severe",\n'
    '  "organic_treatment": "organic/non-chemical treatment options, or empty string if not applicable",\n'
    '  "chemical_treatment": "chemical treatment options, or empty string if not applicable",\n'
    '  "fertilizer_recommendation": "fertilizer guidance relevant to recovery/prevention",\n'
    '  "expert_notes": "one practical additional tip an agronomist would add"\n'
    "}\n"
    "Rules:\n"
    "- If the photo doesn't look like the crop/disease the CNN named (e.g. wrong plant "
    "species, wrong leaf shape/pattern), set agrees_with_model to false and explain why in "
    "agreement_note — do not endorse a guess your own eyes contradict.\n"
    "- If the image is too blurry, dark, distant, or obstructed to tell either way, set "
    "image_quality_ok to false, describe the issue, and keep your own confidence framing low "
    "rather than agreeing just because you have nothing better to compare it to.\n"
    "- If the plant is healthy, severity is \"Healthy\" and treatment fields should focus on "
    "maintenance rather than being left blank."
)

_client = None
FALLBACK = {
    "agrees_with_model": None,
    "agreement_note": "",
    "alternative_diagnosis": "",
    "image_quality_ok": True,
    "image_quality_issue": "",
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


def narrate_diagnosis(kb_entry: dict, confidence: float, image_bytes: bytes) -> dict:
    facts = {
        "cnn_predicted_disease": kb_entry.get("disease_name"),
        "cnn_predicted_crop": kb_entry.get("affected_crop"),
        "cnn_says_is_healthy": kb_entry.get("is_healthy"),
        "cnn_confidence_percent": round(confidence, 1),
        "known_symptoms_for_this_class": kb_entry.get("symptoms"),
        "known_precautions_for_this_class": kb_entry.get("precautionary_measures"),
    }
    b64_image = base64.standard_b64encode(image_bytes).decode("ascii")
    try:
        resp = _get_client().chat.completions.create(
            model=OPENAI_CHAT_MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": json.dumps(facts)},
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64_image}"}},
                    ],
                },
            ],
            response_format={"type": "json_object"},
            temperature=0.4,
        )
        if resp.choices[0].finish_reason == "length":
            raise RuntimeError("Vision verification response was truncated (hit token limit).")
        data = json.loads(resp.choices[0].message.content or "{}")
        return {**FALLBACK, **data}
    except Exception:
        severity = "Healthy" if kb_entry.get("is_healthy") else "Unknown"
        return {
            **FALLBACK,
            "severity": severity,
            "agreement_note": "AI verification was unavailable — this diagnosis is from the vision model alone, unverified.",
        }
