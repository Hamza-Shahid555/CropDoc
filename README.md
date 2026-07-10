 **CropDoc** 

This version dives deeply into your codebase architecture (such as the PyTorch vs ONNX models, the SQLite database schema, the internal mechanics of the RAG pipeline, and the Grad-CAM visualization engine), making it perfect for your final year project (FYP) evaluation or a professional portfolio.

---

```markdown
# CropDoc: AI-Powered Agricultural Diagnostics & Consultation Platform 🌾🔍

CropDoc is an enterprise-grade, end-to-end artificial intelligence application designed for smart agriculture. It bridges the gap between deep learning computer vision and generative AI to assist farmers, agronomists, and researchers. 

The platform offers a dual-engine architecture: an **Instant Disease Diagnostics Engine** powered by an optimized **ResNet9** model featuring **Grad-CAM visual explainability**, and an **Intelligent Agricultural Consultation Engine** powered by **Retrieval-Augmented Generation (RAG)** linked with an internal agronomy knowledge base.

---

## 🚀 Key Architectural Modules

### 1. Computer Vision & Explainable AI (XAI)
* **Custom ResNet9 Architecture:** Optimized Residual Network designed for fast execution and high accuracy on localized leaf edge patterns, outperforming heavy models like ResNet50 in low-resource environments.
* **Dual-Inference Assets:** Features raw weights (`cropdoc_resnet9.pth`) for deep development and an **Open Neural Network Exchange** format (`cropdoc_resnet9.onnx`) with serialized parameters (`cropdoc_resnet9.onnx.data`) for rapid deployment across high-performance runtimes.
* **Grad-CAM Implementation:** Rather than acting as an obscure "black box," the system processes forward and backward passes across final convolutional feature layers to render a heatmap (`gradcam_samples.png`), highlighting exactly *where* the neural network detected symptoms.

### 2. Retrieval-Augmented Generation (RAG) Chatbot
* **Structured Knowledge Base:** Integrates a local semantic matrix (`disease_knowledge_base.json`) detailing verified agricultural remediation workflows, pesticide recommendations, and structural crop data.
* **Dynamic PDF Document Ingestion:** Users can upload custom agricultural manuals or localized crop research documents during their live chat. The app fragments, processes, and stores document segments as vectors on disk inside localized session directories (`data/vector_store/session_<id>_docs/`).
* **Context-Aware Synthesis:** Combines retrieved knowledge blocks with OpenAI embeddings and LLM APIs to generate conversational answers free of hallucinated content.

### 3. Core Security & Session Persistence
* **State Management:** Uses a secure SQLite relational engine (`data/cropdoc.db`) to record comprehensive user actions, user accounts, application logs, and chat contexts.
* **Cryptographic Hardening:** User credential pipelines (`streamlit_app/core/auth.py`) utilize **Bcrypt** password hashing with computational salt factors.

---

## 📂 Detailed Repository Topology

```text
├── .devcontainer/             # Isolated environment definitions for VS Code development
├── .streamlit/                # App custom themes and configuration settings
├── backend/                   # Standalone FastAPI production backend engine
│   ├── .env                   # Ignored secure operational backend secrets
│   └── ...                    # Legacy microservice routers and CORS handling configurations
├── frontend/                  # Separated decoupled web layout files (SPA prototype)
├── streamlit_app/             # Active production monolithic web application structure
│   ├── app.py                 # Primary framework entry-point orchestration file
│   ├── core/                  # Core modules (auth.py, db.py, ui.py, vector_store.py)
│   └── views/                 # Isolated application views
│       ├── 1_Dashboard.py     # Analytics engine & historical diagnostics data tracking
│       ├── 2_Detect_Disease.py# CNN Inference processing, ONNX execution, and Grad-CAM layers
│       └── 3_AI_Chat.py       # Conversational LLM RAG chat engine interface
├── data/                      # Data storage layer
│   ├── cropdoc.db             # Local relational data file (unencrypted SQLite binary)
│   └── vector_store/          # Dynamic collection paths for embedded document chunks
├── CropDoc_Training.ipynb     # Interactive Jupyter training code for your ResNet9 pipeline
├── fyp-final.ipynb            # Final year project testing, dataset curation, and analysis log
├── disease_knowledge_base.json# Aggregated agricultural knowledge base data
├── requirements.txt           # Unified external Python dependencies manifests
└── run.ps1                    # Native multi-platform PowerShell automation startup script

```

---

## 📊 Model Evaluation & Metrics Documentation

The deep learning pipeline has been validated across extensive target image vectors. Performance logs and plots available in the repository root include:

| Artifact | Purpose | Description |
| --- | --- | --- |
| `training_history.png` | Optimization Tracking | Plots Training vs. Validation Loss and Accuracy convergence curves across epochs. |
| `confusion_matrix.png` | Error Matrix Analysis | Visualizes class-to-class classification discrepancies and identifies misclassification risks. |
| `class_distribution.png` | Balance Auditing | Charts dataset distribution balances to monitor and address class bias during training. |
| `per_class_accuracy.png` | Granular Precision Logs | Identifies specific plant-disease categories requiring dataset supplementation or refinement. |
| `classification_report.txt` | Standard Metrics | Contains raw statistical breakdowns for precision, recall, and $F_1\text{-score}$ across all classes. |

---

## 🛠️ Installation & Setup Execution

### Local Environment Setup

#### 1. Clone the Source Repository

```bash
git clone [https://github.com/Hamza-Shahid555/CropDoc.git](https://github.com/Hamza-Shahid555/CropDoc.git)
cd CropDoc

```

#### 2. Configure Environment Parameters

Create your environment configuration file from the provided boilerplate example:

```bash
cp .env.example .env

```

Open the generated `.env` file and insert your respective OpenAI secret key parameters:

```env
OPENAI_API_KEY=sk-proj-YourActualOpenAiAPIKeyGgoesHere...

```

#### 3. Install Required Dependencies

Initialize clean environment scopes and execute global requirements parsing:

```bash
pip install -r requirements.txt

```

---

## 🚀 Running the Platform

### Option A: Automating with PowerShell (Windows/Cross-platform)

For streamlined execution that handles initial configurations automatically, run the built-in PowerShell pipeline:

```powershell
./run.ps1

```

### Option B: Manual Monolithic Bootstrapping

If you prefer manual execution via the command-line interface, launch the Streamlit server directly:

```bash
streamlit run streamlit_app/app.py

```

### Option C: Decoupled Multi-tier Microservice Setup

To separate the backend processing layer from your UI engine, run the FastAPI application alongside the frontend framework:

```bash
uvicorn backend.main:app --reload --port 8000

```

---

## 🔒 Security Posture & Operational Safeguards

As outlined in [SECURITY.md](https://www.google.com/search?q=./SECURITY.md), keep the following architectural constraints in mind before moving to a public deployment:

* **Demo Account Cleanup:** A pre-seeded database user identity configuration (`demo` / `demo1234`) exists inside the database for quick grading. **Remove this seed block** prior to deploying the app to an open server environment.
* **Vector Data Footprint:** Uploaded documents are converted to embeddings on disk. Deleting a chat session inside the Streamlit user interface correctly purges these vectors using `vector_store.delete_collection`. However, deleting rows directly from the SQLite database will result in orphaned vector files on disk.
* **Rate Limiting:** The image processing and RAG chat engines currently do not limit incoming traffic natively. When deploying publicly, wrap the services in a reverse proxy (such as Nginx or Cloudflare) to prevent API abuse or resource exhaustion.

```

***

