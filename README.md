# Wound Care AI Assistant

Clinical decision support and documentation tool — AI-assisted wound healing classification, explainability, and progress note generation. **Decision support only** — the system never diagnoses, recommends treatment, determines infection, or makes autonomous clinical decisions.

---

## Quick start (Docker Compose)

### Prerequisites

- Docker Desktop (or Docker Engine + Compose v2)
- Git

### 1 — Clone and configure

```bash
git clone https://github.com/jonathansmallrn/wound-care-ai-assistant.git
cd wound-care-ai-assistant
cp .env.example .env
```

No further configuration is needed for local demo — `MOCK_AI_MODE=true` is the default (no OpenAI key required).

### 2 — Start the stack

```bash
docker compose up --build
```

On first run this builds both service images, runs Alembic migrations, and seeds demo data. Wait for:

```
INFO:     Application startup complete.
```

### 3 — Open the app

| Service | URL |
|---|---|
| Frontend | http://localhost:5173 |
| Backend API | http://localhost:8000 |
| API docs (Swagger) | http://localhost:8000/docs |
| Health check | http://localhost:8000/health |

### 4 — Stop

```bash
docker compose down          # stop containers, keep DB volume
docker compose down -v       # stop and delete all data (clean slate)
```

---

## Using the app

### Demo data

Five cases are seeded automatically on first start:

| Case | Scenario | Fitzpatrick |
|---|---|---|
| SEED-CASE-001 | Improving trajectory (3 assessments) | III |
| SEED-CASE-002 | Stable trajectory (3 assessments) | II |
| SEED-CASE-003 | Deteriorating wound (2 assessments) | VI |
| SEED-CASE-004 | Low-confidence → forced clinician override | I |
| SEED-CASE-005 | Stable, no change | IV |

### Full workflow

1. **Cases list** (`/`) — create a new case or open a seeded one
2. **Case detail** — view assessment timeline, add a follow-up assessment
3. **New assessment** — enter measurements (L × W × D, tissue, drainage, periwound); baseline auto-saves with no AI step
4. **Assessment workflow** (`/assessments/:id`) — run the pipeline sequentially:
   - Image upload (optional in mock mode — click "Skip")
   - Vision analysis → Longitudinal analysis → Clinical assessment (confidence score) → Explainability (FR-7 evidence trail)
   - Clinician review: Accept or Override (override requires documented reason + Fitzpatrick scale)
   - Progress note generation → copy to EHR
5. **Validation dashboard** (`/validation`) — AI accuracy, override rates, Fitzpatrick I–VI skin-tone bias table

---

## Real OpenAI calls (optional)

> **PHI/BAA notice:** When `MOCK_AI_MODE=false`, wound images and patient measurements are transmitted to OpenAI. Before enabling real AI calls in any environment that handles identifiable patient data, confirm that your OpenAI subscription includes a signed Business Associate Agreement (BAA) covering PHI under HIPAA. Do not transmit identifiable patient data without a signed BAA in place.

Edit `.env`:

```dotenv
MOCK_AI_MODE=false
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4.1
```

Then restart: `docker compose up --build`.

---

## Running without Docker

### Backend

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# Start Postgres separately (or use Docker for just the DB)
docker compose up db -d

cp ../.env.example ../.env    # edit DATABASE_URL if needed
alembic upgrade head
python -m app.seed.seed_data  # seed demo data
uvicorn app.main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

The Vite dev server proxies `/api/*` → `http://localhost:8000` automatically.

---

## Project structure

```
.
├── backend/
│   ├── app/
│   │   ├── common/         # errors.py, prompts.py (prohibited-output clause)
│   │   ├── models/         # SQLAlchemy ORM models + enums
│   │   ├── routers/        # FastAPI route handlers (one file per domain)
│   │   ├── schemas/        # Pydantic v2 request/response models
│   │   ├── seed/           # Idempotent demo data (seed_data.py)
│   │   └── services/       # Business logic
│   │       ├── vision_service.py
│   │       ├── longitudinal_service.py
│   │       ├── clinical_assessment_service.py
│   │       ├── explainability_service.py
│   │       ├── review_service.py
│   │       └── notes_service.py
│   ├── alembic/            # DB migration scripts
│   └── entrypoint.sh       # wait → migrate → seed → uvicorn
├── frontend/
│   └── src/
│       ├── api/            # Typed fetch modules per domain
│       ├── components/     # Layout, ConfidenceBadge, EvidenceTable, ReviewPanel, NoteEditor
│       ├── pages/          # CasesPage, CaseDetailPage, AssessmentWorkflowPage, ValidationDashboardPage
│       └── types/api.ts    # TypeScript interfaces mirroring all backend schemas
├── docker-compose.yml
├── .env.example
└── 01_architecture.md … 05_api_contract.md   ← spec documents
```

---

## Spec documents

## Read these in order

| File | What it defines |
|---|---|
| `01_architecture.md` | Service topology, design rationale, V1 vs V2 scope |
| `02_clinical_workflow.md` | Workflows, classification rules, confidence formula, **prohibited AI outputs** |
| `03_database_erd.md` | Eight-table schema with types and relationships |
| `04_build_specification.md` | What to generate and the build scope guardrails |
| `05_api_contract.md` | All endpoints, request/response schemas, error envelopes |

## Non-negotiable build rules

- **Preserve service boundaries.** Vision (describes) → Longitudinal (calculates) → Clinical Assessment (decides) → Explainability (justifies) are separate services, not one endpoint. Do not collapse them.
- **Prohibited AI outputs** (`02_clinical_workflow.md` §12) must be enforced verbatim in every AI prompt template: no diagnosis, dressing, medication, infection determination, prognosis, or treatment plan.
- **Calculated fields** (`area_cm2`, `volume_cm3`) are computed once on save and stored — never recalculated at query time.
- **Confidence formula:** `(area × 0.50) + (tissue × 0.30) + (drainage × 0.20)`.
- **Validation dashboard is V1**, including Fitzpatrick skin-tone bias tracking — it establishes trustworthiness before deployment.
- **Mandatory clinician review gate** before note generation (except the auto-saved baseline).

## Stack

React + TypeScript + Tailwind (Vite) · FastAPI + SQLAlchemy + Alembic + Pydantic · PostgreSQL · Docker Compose (single-command startup) · OpenAI GPT-4.1 (vision) with a deterministic MOCK_AI_MODE fallback when no API key is present.
