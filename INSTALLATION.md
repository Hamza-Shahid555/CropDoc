# Installation

## Prerequisites

- Python 3.11 or 3.12
- The trained checkpoint `cropdoc_resnet9.pth` in the project root (see `CropDoc_Training.ipynb`
  / `Guide.txt` if you need to retrain it)
- An OpenAI API key (for the AI Chat page — Detect Disease works without one)

## Setup

```bash
cd "New folder"

# 1. Create and activate a virtual environment
python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # macOS/Linux

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure environment variables
copy .env.example .env          # Windows
# cp .env.example .env          # macOS/Linux
# then edit .env and set OPENAI_API_KEY
```

`config.py` also reads `backend/.env` first (for anyone who already had the FastAPI backend's key
set up) and then the root `.env`, which takes priority — so setting the key in either file works.

## Run

```bash
streamlit run streamlit_app/app.py
```

The app opens at `http://localhost:8501`. Log in with the seeded demo account:

- **Username:** `demo`
- **Password:** `demo1234`

or register a new account from the login screen.

## First run behavior

- The sqlite database (`data/cropdoc.db`) and FAISS vector store (`data/vector_store/`) are
  created automatically on first launch.
- The disease knowledge base (`disease_knowledge_base.json`) is embedded and indexed into FAISS
  automatically the first time the AI Chat page runs a query that needs it (or immediately from
  the Settings page via "Rebuild knowledge base index").
- If `cropdoc_resnet9.pth` is missing, the Detect Disease page shows a clear error instead of
  crashing; every other page still works.
- If `OPENAI_API_KEY` isn't set, the AI Chat page shows a warning and stops instead of failing
  with an API error; every other page still works.

## Legacy FastAPI + Next.js stack (optional)

The original backend/frontend split still works standalone if you want it:

```bash
# Backend
pip install -r backend/requirements.txt
uvicorn backend.main:app --reload --app-dir .

# Frontend (separate terminal)
cd frontend
npm install
npm run dev
```

It does not need to be running for the Streamlit app — the Streamlit app imports the shared model
and knowledge-base code directly rather than calling this API over HTTP.
