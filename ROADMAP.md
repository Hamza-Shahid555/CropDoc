# Roadmap

## Done (this rebuild)

- [x] Multi-page Streamlit app with custom theme, sidebar nav, dark/light aware CSS
- [x] Lightweight sqlite + bcrypt auth (login/register, seeded demo account)
- [x] Detect Disease page reusing the existing ResNet9 + Grad-CAM pipeline
- [x] RAG pipeline: PDF/DOCX/TXT/MD/CSV ingestion, chunking, FAISS vector store
- [x] Disease knowledge base auto-embedded into a default FAISS collection
- [x] Six-agent chat system (Planner, Research, Tool, API, Memory, Response) with streaming
- [x] Multi-session chat with per-session document isolation, download/clear chat
- [x] Live usage dashboard (model eval charts + sqlite-backed stats)
- [x] Home, Features, Documentation, About, Contact, Settings pages
- [x] Consolidated `requirements.txt` and `.env.example`
- [x] This documentation set

## Known gaps / not implemented

- **No automated tests.** None existed in the repository before this rebuild either. Given the
  scope of this change, adding a test suite (pytest for `core/db.py`, `rag/chunking.py`,
  `agents/*` with a mocked OpenAI client) would be the highest-value next step.
- **No CI pipeline.** Nothing currently runs tests/lint on push.
- **Single-file sqlite, single-process FAISS.** Fine for a demo/single deployment; would need a
  real database + managed vector store (or at least file-locking) to run multiple app instances
  behind a load balancer.
- **No rate limiting.** See `SECURITY.md`.
- **No password reset / email verification.** See `SECURITY.md`.
- **Legacy `backend/` + `frontend/` are unmaintained by this rebuild going forward** — they still
  work standalone but won't receive new features; the Streamlit app is the primary product now.

## Possible next steps

1. Add a pytest suite covering `core/db.py` repository functions, `rag/chunking.py` edge cases,
   and the orchestrator with a mocked OpenAI client (no real API calls in CI).
2. Add per-user API rate limiting (e.g. a simple sqlite-backed token bucket) before any public
   deployment.
3. Support image uploads inside the AI Chat page itself (currently image upload is Detect Disease
   -only; the chat page accepts documents but not photos), so a user can drop a leaf photo
   mid-conversation instead of switching pages.
4. Replace the bcrypt/sqlite auth with a proper session-signing mechanism using `APP_SECRET` if
   this is ever deployed multi-instance (currently unused — see `SECURITY.md`).
5. Retire or clearly archive `backend/`, `frontend/`, `Guide.txt`, and the old root
   `requirements.txt`/`.streamlit/config.toml` once the Streamlit app is confirmed as the FYP
   submission's primary deliverable, to avoid confusing future readers about which stack is live.
