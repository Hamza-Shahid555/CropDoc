"""Thin sqlite3 repository layer: users, chat sessions/messages, contact
messages, prediction log. No ORM — the schema is small and stable enough that
raw SQL stays more readable than mapping layers.
"""

import contextlib
import datetime
import json
import sqlite3
from pathlib import Path

from ..config import DB_PATH

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS chat_sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    title TEXT NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users (id)
);

CREATE TABLE IF NOT EXISTS chat_messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id INTEGER NOT NULL,
    role TEXT NOT NULL,
    content TEXT NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY (session_id) REFERENCES chat_sessions (id)
);

CREATE TABLE IF NOT EXISTS contact_messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT NOT NULL,
    message TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS prediction_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    class_name TEXT NOT NULL,
    disease_name TEXT,
    confidence REAL,
    is_healthy INTEGER,
    created_at TEXT NOT NULL
);
"""


def _now() -> str:
    return datetime.datetime.utcnow().isoformat()


@contextlib.contextmanager
def get_conn():
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db() -> None:
    with get_conn() as conn:
        conn.executescript(SCHEMA)
        _migrate(conn)


def _migrate(conn: sqlite3.Connection) -> None:
    """Adds columns introduced after the initial schema, without touching
    existing rows or requiring a destructive rebuild."""
    existing = {row["name"] for row in conn.execute("PRAGMA table_info(chat_messages)")}
    for column, coltype in (("image_b64", "TEXT"), ("kind", "TEXT DEFAULT 'text'"), ("meta", "TEXT")):
        if column not in existing:
            conn.execute(f"ALTER TABLE chat_messages ADD COLUMN {column} {coltype}")


# --- users -------------------------------------------------------------

def get_user_by_username(username: str):
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
        return dict(row) if row else None


def create_user(username: str, password_hash: str) -> int:
    with get_conn() as conn:
        cur = conn.execute(
            "INSERT INTO users (username, password_hash, created_at) VALUES (?, ?, ?)",
            (username, password_hash, _now()),
        )
        return cur.lastrowid


# --- chat sessions / messages -------------------------------------------

def create_chat_session(user_id: int, title: str = "New chat") -> int:
    with get_conn() as conn:
        cur = conn.execute(
            "INSERT INTO chat_sessions (user_id, title, created_at) VALUES (?, ?, ?)",
            (user_id, title, _now()),
        )
        return cur.lastrowid


def list_chat_sessions(user_id: int) -> list[dict]:
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM chat_sessions WHERE user_id = ? ORDER BY id DESC", (user_id,)
        ).fetchall()
        return [dict(r) for r in rows]


def rename_chat_session(session_id: int, title: str) -> None:
    with get_conn() as conn:
        conn.execute("UPDATE chat_sessions SET title = ? WHERE id = ?", (title, session_id))


def delete_chat_session(session_id: int) -> None:
    with get_conn() as conn:
        conn.execute("DELETE FROM chat_messages WHERE session_id = ?", (session_id,))
        conn.execute("DELETE FROM chat_sessions WHERE id = ?", (session_id,))


def clear_chat_messages(session_id: int) -> None:
    with get_conn() as conn:
        conn.execute("DELETE FROM chat_messages WHERE session_id = ?", (session_id,))


def add_chat_message(
    session_id: int,
    role: str,
    content: str,
    image_b64: str | None = None,
    kind: str = "text",
    meta: dict | None = None,
) -> None:
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO chat_messages (session_id, role, content, created_at, image_b64, kind, meta) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (session_id, role, content, _now(), image_b64, kind, json.dumps(meta) if meta else None),
        )


def add_diagnosis_message(session_id: int, content: str, meta: dict) -> None:
    """Writes the assistant's structured diagnosis turn (Grad-CAM images and
    LLM narrative live in `meta`) that both Detect Disease and AI Chat render as a
    result card. The uploaded photo itself is a separate, preceding user message
    (via add_chat_message(..., image_b64=...)) — this call only follows it."""
    add_chat_message(session_id, "assistant", content, kind="diagnosis", meta=meta)


def list_chat_messages(session_id: int) -> list[dict]:
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM chat_messages WHERE session_id = ? ORDER BY id ASC", (session_id,)
        ).fetchall()
        messages = [dict(r) for r in rows]
        for m in messages:
            m["meta"] = json.loads(m["meta"]) if m.get("meta") else None
        return messages


def get_latest_diagnosis(session_id: int) -> dict | None:
    with get_conn() as conn:
        row = conn.execute(
            "SELECT meta FROM chat_messages WHERE session_id = ? AND kind = 'diagnosis' "
            "ORDER BY id DESC LIMIT 1",
            (session_id,),
        ).fetchone()
        return json.loads(row["meta"]) if row and row["meta"] else None


# --- contact -------------------------------------------------------------

def add_contact_message(name: str, email: str, message: str) -> None:
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO contact_messages (name, email, message, created_at) VALUES (?, ?, ?, ?)",
            (name, email, message, _now()),
        )


# --- prediction log / dashboard stats ------------------------------------

def log_prediction(user_id: int | None, class_name: str, disease_name: str, confidence: float, is_healthy: bool) -> None:
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO prediction_log (user_id, class_name, disease_name, confidence, is_healthy, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (user_id, class_name, disease_name, confidence, int(bool(is_healthy)), _now()),
        )


def get_dashboard_stats() -> dict:
    with get_conn() as conn:
        total_predictions = conn.execute("SELECT COUNT(*) c FROM prediction_log").fetchone()["c"]
        total_sessions = conn.execute("SELECT COUNT(*) c FROM chat_sessions").fetchone()["c"]
        total_messages = conn.execute("SELECT COUNT(*) c FROM chat_messages").fetchone()["c"]
        top_classes = conn.execute(
            "SELECT disease_name, COUNT(*) c FROM prediction_log "
            "GROUP BY disease_name ORDER BY c DESC LIMIT 8"
        ).fetchall()
        healthy_ratio = conn.execute(
            "SELECT AVG(is_healthy) a FROM prediction_log"
        ).fetchone()["a"]
        avg_confidence = conn.execute(
            "SELECT AVG(confidence) a FROM prediction_log"
        ).fetchone()["a"]
        healthy_count = conn.execute(
            "SELECT COUNT(*) c FROM prediction_log WHERE is_healthy = 1"
        ).fetchone()["c"]
        return {
            "total_predictions": total_predictions,
            "total_sessions": total_sessions,
            "total_messages": total_messages,
            "top_classes": [dict(r) for r in top_classes],
            "healthy_ratio": healthy_ratio,
            "avg_confidence": avg_confidence,
            "healthy_count": healthy_count,
            "diseased_count": total_predictions - healthy_count,
        }


def get_recent_predictions(limit: int = 10) -> list[dict]:
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM prediction_log ORDER BY id DESC LIMIT ?", (limit,)
        ).fetchall()
        return [dict(r) for r in rows]


def get_prediction_trend(days: int = 14) -> list[dict]:
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT date(created_at) AS day, COUNT(*) AS c FROM prediction_log "
            "WHERE date(created_at) >= date('now', ?) "
            "GROUP BY day ORDER BY day ASC",
            (f"-{days} days",),
        ).fetchall()
        return [dict(r) for r in rows]
