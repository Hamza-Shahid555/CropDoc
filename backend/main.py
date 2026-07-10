import os
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

load_dotenv(Path(__file__).resolve().parent / ".env")  # backend/.env, regardless of cwd (no-op if missing, e.g. on Render)

from .routes import chat, predict  # noqa: E402  (import after load_dotenv)

app = FastAPI(title="CropDoc API")

# Comma-separated list, e.g. "http://localhost:3000,https://cropdoc.vercel.app"
_origins = os.environ.get("ALLOWED_ORIGINS", "http://localhost:3000")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in _origins.split(",") if o.strip()],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(predict.router)
app.include_router(chat.router)


@app.get("/health")
def health():
    return {"status": "ok"}
