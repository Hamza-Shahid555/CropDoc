"""Claude Agent: final diagnosis synthesizer.

Reviews the actual leaf photo alongside the CNN's and OpenAI's independent
findings (when available) and produces the diagnosis that gets shown as
primary. It forms its own judgment from the image first, then explicitly
reasons about agreement/disagreement with each other source rather than
blindly deferring to either — mirrors the same reasoning failure this whole
project has been fixing: no single source (a 38-class CNN, or a single LLM
call) should be presented as ground truth without something else checking it
against the actual photo. If neither the CNN nor OpenAI produced usable
context, this still works standalone as a direct diagnosis."""

import base64
import logging

import anthropic

from ..config import ANTHROPIC_API_KEY, ANTHROPIC_MODEL

logger = logging.getLogger(__name__)

DIAGNOSIS_TOOL = {
    "name": "record_diagnosis",
    "description": "Record the final synthesized plant disease diagnosis.",
    "input_schema": {
        "type": "object",
        "properties": {
            "plant_species": {"type": "string"},
            "disease_name": {"type": "string", "description": "Specific disease/pathogen name, or 'Healthy'"},
            "is_healthy": {"type": "boolean"},
            "confidence": {"type": "number", "description": "0-100"},
            "severity": {"type": "string", "enum": ["Healthy", "Mild", "Moderate", "Severe"]},
            "symptoms": {"type": "string"},
            "explanation": {"type": "string", "description": "1-2 sentences on why these symptoms indicate this disease"},
            "causes": {"type": "string"},
            "organic_treatment": {"type": "string"},
            "chemical_treatment": {"type": "string"},
            "fertilizer_recommendation": {"type": "string"},
            "expert_notes": {"type": "string"},
            "image_quality_ok": {"type": "boolean"},
            "image_quality_issue": {"type": "string"},
            "agrees_with_openai": {"type": "boolean", "description": "Only include if OpenAI's finding was provided"},
            "agrees_with_cnn": {"type": "boolean", "description": "Only include if the CNN's finding was provided"},
            "agreement_note": {
                "type": "string",
                "description": "1-3 sentences comparing your finding to whichever other sources were provided; if none were provided, note this is a standalone diagnosis",
            },
        },
        "required": [
            "plant_species", "disease_name", "is_healthy", "confidence", "severity", "symptoms",
            "explanation", "causes", "organic_treatment", "chemical_treatment",
            "fertilizer_recommendation", "expert_notes", "image_quality_ok", "image_quality_issue",
            "agreement_note",
        ],
    },
}

SYSTEM_PROMPT = (
    "You are the final-review plant pathologist. You are shown a leaf photo and, when available, "
    "independent findings from a specialist CNN (trained on only 38 fixed crop-disease classes, "
    "with no 'unknown' option — it can be confidently wrong for any other plant) and/or an OpenAI "
    "vision model. Treat those as advisory opinions from other panelists, not ground truth: form "
    "your OWN judgment from the image first, then explicitly compare it to whatever was provided.\n\n"
    "Always commit to your single best specific guess for plant_species (leaf shape/margin/venation) "
    "and disease_name (lesion shape/border/color pattern, not a generic category like 'Leaf Spot "
    "Disease' or 'Fungal Infection') — express uncertainty through the confidence score, not through "
    "a vague answer. Only say 'Unknown' species if the photo genuinely gives no identifying clues.\n\n"
    "Rules:\n"
    "- If the image is blurry, dark, distant, or obstructed, set image_quality_ok to false, describe "
    "the issue, and keep confidence low rather than guessing.\n"
    "- If you disagree with a provided source, say so explicitly in agreement_note and explain why "
    "(e.g. the CNN can only recognize its own training classes and may force-fit an unfamiliar plant "
    "into the wrong one) — do not silently split the difference.\n"
    "- Your organic/chemical/fertilizer recommendations should reflect your own final diagnosis; you "
    "may draw on a provided source's treatment suggestions where they still apply, but don't copy "
    "advice for a disease you've disagreed with.\n"
    "- Always call record_diagnosis exactly once with your complete findings."
)


def _build_context_block(cnn_context: dict | None, openai_context: dict | None) -> str:
    parts = []
    if cnn_context:
        parts.append(
            f"Specialist CNN finding (only recognizes 38 fixed classes): "
            f"{cnn_context.get('class_name', 'Unknown')} at {cnn_context.get('confidence', 0):.1f}% confidence."
        )
    if openai_context:
        label = "Healthy" if openai_context.get("is_healthy") else openai_context.get("disease_name", "Unknown")
        parts.append(
            f"OpenAI vision finding: {openai_context.get('plant_species', 'Unknown')} — {label} "
            f"at {openai_context.get('confidence', 0)}% confidence. "
            f"Symptoms it noted: {openai_context.get('symptoms', 'N/A')}. "
            f"Its treatment suggestions — organic: {openai_context.get('organic_treatment', 'N/A')}; "
            f"chemical: {openai_context.get('chemical_treatment', 'N/A')}."
        )
    if not parts:
        return ""
    return "Other findings for cross-reference (advisory only — form your own judgment first):\n\n" + "\n\n".join(parts)


last_error: str | None = None  # set by the most recent failed call; read by the caller for on-screen diagnostics


def synthesize_diagnosis(image_bytes: bytes, cnn_context: dict | None = None, openai_context: dict | None = None) -> dict | None:
    global last_error
    last_error = None
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    b64_image = base64.standard_b64encode(image_bytes).decode("ascii")
    context_block = _build_context_block(cnn_context, openai_context)
    text_prompt = "Diagnose this leaf photo and record your final findings."
    if context_block:
        text_prompt += "\n\n" + context_block

    try:
        response = client.messages.create(
            model=ANTHROPIC_MODEL,
            max_tokens=2500,
            system=SYSTEM_PROMPT,
            tools=[DIAGNOSIS_TOOL],
            tool_choice={"type": "tool", "name": "record_diagnosis"},
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "image", "source": {"type": "base64", "media_type": "image/jpeg", "data": b64_image}},
                        {"type": "text", "text": text_prompt},
                    ],
                }
            ],
        )
        if response.stop_reason == "max_tokens":
            raise RuntimeError("Claude diagnosis response was truncated (hit max_tokens).")
        for block in response.content:
            if block.type == "tool_use" and block.name == "record_diagnosis":
                return dict(block.input)
        raise RuntimeError("Claude did not return a structured diagnosis.")
    except Exception as e:
        last_error = f"{type(e).__name__}: {e}"
        logger.exception("Claude synthesis failed")
        return None
