# API Documentation

The Streamlit app has no HTTP API of its own — pages call Python functions directly in-process.
"API" here means two things: the **tool registry** the chat assistant can call, and the **legacy
FastAPI endpoints** that still exist in `backend/` for anyone using the old frontend.

## Agent tool registry (`streamlit_app/agents/`)

Exposed to the Response Agent's OpenAI function-calling loop. The model decides when to call
these; they are not directly reachable from the UI.

### `lookup_disease(class_name: str) -> dict`
Source: `backend/agent/tools.py` (reused, not duplicated).
Looks up a disease-knowledge-base entry by exact class name (e.g. `Tomato___Late_blight`), falling
back to a case-insensitive substring match on the human-readable disease name.

Returns: `{class_name, disease_name, affected_crop, is_healthy, symptoms, precautionary_measures}`
or `{"error": "..."}` if not found.

### `get_dashboard_stats() -> dict`
Source: `streamlit_app/core/db.py::get_dashboard_stats`.
Returns live usage stats: `total_predictions`, `total_sessions`, `total_messages`, `top_classes`
(list of `{disease_name, c}`), `healthy_ratio`.

### `get_weather(location: str) -> dict`
Source: `streamlit_app/agents/api_agent.py`. Calls the free Open-Meteo geocoding + forecast APIs
(no API key required). Returns `{location, current, next_3_days}` or `{"error": "..."}`.

## Internal (non-tool) agent functions

These run as part of the orchestrator, not as LLM-callable tools:

| Function | Module | Purpose |
|---|---|---|
| `plan_turn(message) -> {"needs_research": bool}` | `agents/planner.py` | One JSON-mode LLM call deciding if RAG grounding is needed this turn |
| `research(query, session_id) -> list[dict]` | `agents/research_agent.py` | FAISS similarity search over the KB + session document collections |
| `recall(session_id) -> list[dict]` / `remember(session_id, role, content)` | `agents/memory_agent.py` | Read/write chat history in sqlite |
| `generate(messages) -> Generator[str]` | `agents/response_agent.py` | Resolves tool calls, then streams the final answer |
| `run_turn(session_id, user_message, detected_disease) -> Generator[str]` | `agents/orchestrator.py` | Entry point used by the AI Chat page |

## RAG functions (`streamlit_app/rag/`)

| Function | Purpose |
|---|---|
| `loaders.load_any(filename, data: bytes) -> str` | Dispatches to a PDF/DOCX/TXT/MD/CSV loader by extension |
| `chunking.chunk_text(text, chunk_size=800, overlap=100) -> list[str]` | Paragraph-aware splitter |
| `vector_store.get_collection(name) -> FaissCollection` | Get-or-create a FAISS collection |
| `ingest.ingest_document(collection_name, filename, data) -> int` | Load → chunk → embed → index; returns chunk count |
| `ingest.ingest_kb_if_empty() -> int` | Seeds the `disease_knowledge_base` collection on first run |
| `retriever.search(collection_name, query, top_k) -> list[dict]` | Top-k similarity search, one collection |
| `retriever.search_multi(collection_names, query, top_k) -> list[dict]` | Merged top-k across collections |

## Legacy FastAPI backend (`backend/`, unchanged)

Still deployable standalone (see `render.yaml`); not called by the Streamlit app.

### `POST /predict`
`multipart/form-data`, field `file` (image). Returns class name, confidence, disease info, and
three base64 PNGs (`original_image`, `heatmap_image`, `overlay_image`).

### `POST /chat`
`application/json`: `{"message": str, "detected_disease": str | null, "history": [{"role", "content"}]}`.
Returns `{"reply": str}`. Single-tool agent (`lookup_disease` only) — the Streamlit app's
multi-agent version supersedes this for new usage.

### `GET /health`
Returns `{"status": "ok"}`.
