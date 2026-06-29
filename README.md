# Wound Care AI Assistant — Specifications

Source-of-truth design documents for the Wound Care AI Assistant, a clinical decision support and documentation tool. **Decision support only** — the system never diagnoses, recommends treatment, determines infection, or makes autonomous clinical decisions.

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
