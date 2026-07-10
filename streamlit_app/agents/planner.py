"""Planner Agent: one small, cheap LLM call that decides whether this turn
needs Research Agent grounding (RAG over the knowledge base / uploaded docs)
before the Response Agent generates its answer. Tool/API availability is
always handed to the Response Agent's own function-calling loop — the model
itself decides when to actually call lookup_disease / get_weather — so the
planner's only job is the one decision that has to be made *before* that
call: whether to spend an embedding + similarity search on this turn."""

import json

from openai import OpenAI

from ..config import OPENAI_API_KEY, OPENAI_CHAT_MODEL

SYSTEM_PROMPT = (
    "You are the planning module for CropDoc, a crop-disease assistant. Given the "
    "user's latest message, decide whether answering it well benefits from grounding "
    "in the plant-disease knowledge base or any documents the user has uploaded "
    "(symptoms, treatment, prevention, disease facts, crop info, or referencing an "
    "uploaded document). Respond with strict JSON only: "
    '{"needs_research": true|false}. '
    "needs_research should be false only for pure greetings, thanks, or meta "
    "questions about the assistant itself."
)

_client = None


def _get_client() -> OpenAI:
    global _client
    if _client is None:
        _client = OpenAI(api_key=OPENAI_API_KEY)
    return _client


def plan_turn(message: str) -> dict:
    try:
        resp = _get_client().chat.completions.create(
            model=OPENAI_CHAT_MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": message},
            ],
            response_format={"type": "json_object"},
            temperature=0,
        )
        data = json.loads(resp.choices[0].message.content or "{}")
        return {"needs_research": bool(data.get("needs_research", True))}
    except Exception:
        return {"needs_research": True}  # safe default: over-include context rather than under
