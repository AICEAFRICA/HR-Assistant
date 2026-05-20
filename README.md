# HR Agent — AI-Powered HR Management System

An intelligent HR assistant built with FastAPI, Streamlit, and Google Gemini. Provides RAG-based policy Q&A, leave management, employee services, analytics, and automated document generation. Backed by PostgreSQL + pgvector for hybrid semantic and structured data queries.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│  Browser / API Client                                       │
└───────────┬────────────────────────────────┬────────────────┘
            │ :8501 (Streamlit)              │ :8001 (FastAPI)
┌───────────▼───────────┐       ┌────────────▼────────────────┐
│   frontend/app.py     │       │   backend/main.py            │
│   Streamlit UI        │──────▶│   REST API + Swagger         │
└───────────────────────┘       └────────────┬────────────────┘
                                             │
                         ┌───────────────────┼──────────────────┐
                         │                   │                  │
               ┌─────────▼──────┐  ┌─────────▼──────┐  ┌──────▼──────┐
               │  RAG Engine    │  │  HR Analytics  │  │  Document   │
               │  (Gemini +     │  │  Leave Mgmt    │  │  Generator  │
               │   pgvector)    │  │  Employee Svcs │  │  (Jinja2)   │
               └────────────────┘  └────────────────┘  └─────────────┘
                                             │
                              ┌──────────────▼──────────────┐
                              │  nginx proxy  :80            │
                              │  (strips /rest/v1 prefix)   │
                              └──────────────┬──────────────┘
                                             │
                              ┌──────────────▼──────────────┐
                              │  PostgREST  :3000            │
                              │  (REST API over PostgreSQL)  │
                              └──────────────┬──────────────┘
                                             │
                              ┌──────────────▼──────────────┐
                              │  PostgreSQL + pgvector       │
                              │  (hr_db — tables + vectors)  │
                              └─────────────────────────────┘
```

---

## Project Structure

```
hr-agent/
├── backend/                    # FastAPI application
│   ├── main.py                 # App entry point, routes, Pydantic models
│   └── services/               # Business logic layer
│       ├── knowledge_base.py   # Supabase/PostgREST client + storage
│       ├── rag_engine.py       # RAG with Gemini + pgvector
│       ├── query_router.py     # Intent detection → RAG or structured query
│       ├── hr_analytics.py     # Headcount, attrition, appraisals
│       ├── performance_analytics.py  # Quarterly performance index
│       ├── leave_management.py # Leave requests and approvals
│       ├── employee_services.py # Insurance, shares, compliance, career
│       ├── document_generator.py # Jinja2-based document generation
│       └── document_processor.py # PDF/DOCX text extraction for RAG
├── frontend/                   # Streamlit UI
│   ├── app.py                  # Role-based entry point (Employee / HR)
│   └── hr_dashboard.py         # Live analytics dashboard component
├── database/                   # Database setup
│   ├── init_extensions.sql     # pgvector, citext, uuid-ossp extensions
│   └── migrations/             # Future schema migrations
├── infra/                      # Infrastructure configuration
│   └── nginx/
│       ├── nginx.conf          # Production reverse proxy
│       └── postgrest.conf      # Dev proxy (strips /rest/v1 for supabase-py)
├── scripts/                    # Utility / one-off scripts
│   ├── regenerate_kb.py        # Rebuild knowledge base chunks
│   └── process_hr_documents.py # Ingest HR documents from storage
├── tests/                      # Test suite
│   ├── test_api.py             # API endpoint tests
│   ├── test_rag.py             # RAG engine tests
│   └── test_routing.py         # Query router tests
├── templates/                  # Jinja2 document templates
│   ├── letters/
│   ├── certificates/
│   ├── contracts/
│   └── reports/
├── Dockerfile                  # Backend container
├── Dockerfile.streamlit        # Frontend container
├── docker-compose.yml          # Production stack
├── docker-compose.dev.yml      # Local dev stack (includes DB + PostgREST)
├── requirements.txt
└── .env.example
```

---

## Quick Start — Local Development (Docker)

### Prerequisites
- Docker Desktop
- A [Google Gemini API key](https://aistudio.google.com/app/apikey)

### 1. Clone and configure

```bash
git clone https://github.com/your-org/hr-agent.git
cd hr-agent
cp .env.example .env
# Edit .env — set GEMINI_API_KEY at minimum
```

### 2. Load the database

Obtain `schema.sql` and `data.sql` from your team lead (not committed — contains employee data).

```bash
# Start only the DB container first
docker compose -f docker-compose.dev.yml up -d db

# Wait for it to be healthy, then load extensions + schema
docker cp database/init_extensions.sql hr-db-local:/tmp/
docker cp schema.sql hr-db-local:/tmp/
docker cp data.sql hr-db-local:/tmp/

docker exec hr-db-local psql -U hr_user -d hr_db -f /tmp/init_extensions.sql
docker exec hr-db-local psql -U hr_user -d hr_db -f /tmp/schema.sql
docker exec hr-db-local psql -U hr_user -d hr_db -f /tmp/data.sql
```

### 3. Start the full stack

```bash
docker compose -f docker-compose.dev.yml up --build
```

| Service | URL |
|---|---|
| Streamlit UI | http://localhost:8501 |
| FastAPI Swagger | http://localhost:8001/api/docs |
| PostgREST | http://localhost:3000 |
| PostgreSQL | localhost:5433 |

---

## Environment Variables

See `.env.example` for the full list. Key variables:

| Variable | Description |
|---|---|
| `GEMINI_API_KEY` | Google Gemini API key (required) |
| `SUPABASE_URL` | PostgREST base URL (cloud or `http://postgrest-proxy` for local) |
| `SUPABASE_KEY` | JWT anon key |
| `SUPABASE_SERVICE_KEY` | JWT service key (bypasses RLS) |

---

## Production Deployment

```bash
# Set all env vars in .env, then:
docker compose up --build -d
```

The production stack (`docker-compose.yml`) expects an external PostgreSQL + PostgREST.
Point `SUPABASE_URL` at your PostgREST instance and supply valid JWT tokens.

---

## Running Tests

```bash
# From repo root
PYTHONPATH=. python -m pytest tests/

# Windows PowerShell
$env:PYTHONPATH="."; python -m pytest tests/
```

---

## Key Design Decisions

- **supabase-py over raw psycopg2** — preserves compatibility with Supabase cloud while enabling self-hosted PostgREST. The nginx proxy (`infra/nginx/postgrest.conf`) strips the `/rest/v1` prefix that `supabase-py` appends automatically.
- **CPU-only PyTorch** — `sentence-transformers` is used for local embeddings. Both Dockerfiles pre-install the CPU wheel to avoid pulling 2 GB of CUDA libraries.
- **pgvector** — vector similarity search (`match_kb_chunks` RPC) runs inside PostgreSQL, no separate vector DB needed.
- **Gemini 2.5 Flash** — used for both query analysis and answer generation in the RAG pipeline.

---

## Contributing

1. Branch from `main`: `git checkout -b feature/your-feature`
2. Keep service logic in `backend/services/`, routes in `backend/main.py`
3. Add tests in `tests/` for new features
4. Run `$env:PYTHONPATH="."; python -m pytest tests/` before opening a PR
5. **Never commit** `.env`, `data.sql`, or `schema.sql`
