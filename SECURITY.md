# Security

## Authentication

- Username/password accounts stored in sqlite (`data/cropdoc.db`, `users` table), passwords
  hashed with bcrypt (`streamlit_app/core/auth.py`). No plaintext passwords are stored or logged.
- A seeded demo account (`demo` / `demo1234`) exists so the app is immediately usable. **Change or
  remove this before any public deployment** — anyone can log in with it.
- Session state is per-browser-session (Streamlit's default) — there is no persistent "remember
  me" cookie or JWT. A full page reload starts a fresh, logged-out session.
- No password reset flow, no email verification, no rate limiting on login attempts. Acceptable
  for a single-user/demo deployment; not sufficient for a public multi-tenant product.

## Secrets

- `OPENAI_API_KEY` is read from `backend/.env` and/or a root `.env`, both listed in `.gitignore`
  (verified: `backend/.env` was already excluded). Never commit either file.
- `APP_SECRET` in `config.py` is currently unused by any signing/encryption logic — it's a
  placeholder for future session-signing needs, not a security boundary today.
- `.env.example` documents required variable names without real values — safe to commit.

## Data handling

- Uploaded documents (for RAG) are stored as embedded chunks in
  `data/vector_store/session_<id>_docs/` and are **not automatically deleted** when a chat session
  is deleted from the UI's session list unless that delete path runs (it does — see
  `views/3_AI_Chat.py`'s 🗑️ button, which calls `vector_store.delete_collection`). Manually
  removing a session row from the database without going through the UI would leave orphaned
  vector data on disk.
- Uploaded document text is sent to OpenAI's embeddings API and (via retrieved context) the chat
  completions API. Don't upload anything confidential you don't want processed by a third-party
  LLM provider.
- The sqlite database is a single unencrypted file. Anyone with filesystem access to the server
  can read all chat history, contact messages, and prediction logs.

## Network / deployment

- No rate limiting on the Detect Disease or AI Chat pages — a public deployment could have its
  OpenAI quota exhausted or its CPU (Grad-CAM is a forward+backward pass) hammered by anyone with
  the URL. Consider a reverse-proxy rate limit if deploying publicly.
- The legacy FastAPI backend's CORS defaults to `http://localhost:3000` unless `ALLOWED_ORIGINS`
  is set — not relevant to the Streamlit app (no CORS surface), but relevant if you also deploy
  `backend/` standalone.
- No input size limit is enforced on uploaded images/documents beyond Streamlit's own default
  (200MB/file) — large uploads could cause memory pressure.

## Known gaps (not implemented — flagged rather than silently skipped)

- No automated test suite exists in this repository (confirmed during the Streamlit rebuild — none
  were present before it, either). See `ROADMAP.md`.
- No structured logging/monitoring; errors surface only in the Streamlit server console.
- No CSRF/XSS-specific hardening beyond what Streamlit provides by default, since all rendering
  goes through `st.markdown(..., unsafe_allow_html=True)` in a few UI-helper spots
  (`core/ui.py`) — those calls only ever render strings this codebase constructs itself, never
  raw user input, so this is safe as written; keep it that way if extending those helpers.
