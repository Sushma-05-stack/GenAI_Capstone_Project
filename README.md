# Enterprise RAG Evaluation Dashboard

A production-ready platform for evaluating Retrieval-Augmented Generation (RAG) systems using **RAGAS metrics** with **multi-LLM fallback routing**, full analytics, and enterprise security.

---

## Architecture

```
┌─────────────────┐     ┌─────────────────────────────────────┐
│  Next.js 14      │────▶│  FastAPI Backend                     │
│  React + TS      │     │  ├── Auth (JWT + RBAC)              │
│  Tailwind CSS    │     │  ├── Document Pipeline              │
│  Recharts        │     │  ├── RAG Pipeline + LangSmith       │
└─────────────────┘     │  ├── Multi-LLM Router               │
                         │  ├── RAGAS Evaluation Engine        │
                         │  └── Analytics + Reports            │
                         └─────────┬───────────────────────────┘
                                   │
                    ┌──────────────┴──────────────┐
                    │                             │
              ┌─────▼──────┐             ┌───────▼──────┐
              │ MongoDB     │             │  ChromaDB    │
              │ Atlas       │             │  (Vectors)   │
              └────────────┘             └──────────────┘
```

## Features

- **Authentication**: JWT, RBAC (Admin/Evaluator/Viewer), password reset
- **Dataset Management**: Upload PDF, DOCX, TXT, CSV; QA test sets; versioning
- **Document Pipeline**: Extract → Clean → Chunk → Embed → ChromaDB index
- **RAG Pipeline**: Semantic retrieval + prompt construction + LLM generation
- **Multi-LLM Fallback**: OpenAI → Gemini → Groq → Claude with auto-routing
- **RAGAS Evaluation**: Faithfulness, Answer Relevancy, Context Precision/Recall, Hallucination Risk
- **Prompt Versioning**: Library, A/B comparison with metric deltas
- **Model Benchmarking**: Side-by-side comparison tables and radar charts
- **Analytics Dashboard**: Trend lines, pie charts, heatmaps, hallucination reports
- **LangSmith Integration**: Full trace observability per evaluation run
- **Security**: Prompt injection detection, rate limiting, audit logs, input/output validation
- **Reports**: Export to PDF, CSV, Excel
- **Feedback System**: Rate responses, flag hallucinations

---

## Quick Start

### Prerequisites
- Python 3.11+
- Node.js 20+
- MongoDB Atlas (or local MongoDB)

### Backend Setup

```bash
cd backend
python -m venv venv
venv\Scripts\activate          # Windows
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your API keys
uvicorn app.main:app --reload --port 8000
```

### Frontend Setup

```bash
cd frontend
npm install
# Create .env.local
echo "NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1" > .env.local
npm run dev
```

### Docker (Full Stack)

```bash
cp backend/.env.example backend/.env
# Edit backend/.env with API keys
docker-compose up --build
```

Open http://localhost:3000

---

## API Documentation

Available at http://localhost:8000/docs (Swagger UI, dev mode only)

### Key Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/auth/register` | Register new user |
| POST | `/api/v1/auth/login` | Login, get JWT |
| GET | `/api/v1/datasets/` | List datasets |
| POST | `/api/v1/datasets/{id}/upload` | Upload document |
| POST | `/api/v1/rag/query` | RAG query |
| POST | `/api/v1/evaluation/run` | Start evaluation |
| GET | `/api/v1/evaluation/history` | Eval run history |
| GET | `/api/v1/evaluation/{id}/results` | Per-question results |
| POST | `/api/v1/prompts/compare` | A/B prompt comparison |
| GET | `/api/v1/models/compare?run_ids=a,b` | Model benchmarking |
| GET | `/api/v1/dashboard/summary` | KPI summary |
| GET | `/api/v1/dashboard/trends` | Time-series trends |
| GET | `/api/v1/reports/export/pdf?run_id=` | PDF report |
| GET | `/api/v1/reports/export/excel?run_id=` | Excel report |
| GET | `/api/v1/security/logs` | Audit logs (admin) |

---

## RAGAS Metrics Explained

| Metric | Description | Range |
|--------|-------------|-------|
| **Faithfulness** | Is the answer grounded in the retrieved context? | 0–1 (higher = better) |
| **Answer Relevancy** | Is the answer relevant to the question? | 0–1 (higher = better) |
| **Context Precision** | Are retrieved chunks relevant? | 0–1 (higher = better) |
| **Context Recall** | Does context cover the ground truth? | 0–1 (higher = better) |
| **Hallucination Risk** | `1 - Faithfulness` — likelihood of fabrication | 0–1 (lower = better) |
| **Retrieval Quality** | F1 of Context Precision and Recall | 0–1 (higher = better) |

---

## Environment Variables

See `backend/.env.example` for the full list. Required keys:
- `SECRET_KEY` — JWT signing secret
- `MONGODB_URL` — MongoDB Atlas connection string
- `OPENAI_API_KEY` — Required for embeddings and default LLM
- `LANGCHAIN_API_KEY` — Optional, for LangSmith tracing

At least one of `OPENAI_API_KEY`, `GOOGLE_API_KEY`, or `GROQ_API_KEY` must be set.

---

## Deployment

### Backend → Render
1. Connect GitHub repo
2. Set build command: `pip install -r requirements.txt`
3. Set start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
4. Add all environment variables from `.env`

### Frontend → Vercel
1. Import frontend directory
2. Set `NEXT_PUBLIC_API_URL` to your Render backend URL
3. Deploy

### Database → MongoDB Atlas
1. Create free M0 cluster
2. Copy connection string to `MONGODB_URL`
3. Whitelist Render IP (or 0.0.0.0/0 for dev)

---

## Resume Bullets

- Built enterprise RAG Evaluation Dashboard with **FastAPI + Next.js** evaluating RAG outputs using **RAGAS** (faithfulness, answer relevancy, context precision/recall, hallucination risk)
- Implemented **multi-LLM fallback router** (OpenAI → Gemini → Groq → Claude) with automatic failover on timeout/rate-limit, reducing evaluation downtime by eliminating single-provider dependency
- Designed **document ingestion pipeline** (PDF/DOCX/TXT/CSV → chunking → OpenAI embeddings → ChromaDB) supporting semantic retrieval at scale
- Integrated **LangSmith observability** for full prompt trace logging across all RAG evaluation runs
- Built **JWT + RBAC auth system** (Admin/Evaluator/Viewer) with audit logging, prompt injection detection, and rate limiting
- Created **prompt A/B comparison** engine measuring faithfulness/relevancy/latency deltas across prompt versions
- Developed **analytics dashboard** with time-series trend charts (Recharts), model usage distribution, and hallucination risk reports
- Added **multi-format report export** (PDF/CSV/Excel) using ReportLab and OpenPyXL
