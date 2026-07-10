"""Central configuration: env loading, paths, model settings.

Loads backend/.env first (so the existing OPENAI_API_KEY carries over from the
FastAPI-era setup without duplication) then the root .env, which takes priority.
"""

import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent  # "New folder" project root
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

load_dotenv(BASE_DIR / "backend" / ".env")
load_dotenv(BASE_DIR / ".env", override=True)

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
OPENAI_CHAT_MODEL = os.environ.get("OPENAI_CHAT_MODEL", "gpt-4o-mini")
OPENAI_EMBEDDING_MODEL = os.environ.get("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")

ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
ANTHROPIC_MODEL = os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-5")

APP_SECRET = os.environ.get("APP_SECRET", "cropdoc-dev-secret-change-me")

DB_PATH = DATA_DIR / "cropdoc.db"
VECTOR_DIR = DATA_DIR / "vector_store"

CHECKPOINT_PATH = BASE_DIR / "cropdoc_resnet9.pth"
KB_PATH = BASE_DIR / "disease_knowledge_base.json"

APP_NAME = "CropDoc"
APP_TAGLINE = "AI-powered crop disease diagnosis and advisory"


def openai_configured() -> bool:
    # "sk-your-key-here" (the literal .env.example placeholder) does NOT start with "sk-...",
    # so that check never actually caught someone pasting the template unchanged - which is
    # exactly what happened on the first Streamlit Cloud deploy (confirmed via the real
    # AuthenticationError: "Incorrect API key provided: sk-your-****-key"). Check for the
    # real placeholder text instead of a pattern that doesn't match it.
    return bool(OPENAI_API_KEY) and "your-key-here" not in OPENAI_API_KEY and "your" not in OPENAI_API_KEY.lower()


def anthropic_configured() -> bool:
    return bool(ANTHROPIC_API_KEY) and "your-key-here" not in ANTHROPIC_API_KEY and "your" not in ANTHROPIC_API_KEY.lower()
