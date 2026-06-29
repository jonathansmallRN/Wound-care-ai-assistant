# Wound Care AI Assistant — Build Specification (v1.0)

> Portfolio project · Clinical AI Strategist track · June 2026

Using this Build Specification v1.0, generate the complete Wound Care AI Assistant project.

## Requirements

- React + TypeScript + Tailwind frontend
- FastAPI backend
- PostgreSQL database
- Docker Compose local environment
- OpenAI GPT-4.1 Vision integration
- Clinical Assessment Service
- Longitudinal Service
- Explainability Service
- Validation Dashboard
- Audit Logging

## Generate

1. Project folder structure
2. Database migrations
3. FastAPI routes
4. Pydantic models
5. SQLAlchemy models
6. React pages and components
7. API client layer
8. Docker configuration
9. Environment variable configuration
10. Mock seed data

The implementation must follow the architecture, workflow, ERD, and API contract defined in this specification.

## Scope guardrails

This application is a **clinical decision support and documentation tool only**.

**Do not implement** diagnosis, treatment recommendations, infection determination, or autonomous clinical decision-making.

> See `02_clinical_workflow.md` §12 (Prohibited AI outputs) for the full list of constraints that must be enforced in every AI prompt template.
