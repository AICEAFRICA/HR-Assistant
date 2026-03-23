# HR AI Assistant

A comprehensive **AI-powered HR Management System** featuring a RAG-based knowledge base, employee self-service portal, document generation, leave management, performance analytics, and a live HR dashboard — all powered by **Google Gemini 2.5 Flash** and **Supabase**.

## ✨ Key Features

| Feature | Description |
|---|---|
| **AI Chat (RAG)** | Ask HR policy questions in natural language — answers are grounded in your uploaded company documents |
| **Intelligent Query Routing** | Automatically routes queries to the right handler: knowledge base, analytics engine, or document generator |
| **HR Dashboard** | Live Plotly-powered analytics: headcount, attrition, probation reviews, appraisals, contract alerts |
| **Performance Analytics** | Quarterly organisational index with weighted scoring across 7 criteria, employee rankings & profiles |
| **Leave Management** | Full lifecycle — employees request leave, HR approves/rejects with notifications |
| **Document Generator** | Generate offer letters, termination letters, and experience certificates in HTML, DOCX, or PDF |
| **Employee Self-Service** | Insurance, stock options, compliance training, governance structure, career development |
| **Role-Based Access** | Separate Employee and HR Personnel views in the Streamlit frontend |

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| **Backend API** | FastAPI, Uvicorn, Pydantic |
| **Frontend** | Streamlit, Plotly |
| **AI / LLM** | Google Gemini 2.5 Flash, Gemini Embeddings (`gemini-embedding-001`, 768-dim) |
| **Database** | Supabase (PostgreSQL + pgvector) |
| **Document Processing** | PyMuPDF, PyPDF2, python-docx, tiktoken |
| **Document Generation** | Jinja2, WeasyPrint / ReportLab (PDF), python-docx (DOCX) |
| **Infrastructure** | Docker, Nginx, CORS middleware |

---

## 🚀 Quick Start

### 1. Clone & Install Dependencies

```powershell
pip install -r requirements.txt
```

### 2. Configure Environment

Create a `.env` file with your credentials:

```env
GEMINI_API_KEY=your_google_gemini_api_key
SUPABASE_URL=your_supabase_project_url
SUPABASE_KEY=your_supabase_anon_key
SUPABASE_SERVICE_KEY=your_service_role_key
```

### 3. Set Up the Database

1. Run `schema_update_gemini.sql` in your Supabase SQL Editor to create the 768-dimensional embedding columns. *(Optional — only needed for fresh setups)*
2. Run `supabase_functions.sql` to install the vector search database functions.

### 4. Process HR Documents

```powershell
python process_hr_documents.py
```

This downloads files from your Supabase storage buckets (`hr_policies`, `hr-docs`, `hr-templates`, `hr-reports`), extracts text (PDF, DOCX, TXT), chunks it, generates embeddings, and stores everything in the `kb_article` / `kb_chunk` tables.

### 5. Start the Application

**Option A — Streamlit Frontend (recommended for quick start):**
```powershell
streamlit run rag_web_app.py
```

**Option B — FastAPI Backend:**
```powershell
uvicorn main:app --reload --port 8000
```
Or use the provided scripts:
```powershell
.\start_server.ps1   # PowerShell
start_server.bat      # Command Prompt
```
Interactive API docs available at `http://localhost:8000/api/docs` (Swagger) and `/api/redoc`.

**Option C — Docker (production):**
```powershell
docker-compose up -d
```
Deploys three services: API (port 8001), Streamlit Frontend (port 8501), and Nginx reverse proxy (ports 80/443).

For development with hot-reload:
```powershell
docker-compose -f docker-compose.dev.yml up
```

---

## 📁 Project Structure

```
├── main.py                  # FastAPI backend (~30 API endpoints)
├── rag_web_app.py           # Streamlit frontend (role-based UI)
├── rag_engine.py            # RAG engine (Gemini + vector search)
├── query_router.py          # Intelligent query routing (data / document / generation)
├── knowledge_base.py        # Supabase vector store client & embeddings
├── document_processor.py    # PDF / DOCX / TXT extraction & chunking
├── process_hr_documents.py  # Batch document ingestion script
├── hr_analytics.py          # Headcount, attrition, probation, appraisals, contracts
├── performance_analytics.py # Quarterly index, weighted scoring, employee profiles
├── leave_management.py      # Leave requests, approval workflow, statistics
├── employee_services.py     # Insurance, shares, compliance, governance, development
├── document_generator.py    # Offer letters, termination letters, certificates
├── hr_dashboard.py          # Live Streamlit dashboard with Plotly charts
├── regenerate_kb.py         # Rebuild the knowledge base from scratch
├── requirements.txt         # Python dependencies
├── .env                     # Environment variables (not committed)
├── Dockerfile               # API container (Python 3.11-slim, multi-stage)
├── Dockerfile.streamlit     # Frontend container
├── docker-compose.yml       # Production deployment (API + Frontend + Nginx)
├── docker-compose.dev.yml   # Development deployment with hot-reload
├── nginx/                   # Nginx config & SSL certificates
├── templates/               # Jinja2 document templates (letters, certificates, etc.)
├── generated_documents/     # Output directory for generated documents
├── test_api.py              # API endpoint tests (~30 tests, JSON report)
├── test_rag.py              # RAG system tests (10 sample queries)
└── test_routing.py          # Query routing validation tests
```

