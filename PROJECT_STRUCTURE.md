# Project Structure

```
New folder/                              (project root)
├── streamlit_app/                       Primary application
│   ├── app.py                           Entrypoint: page config, auth gate, sidebar, nav
│   ├── config.py                        Env loading, paths, model settings
│   ├── theme/style.css                  Custom CSS (cards, palette, animations)
│   ├── core/
│   │   ├── db.py                        sqlite schema + repository functions
│   │   ├── auth.py                      bcrypt login/register/session gate
│   │   ├── ui.py                        Reusable UI helpers (cards, badges, metric tiles)
│   │   └── model_loader.py              st.cache_resource-wrapped ResNet9 loader
│   ├── models/resnet9.py                Re-exports backend.models.resnet9
│   ├── rag/
│   │   ├── loaders.py                   PDF/DOCX/TXT/MD/CSV → plain text
│   │   ├── chunking.py                  Paragraph-aware recursive text splitter
│   │   ├── vector_store.py              FAISS collection wrapper + OpenAI embeddings
│   │   ├── ingest.py                    File/KB → chunks → embedded → indexed
│   │   └── retriever.py                 Top-k similarity search
│   ├── agents/
│   │   ├── orchestrator.py              Ties all agents together for one chat turn
│   │   ├── planner.py                   Planner Agent (needs_research? — 1 LLM call)
│   │   ├── research_agent.py            Research Agent (FAISS search, no LLM call)
│   │   ├── tool_agent.py                Tool Agent (lookup_disease, get_dashboard_stats)
│   │   ├── api_agent.py                 API Agent (get_weather via Open-Meteo)
│   │   ├── memory_agent.py              Memory Agent (sqlite recall/persist)
│   │   ├── response_agent.py            Response Agent (tool loop + streamed answer)
│   │   └── tools.py                     Aggregates tool_agent + api_agent registries
│   └── views/                           Pages (Streamlit st.Page/st.navigation)
│       ├── 1_Home.py
│       ├── 2_Detect_Disease.py
│       ├── 3_AI_Chat.py
│       ├── 4_Dashboard.py
│       ├── 5_Features.py
│       ├── 6_Documentation.py
│       ├── 7_About.py
│       ├── 8_Contact.py
│       └── 9_Settings.py
│
├── backend/                             Legacy FastAPI backend (still functional, standalone)
│   ├── main.py                          FastAPI app: /predict, /chat, /health
│   ├── models/resnet9.py                Original ResNet9 + Grad-CAM implementation (reused above)
│   ├── agent/agent.py, tools.py         Original single-tool OpenAI agent
│   ├── routes/predict.py, chat.py
│   └── .env                             OPENAI_API_KEY (gitignored)
│
├── frontend/                            Legacy Next.js frontend (still functional, standalone)
│   ├── app/, components/, lib/api.ts
│   └── package.json
│
├── data/                                Runtime data (gitignored)
│   ├── cropdoc.db                       sqlite database
│   └── vector_store/                    FAISS indexes + metadata, one dir per collection
│
├── disease_knowledge_base.json          38-entry disease knowledge base (shared source of truth)
├── cropdoc_resnet9.pth                  Trained model checkpoint
├── cropdoc_resnet9.onnx(.data)          ONNX export
├── *.png, classification_report.txt     Training evaluation artifacts (shown on Dashboard)
├── CropDoc_Training.ipynb               Kaggle training notebook
├── CropDoc_FYP_Report.docx              Academic report
├── local_inference.py                   Standalone CLI inference script
├── requirements.txt                     Consolidated dependencies for streamlit_app/
└── .env.example                         Documented environment variables
```

## Naming notes

- `streamlit_app/views/` (not `pages/`) — Streamlit auto-discovers a `pages/` directory next to
  the entrypoint and injects its own sidebar navigation, which conflicts with the explicit
  `st.navigation`/`st.Page` routing used here (it showed nav links before login). Renaming the
  directory avoids that.
- `Guide.txt`, root `.streamlit/config.toml`, and the old root `requirements.txt` describe an even
  earlier prototype (`app.py` + `chatbot.py`) that no longer exists in this repo. They're left in
  place but superseded by this documentation set.
