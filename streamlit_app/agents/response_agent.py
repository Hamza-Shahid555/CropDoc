"""Response Agent: resolves any tool calls the model needs (reusing the same
proven function-calling loop shape as backend/agent/agent.py, just with a
bigger tool registry), then makes one final streamed call — with no `tools`
param, so it's guaranteed to return plain text — for the user-visible,
token-by-token answer."""

import json

from openai import OpenAI

from ..config import OPENAI_API_KEY, OPENAI_CHAT_MODEL
from .tools import TOOL_FUNCTIONS, TOOL_SCHEMAS

MAX_TOOL_ITERATIONS = 5

_client = None


def get_client() -> OpenAI:
    global _client
    if _client is None:
        _client = OpenAI(api_key=OPENAI_API_KEY)
    return _client


def _resolve_tools(messages: list[dict]) -> list[dict]:
    client = get_client()
    for _ in range(MAX_TOOL_ITERATIONS):
        response = client.chat.completions.create(
            model=OPENAI_CHAT_MODEL,
            messages=messages,
            tools=TOOL_SCHEMAS,
            tool_choice="auto",
        )
        msg = response.choices[0].message
        if not msg.tool_calls:
            break

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
                "content": json.dumps(result, default=str),
            })
    return messages


def generate(messages: list[dict]):
    """Resolves tool calls, then streams the final answer text chunk by chunk."""
    messages = _resolve_tools(messages)
    client = get_client()
    stream = client.chat.completions.create(model=OPENAI_CHAT_MODEL, messages=messages, stream=True)
    for chunk in stream:
        delta = chunk.choices[0].delta.content
        if delta:
            yield delta