---

## 🔧 How It Works

### RAG Pipeline

1. **Ingest** — `process_hr_documents.py` downloads documents from Supabase storage buckets, extracts text, splits into chunks (≈500 tokens with overlap), and generates embeddings via Gemini.
2. **Route** — `query_router.py` classifies each user query as a *data query* (analytics), *document query* (RAG), or *document generation* request using pattern matching and keyword analysis.
3. **Retrieve** — `rag_engine.py` performs vector similarity search against the knowledge base (min similarity 0.4, top-5 chunks).
4. **Generate** — Gemini 2.5 Flash synthesises a grounded answer from the retrieved context, with confidence scoring and source attribution.

### Query Types

| Type | Examples | Handler |
|---|---|---|
| **Data** | "Show headcount", "What is the attrition rate?" | `hr_analytics.py` / `performance_analytics.py` |
| **Document** | "What is the leave policy?", "Dress code rules" | `rag_engine.py` (vector search + LLM) |
| **Generation** | "Generate an offer letter for John" | `document_generator.py` |

---

## 📡 API Endpoints

~30 endpoints organised into 8 categories:

| Category | Key Endpoints |
|---|---|
| **System** | `GET /api/health`, `GET /` |
| **RAG Query** | `POST /api/query`, `POST /api/query/router-info` |
| **Leave** | `POST /api/leave/request`, `GET /api/leave/employee/{email}`, `GET /api/leave/all`, `PUT /api/leave/approve`, `GET /api/leave/statistics` |
| **Insurance** | `POST /api/employee-services/insurance/enroll`, `GET /api/employee-services/insurance/{email}` |
| **Shares** | `POST /api/employee-services/shares/allocate`, `GET /api/employee-services/shares/{email}` |
| **Compliance** | `POST /api/employee-services/compliance/record`, `GET /api/employee-services/compliance/{email}` |
| **Governance** | `POST /api/employee-services/governance/role`, `GET /api/employee-services/governance/structure` |
| **Career Dev** | `POST /api/employee-services/development/plan`, `POST /api/employee-services/development/training`, `GET /api/employee-services/development/{email}` |
| **Documents** | `POST /api/documents/generate`, `POST /api/documents/generate-termination`, `POST /api/documents/generate-certificate` |
| **Dashboard** | `GET /api/dashboard/summary`, `GET /api/dashboard/headcount`, `GET /api/dashboard/attrition`, `GET /api/dashboard/probation`, `GET /api/dashboard/appraisals`, `GET /api/dashboard/contracts`, `GET /api/dashboard/performance`, and more |

Full interactive documentation at **`/api/docs`** (Swagger UI) or **`/api/redoc`**.

---

## 📊 Usage Examples

### Search the Knowledge Base (Python)

```python
from knowledge_base import HRKnowledgeBaseClient

kb = HRKnowledgeBaseClient()
results = kb.search_similar_chunks("What is the leave policy?")

for result in results:
    print(f"Source: {result['article_title']}")
    print(f"Similarity: {result['similarity']:.2f}")
    print(f"Content: {result['content']}")
    print("---")
```

### Query via the API

```bash
curl -X POST http://localhost:8000/api/query \
  -H "Content-Type: application/json" \
  -d '{"query": "What is our company leave policy?", "user_role": "Employee"}'
```

### Generate a Document via the API

```bash
curl -X POST http://localhost:8000/api/documents/generate \
  -H "Content-Type: application/json" \
  -d '{
    "employee_name": "John Doe",
    "position_title": "Software Engineer",
    "department": "Engineering",
    "salary": 85000,
    "start_date": "2026-04-01",
    "employment_type": "Full-time"
  }'
```

---

## 🔍 Testing

Run the test suites to validate the system:

```powershell
python test_api.py       # ~30 API endpoint tests with JSON report
python test_rag.py       # RAG system tests (10 sample queries)
python test_routing.py   # Query routing classification tests
```

---

## 🗄️ Database Tables

The system uses the following Supabase tables:

| Table | Purpose |
|---|---|
| `kb_article` / `kb_chunk` | Knowledge base documents & vector embeddings |
| `people` | Employee master data |
| `org_unit` | Organisational structure |
| `employment_contract` | Contracts, probation, and employment terms |
| `leave_request` | Leave requests and approval status |
| `appraisal_cycle` / `appraisal_record` | Performance appraisal tracking |
| `employee_performance_record` | Performance scores per criteria |
| `attendance` | Check-in / check-out records |
| `performance_criteria` | Configurable scoring criteria & weights |
| `employee_insurance` | Insurance plan enrolments |
| `employee_shares` | Stock option allocations & vesting |
| `compliance_training` | Compliance training records & expiry |
| `governance_roles` / `role_assignments` | Governance structure |
| `career_development_plans` / `employee_training` | Career development & training |
| `notification` | System notifications |

---

## ⚡ Performance

- **Batch processing** for document ingestion — skips already-processed files on re-runs
- **Session-state caching** with 5-minute TTL on dashboard and performance data
- **Configurable chunking** — 500-token chunks with 150-token overlap for optimal retrieval
- **Singleton patterns** to prevent redundant service initialisation in the Streamlit app

---

## 📄 License

This project is proprietary. All rights reserved.