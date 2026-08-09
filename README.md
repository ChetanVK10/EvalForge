# LLMOps Studio — LLM Evaluation, Regression Testing & Release Promotion Platform

LLMOps Studio is an enterprise-grade platform for evaluating LLM outputs, detecting quality/latency/cost regressions between prompt versions or model providers, and automating release promotion decisions.

Built with **React**, **FastAPI**, **PostgreSQL**, **Redis**, and **Docker**, LLMOps Studio transforms LLM evaluation from ad-hoc manual testing into a continuous delivery release gate.

---

## Key Features

- **Dataset & Test Case Management**: Structured dataset curation with category metadata and JSONL import.
- **Prompt Versioning & Model Configurations**: Fine-grained versioning of prompt templates (system/user templates) and provider model configurations.
- **Multi-Provider LLM Gateway**: Standardized inference across **Groq** and **Google Gemini** models with unified latency and token telemetry.
- **Hybrid Evaluation Engine**: Combines deterministic evaluators (Exact Match, Keyword Match, Levenshtein Distance), semantic similarity embeddings, and LLM-as-a-Judge evaluations.
- **Async Experiment Runner & Persistence**: Bounded async execution with progress tracking, error isolation, and full relational telemetry persistence.
- **Regression Engine & Explainable Promotion Gate**: Symmetric case-level and aggregate delta calculations evaluating release safety against configurable quality/factuality regression thresholds.
- **Redis Caching**: Lightweight caching of read-heavy dashboard aggregations with TTL expiration, explicit invalidation, and fail-open PostgreSQL fallback.
- **Production Containerization**: Fully containerized multi-stage Docker builds with Docker Compose orchestration and automated database migrations (`alembic upgrade head`).

---

## System Architecture

```mermaid
graph TD
    Client[React / TypeScript Frontend] -->|REST API| API[FastAPI Application]
    API -->|Read-Heavy Cache| Redis[(Redis Cache)]
    API -->|Relational Persistence| Postgres[(PostgreSQL DB)]

    API --> Runner[Async Experiment Runner]
    Runner --> Gateway[Multi-Provider LLM Gateway]

    Gateway -->|Inference| Groq[Groq API]
    Gateway -->|Inference| Gemini[Google Gemini API]

    Runner --> Engine[Hybrid Evaluation Engine]
    Engine -->|Deterministic| Det[Exact Match / Levenshtein]
    Engine -->|Semantic| Sem[Sentence Transformers]
    Engine -->|LLM Judge| Judge[LLM-as-a-Judge]

    API --> RegEngine[Regression Engine]
    RegEngine --> Gate[Promotion Gate]
    Gate -->|Verdict| Decision[PASS / FAIL Decision]
```

---

## Technology Stack

- **Frontend**: React 19, TypeScript, Vite, TanStack Start (Nitro SSR), Tailwind CSS, shadcn/ui, Recharts.
- **Backend**: Python 3.11, FastAPI, SQLAlchemy 2.0 (ORM), Alembic (Migrations), Pydantic v2.
- **Database & Cache**: PostgreSQL 16, Redis 7 (fail-open cache).
- **LLM Integrations**: Groq SDK (`llama-3.3-70b-versatile`), Google GenAI SDK (`gemini-3.6-flash`, `gemini-3.5-flash`, `gemini-3.5-flash-lite`).
- **Containerization**: Docker, Docker Compose.

---

## Local Development Setup

### 1. Backend Setup

```bash
cd backend
python -m venv .venv
# On Windows: .venv\Scripts\activate  |  On Linux/Mac: source .venv/bin/activate
pip install -r requirements.txt

# Run migrations against local database
alembic upgrade head

# Start FastAPI development server
uvicorn app.main:app --reload --port 8000
```

### 2. Frontend Setup

```bash
# In the repository root:
npm install

# Start Vite development server
npm run dev
```

The frontend will run on `http://localhost:5173` and communicate with the FastAPI backend at `http://localhost:8000/api/v1`.

---

## Docker Compose Quick Start

To launch the complete production stack (PostgreSQL, Redis, FastAPI Backend, Nitro Frontend):

