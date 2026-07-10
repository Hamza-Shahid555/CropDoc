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

APP_SECRET = os.environ.get("APP_SECRET", "cropdoc-dev-secret-change-me")

DB_PATH = DATA_DIR / "cropdoc.db"
VECTOR_DIR = DATA_DIR / "vector_store"

CHECKPOINT_PATH = BASE_DIR / "cropdoc_resnet9.pth"
KB_PATH = BASE_DIR / "disease_knowledge_base.json"

APP_NAME = "CropDoc"
APP_TAGLINE = "AI-powered crop disease diagnosis and advisory"


def openai_configured() -> bool:
    return bool(OPENAI_API_KEY) and not OPENAI_API_KEY.startswith("sk-...")
