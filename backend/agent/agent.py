"""Agentic chat loop: sends the conversation to OpenAI, lets the model call
lookup_disease as needed, and keeps looping until it produces a final answer."""

import json
import os

from openai import OpenAI

from .tools import TOOL_FUNCTIONS, TOOL_SCHEMAS

MODEL = os.environ.get("OPENAI_CHAT_MODEL", "gpt-4o-mini")
MAX_TOOL_ITERATIONS = 5

SYSTEM_PROMPT = (
    "You are CropDoc Assistant, an agricultural advisor helping a farmer understand "
    "a crop disease detected by a computer vision model. Be concise and practical. "
    "Whenever the user asks about symptoms, treatment, prevention, or anything "
    "disease-specific, call the lookup_disease tool first to ground your answer in "
    "the knowledge base instead of guessing. If the user asks something unrelated "
    "to plant health, answer briefly and steer back to the topic."
)

_client = None


def get_client():
    global _client
    if _client is None:
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            raise RuntimeError(
                "OPENAI_API_KEY is not set. Add it to backend/.env before using /chat."
            )
        _client = OpenAI(api_key=api_key)
    return _client


def run_agent(message: str, history: list[dict], detected_disease: str | None) -> str:
    """history: list of {"role": "user"|"assistant", "content": str}"""
    client = get_client()

    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    if detected_disease:
        messages.append({
            "role": "system",
            "content": f"The vision model just detected this disease class: {detected_disease}",
        })
    messages.extend(history)
    messages.append({"role": "user", "content": message})

    for _ in range(MAX_TOOL_ITERATIONS):
        response = client.chat.completions.create(
            model=MODEL,
            messages=messages,
            tools=TOOL_SCHEMAS,
            tool_choice="auto",
        )
        msg = response.choices[0].message

        if not msg.tool_calls:
            return msg.content or ""

        messages.append({
            "role": "assistant",
            "content": msg.content,
            "tool_calls": [
                {
                    "id": tc.id,
                    "type": "function",
                    "function": {"name": tc.function.name, "arguments": tc.function.arguments},
                }
                for tc in msg.tool_calls
            ],
        })

        for tc in msg.tool_calls:
            fn = TOOL_FUNCTIONS.get(tc.function.name)
            args = json.loads(tc.function.arguments or "{}")
            result = fn(**args) if fn else {"error": f"Unknown tool {tc.function.name}"}
            messages.append({
                "role": "tool",
                "tool_call_id": tc.id,
                "content": json.dumps(result),
            })

    return "I looked into it but couldn't finish reasoning in time — please rephrase your question."