1. **Configure Environment Variables**:
   Copy `.env.example` to `.env` and add your LLM provider keys:

   ```bash
   cp .env.example .env
   ```

   Set `GROQ_API_KEY` and `GEMINI_API_KEY` in `.env`.

2. **Launch Services**:

   ```bash
   docker compose up --build
   ```

3. **Access Services**:
   - **Frontend UI**: `http://localhost:3000`
   - **FastAPI API Docs**: `http://localhost:8000/docs`
   - **Health Check**: `http://localhost:8000/api/v1/health`
   - **Readiness Check**: `http://localhost:8000/api/v1/ready`

---

## Environment Variables

| Variable                      | Description                            | Default / Example                                                   |
| :---------------------------- | :------------------------------------- | :------------------------------------------------------------------ |
| `DATABASE_URL`                | PostgreSQL connection string           | `postgresql+psycopg://postgres:postgres@localhost:5432/llm_evalops` |
| `REDIS_URL`                   | Redis cache connection string          | `redis://localhost:6379/0`                                          |
| `CACHE_ENABLED`               | Toggle Redis cache                     | `true`                                                              |
| `DASHBOARD_CACHE_TTL_SECONDS` | Redis cache TTL for dashboard summary  | `60`                                                                |
| `CORS_ORIGINS`                | Allowed CORS origins (comma-separated) | `http://localhost:5173,http://localhost:3000`                       |
| `GROQ_API_KEY`                | Server-side Groq provider API key      | `gsk_...`                                                           |
| `GEMINI_API_KEY`              | Server-side Gemini provider API key    | `AIza...`                                                           |
| `VITE_API_BASE_URL`           | Frontend API base URL                  | `http://localhost:8000/api/v1`                                      |

---

## Testing

### Backend Unit & Integration Tests

```bash
# Run pytest test suite (66 tests covering DB, Gateway, Evaluators, Regression, Cache)
pytest backend/tests
```

### Frontend Production Build Verification

```bash
npm run build
```

---

## API Overview

- `GET /api/v1/dashboard`: Cached workspace health metrics and regression alerts.
- `GET / POST /api/v1/datasets`: Dataset listing and creation.
- `POST /api/v1/datasets/{id}/cases`: Add individual evaluation case.
- `POST /api/v1/datasets/{id}/import`: Bulk import test cases from JSONL payload.
- `GET / POST /api/v1/configurations/models`: Model configurations list and creation.
- `GET / POST /api/v1/prompts`: Prompt configurations and prompt version management.
- `POST /api/v1/evaluations`: Trigger asynchronous evaluation experiment execution.
- `GET /api/v1/evaluations/{id}/status`: Poll execution progress status.
- `GET /api/v1/experiments`: Experiment execution history.
- `GET /api/v1/experiments/{id}`: Detailed experiment results with case breakdown and judge explanations.
- `POST /api/v1/regressions/compare`: Baseline vs candidate experiment regression analysis and promotion gate evaluation.

---

## Scalability & Production Architecture Notes

- **Redis Read Caching**: Redis caches expensive, read-heavy dashboard aggregation metrics (`dashboard:summary:v1`). The cache automatically invalidates upon experiment completion or new experiment creation, and features **fail-open** fallback to PostgreSQL if Redis is offline.
- **Bounded Async Runner**: Experiment execution uses asyncio concurrency bounds to prevent API rate limiting while maintaining high throughput.
- **Worker Queue Transition Path**: At larger scale, experiment execution can be decoupled from the web application by replacing background tasks with a Redis-backed distributed task queue (e.g., Celery or RQ), allowing API servers and evaluation workers to scale independently.

---

## Resume Story

> Built an end-to-end LLM evaluation and regression platform using React, FastAPI, PostgreSQL, Redis, and Docker. Implemented versioned prompt templates, multi-provider LLM gateway (Groq, Gemini), hybrid evaluation engine (deterministic, semantic, LLM-as-a-Judge), experiment telemetry tracking, regression detection algorithms, explainable promotion gates, and fail-open Redis caching.
