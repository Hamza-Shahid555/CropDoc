# CropDoc: AI-Powered Agricultural Diagnostics & Consultation Platform 🌾🔍

CropDoc is an enterprise-grade, end-to-end artificial intelligence application designed for smart agriculture. It bridges the gap between deep learning computer vision and generative AI to assist farmers, agronomists, and researchers.

The platform offers a dual-engine architecture:

- **Instant Disease Diagnostics Engine** powered by an optimized **ResNet9** model with **Grad-CAM** visual explainability.
- **Intelligent Agricultural Consultation Engine** powered by **Retrieval-Augmented Generation (RAG)** integrated with an agricultural knowledge base.

---

# 🚀 Key Architectural Modules

## 1. Computer Vision & Explainable AI (XAI)

### Custom ResNet9 Architecture
- Lightweight residual neural network optimized for crop disease classification.
- Faster inference than larger models (e.g., ResNet50).
- Suitable for deployment on low-resource devices.
- Trained specifically on agricultural leaf disease datasets.

### Dual Model Formats

The project provides two deployment formats:

| File | Purpose |
|------|----------|
| `cropdoc_resnet9.pth` | PyTorch model for training and experimentation |
| `cropdoc_resnet9.onnx` | Optimized ONNX model for production inference |
| `cropdoc_resnet9.onnx.data` | Serialized weights used by ONNX runtime |

### Grad-CAM Explainability

CropDoc includes **Gradient-weighted Class Activation Mapping (Grad-CAM)** which visualizes where the neural network focused during prediction.

Instead of acting as a black-box model, Grad-CAM generates a heatmap highlighting infected regions of the leaf.

Example output:

```
Input Image
      ↓
ResNet9 Prediction
      ↓
Backward Pass
      ↓
Feature Importance
      ↓
Grad-CAM Heatmap
```

Sample visualization:

```
gradcam_samples.png
```

---

# 2. Intelligent Agricultural Chatbot (RAG)

The chatbot uses **Retrieval-Augmented Generation (RAG)** to answer agricultural questions using trusted information instead of relying only on an LLM.

## Knowledge Sources

- `disease_knowledge_base.json`
- Uploaded PDF documents
- Agricultural manuals
- Research papers

## RAG Pipeline

```
User Question
      ↓
Embedding Generation
      ↓
Similarity Search
      ↓
Relevant Chunks Retrieved
      ↓
Prompt Construction
      ↓
OpenAI LLM
      ↓
Final Response
```

## Dynamic PDF Upload

Users can upload custom agricultural documents during chat.

Uploaded PDFs are:

1. Parsed
2. Split into chunks
3. Embedded into vectors
4. Stored locally

Example directory:

```
data/vector_store/session_<id>_docs/
```

---

# 3. Security & Authentication

CropDoc includes secure authentication features.

## SQLite Database

```
data/cropdoc.db
```

Stores:

- User accounts
- Chat history
- Login records
- Predictions
- Application logs

## Password Security

Passwords are never stored in plain text.

Authentication uses:

- Bcrypt hashing
- Salted passwords
- Secure verification

Implemented in:

```
streamlit_app/core/auth.py
```

---

# 📂 Project Structure

```text
├── .devcontainer/
│
├── .streamlit/
│
├── backend/
│   ├── .env
│   └── ...
│
├── frontend/
│
├── streamlit_app/
│   ├── app.py
│   ├── core/
│   │   ├── auth.py
│   │   ├── db.py
│   │   ├── ui.py
│   │   └── vector_store.py
│   │
│   └── views/
│       ├── 1_Dashboard.py
│       ├── 2_Detect_Disease.py
│       └── 3_AI_Chat.py
│
├── data/
│   ├── cropdoc.db
│   └── vector_store/
│
├── CropDoc_Training.ipynb
├── fyp-final.ipynb
├── disease_knowledge_base.json
├── requirements.txt
└── run.ps1
```

---

# 📊 Model Evaluation

The repository includes multiple evaluation artifacts.

| File | Description |
|------|-------------|
| `training_history.png` | Training vs Validation Accuracy/Loss |
| `confusion_matrix.png` | Classification error visualization |
| `class_distribution.png` | Dataset balance visualization |
| `per_class_accuracy.png` | Accuracy for every disease class |
| `classification_report.txt` | Precision, Recall and F1-Score |

---

# 🛠️ Installation

## 1. Clone Repository

```bash
git clone https://github.com/Hamza-Shahid555/CropDoc.git

cd CropDoc
```

---

## 2. Create Environment File

```bash
cp .env.example .env
```

Edit `.env`

```env
OPENAI_API_KEY=sk-proj-your_api_key
```

---

## 3. Install Dependencies

```bash
pip install -r requirements.txt
```

---

# 🚀 Running CropDoc

## Option 1 (Recommended)

Run using PowerShell:

```powershell
./run.ps1
```

---

## Option 2

Run Streamlit directly:

```bash
streamlit run streamlit_app/app.py
```

---

## Option 3

Run backend separately:

```bash
uvicorn backend.main:app --reload --port 8000
```

---

# 🔒 Security Notes

Before public deployment:

- Remove the default demo account:
  ```
  Username: demo
  Password: demo1234
  ```

- Uploaded documents are converted into vector embeddings and stored on disk.

- Deleting chat sessions from the UI removes corresponding vectors.

- Deleting SQLite rows manually may leave orphaned vector files.

- Add rate limiting (e.g., Nginx or Cloudflare) before exposing the application publicly.

---

# 🧠 Technologies Used

### Machine Learning
- PyTorch
- ONNX Runtime
- ResNet9
- Grad-CAM

### AI & NLP
- OpenAI API
- Retrieval-Augmented Generation (RAG)
- Embeddings
- Vector Search

### Backend
- Python
- Streamlit
- FastAPI
- SQLite

### Security
- Bcrypt Password Hashing

### Development
- Jupyter Notebook
- PowerShell
- Git

---

# 📈 Core Features

- 🌿 Plant disease detection from leaf images
- 🔥 Grad-CAM explainable AI visualization
- 🤖 AI agricultural assistant
- 📚 Retrieval-Augmented Generation (RAG)
- 📄 PDF document upload and semantic search
- 🗄️ SQLite database management
- 🔐 Secure authentication using Bcrypt
- 📊 Dashboard with prediction history
- ⚡ ONNX optimized inference
- 💬 Conversational AI support

---

# 🎯 Future Improvements

- Multi-language farmer support
- Mobile application
- Cloud deployment
- Real-time weather integration
- IoT sensor connectivity
- Larger agricultural knowledge base
- Multi-crop disease detection
- Voice-based AI assistant

---

# 📜 License

This project was developed as a **Final Year Project (FYP)** and serves as an AI-powered agricultural diagnostic and consultation platform for educational and research purposes.
