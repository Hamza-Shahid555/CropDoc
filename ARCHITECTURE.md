# CropDoc — Architecture

## Overview

CropDoc diagnoses crop leaf diseases from a photo (ResNet9 + Grad-CAM) and lets the user ask a
multi-agent assistant follow-up questions, grounded in a disease knowledge base and any documents
the user uploads. The primary product is a single Streamlit application (`streamlit_app/`).

A previous iteration of this project shipped as a FastAPI backend (`backend/`) + Next.js frontend
(`frontend/`). Those are left in place and still work standalone, but the Streamlit app does not
call them over HTTP — it imports the shared, framework-agnostic model and knowledge-base code
directly (see "Code reuse" below) so there is one vision-model implementation, not two.

## Layers

```
┌─────────────────────────────────────────────────────────────┐
│ streamlit_app/views/*.py           Pages (Home, Detect, Chat,│
│                                     Dashboard, Settings, ...) │
├─────────────────────────────────────────────────────────────┤
│ streamlit_app/agents/               Multi-agent chat          │
│   orchestrator.py                   orchestrates a turn       │
│   planner.py                        1 LLM call: needs_research?│
│   research_agent.py                 FAISS similarity search   │
│   tool_agent.py / api_agent.py      OpenAI function-calling   │
│                                      tool registry             │
│   memory_agent.py                   sqlite recall/persist     │
│   response_agent.py                 tool loop + streamed reply│
├─────────────────────────────────────────────────────────────┤
│ streamlit_app/rag/                  Document ingestion + FAISS│
│   loaders.py / chunking.py          PDF/DOCX/TXT/MD/CSV → text│
│   vector_store.py                   FAISS index + JSON sidecar│
│   ingest.py / retriever.py          embed+add / top-k search  │
├─────────────────────────────────────────────────────────────┤
│ streamlit_app/models/resnet9.py     Re-exports the vision     │
│                                      model from backend/       │
├─────────────────────────────────────────────────────────────┤
│ streamlit_app/core/                 db.py (sqlite), auth.py   │
│                                      (bcrypt), ui.py (theme),  │
│                                      model_loader.py (cached)  │
└─────────────────────────────────────────────────────────────┘
```

## Request flow

**Detect Disease**: uploaded image → `backend.models.resnet9.preprocess_image` →
`ResNet9.forward` (cached via `st.cache_resource`) → softmax → predicted class → Grad-CAM on
`model.res2` → `backend.agent.tools.lookup_disease` for symptoms/measures → rendered in
`views/2_Detect_Disease.py`, logged to sqlite (`prediction_log`), and stashed in
`st.session_state["detected_disease"]` so the Chat page can pick it up as context.

**AI Chat** (`agents/orchestrator.run_turn`):
1. **Memory Agent** recalls recent turns from sqlite.
2. **Planner Agent** makes one cheap LLM call to decide if this turn needs RAG grounding.
3. **Research Agent** (if flagged) embeds the query and searches the knowledge-base FAISS
   collection plus the current chat session's private document collection; results are injected
   as a system message.
4. **Response Agent** runs the OpenAI function-calling loop (tools from **Tool Agent** —
   `lookup_disease`, `get_dashboard_stats` — and **API Agent** — `get_weather` via Open-Meteo,
   no key required) until the model stops calling tools, then makes one final `stream=True` call
   (no `tools` param, so it's guaranteed to return plain text) that is rendered token-by-token via
   `st.write_stream`.
5. **Memory Agent** persists both sides of the turn.

Net LLM calls per turn: 1 (planner) + 1–2 (response agent's tool loop) + 1 (final streamed
answer) — comparable to the original single-tool agent, but modular: new tools or agents plug
into the registry without touching the orchestrator.

## Vector store: FAISS, not Chroma

The original design used ChromaDB. In this environment, ChromaDB's compiled native extension
segfaulted on every `collection.add()` call — traced to an ABI mismatch with the `numpy<2` pin
this project needs for `torch`/Grad-CAM compatibility (see `backend/requirements.txt`). FAISS
(`faiss-cpu`) has no such conflict and was verified working end-to-end with real OpenAI
embeddings, so `streamlit_app/rag/vector_store.py` implements a small `FaissCollection` wrapper
(a FAISS `IndexFlatL2` plus a parallel JSON file of `{id, document, metadata}` records) that
exposes the same `get_collection(name).add(...)` / `.query(...)` shape the rest of the RAG code
expects.

## Code reuse (not duplication)

- `streamlit_app/models/resnet9.py` re-exports `backend.models.resnet9` — one model definition.
- `streamlit_app/agents/tool_agent.py` imports `backend.agent.tools.lookup_disease` — one
  knowledge-base lookup, same exact/fuzzy-match behavior as the original FastAPI `/predict` and
  `/chat` endpoints.
- `disease_knowledge_base.json` at the project root is the single source of truth, read by both
  the legacy backend and the new RAG ingestion.

## Persistence

- `data/cropdoc.db` — sqlite: `users`, `chat_sessions`, `chat_messages`, `contact_messages`,
  `prediction_log`.
- `data/vector_store/<collection>/` — FAISS index + metadata per collection: one always-on
  `disease_knowledge_base` collection, plus one `session_<id>_docs` collection per chat session
  that has had documents uploaded to it.
