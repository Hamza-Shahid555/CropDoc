"""Memory Agent: no LLM call — reads recent turns from sqlite before a
response is generated, and writes the finished turn back after."""

from ..core import db


def recall(session_id: int, limit: int = 20) -> list[dict]:
    messages = db.list_chat_messages(session_id)[-limit:]
    return [{"role": m["role"], "content": m["content"]} for m in messages]


def remember(session_id: int, role: str, content: str) -> None:
    db.add_chat_message(session_id, role, content)
