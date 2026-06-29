# Wound Care AI Assistant — Database Schema (ERD v2)

> Portfolio project · Clinical AI Strategist track · June 2026
> Updated: `area_cm2` + `volume_cm3` added to assessments · `clinicians` table added · `reviewer_id` foreign key added to validation_reviews.

**v2 changes:**

- **assessments:** `+area_cm2 (float)` · `+volume_cm3 (float)` — stored calculated fields, computed on save from `length × width` and `length × width × depth`.
- **NEW TABLE — clinicians:** reviewer identity for per-clinician accuracy analytics.
- **validation_reviews:** `+reviewer_id (uuid FK → clinicians.id)`.

## Table 1 — cases

Root entity. One case = one wound tracked over time. No PHI stored.

| Column | Type | Notes |
|---|---|---|
| id | uuid PK | Primary key |
| case_ref | varchar | Human-readable case identifier (no PHI) |
| created_at | timestamp | Case creation datetime |
| status | enum | `active` \| `archived` |

## Table 2 — assessments

Central table. `area_cm2` and `volume_cm3` stored on save — never recalculated at query time.

| Column | Type | Notes |
|---|---|---|
| id | uuid PK | Primary key |
| case_id | uuid FK | References `cases.id` |
| assessment_date | date | Date of clinical assessment |
| is_baseline | boolean | True for first assessment — no classification generated |
| length_cm | float | Wound length in centimetres |
| width_cm | float | Wound width in centimetres |
| depth_cm | float | Wound depth in centimetres |
| **area_cm2** *(NEW)* | float | Computed on save: `length_cm × width_cm` |
| **volume_cm3** *(NEW)* | float | Computed on save: `length_cm × width_cm × depth_cm` |
| tissue_type | varchar | `granulation` \| `slough` \| `eschar` \| `epithelial` \| `mixed` |
| drainage_amount | varchar | `none` \| `minimal` \| `moderate` \| `heavy` |
| drainage_type | varchar | `serous` \| `serosanguineous` \| `sanguineous` \| `purulent` |
| periwound | varchar | `intact` \| `macerated` \| `erythema` \| `induration` |
| notes | text | Free-text clinician notes |
| review_status | enum | `pending` \| `accepted` \| `overridden` |
| clinician_classification | enum | `improving` \| `stable` \| `deteriorating` \| null |
| override_reason | text | Required when `review_status = overridden` |
| note_draft | text | Clinician-edited progress note |
| created_at | timestamp | Record creation datetime |

## Table 3 — images

URL-only. Keeps Postgres rows small and fast.

| Column | Type | Notes |
|---|---|---|
| id | uuid PK | Primary key |
| assessment_id | uuid FK | References `assessments.id` |
| storage_url | varchar | S3 or Cloudinary URL — images never stored as blobs |
| filename | varchar | Original upload filename |
| mime_type | varchar | `image/jpeg` \| `image/png` \| `image/heic` |
| file_size_bytes | integer | Enforces 20 MB upload limit |
| uploaded_at | timestamp | Upload datetime |

## Table 4 — ai_findings

`area_delta_pct` now uses stored `area_cm2` values — no inline recalculation needed.

| Column | Type | Notes |
|---|---|---|
| id | uuid PK | Primary key |
| assessment_id | uuid FK | References `assessments.id` |
| model_version | varchar | e.g. `gpt-4.1` — pinned per request |
| vision_output | text | Raw GPT-4.1 image analysis response |
| area_delta_pct | float | `((prev.area_cm2 - curr.area_cm2) / prev.area_cm2) × 100` |
| tissue_change | varchar | `improved` \| `stable` \| `worsened` — from vision output |
| drainage_change | varchar | `improved` \| `stable` \| `worsened` — from clinician data |
| ai_available | boolean | False if API call failed — triggers manual path |
| failure_reason | text | Error message when `ai_available = false` |
| created_at | timestamp | Analysis datetime |

## Table 5 — ai_classifications

Stores full confidence breakdown. Each signal score is independently queryable.

| Column | Type | Notes |
|---|---|---|
| id | uuid PK | Primary key |
| ai_finding_id | uuid FK | References `ai_findings.id` |
| classification | enum | `improving` \| `stable` \| `deteriorating` |
| confidence_score | float | 0.0–1.0 weighted sum of signal scores |
| area_signal_score | float | 0.0–1.0 · weight 0.50 |
| tissue_signal_score | float | 0.0–1.0 · weight 0.30 |
| drainage_signal_score | float | 0.0–1.0 · weight 0.20 |
| evidence_json | jsonb | Structured evidence list — feeds FR-7 explainability UI |
| created_at | timestamp | Classification datetime |

## Table 6 — clinicians *(new in v2)*

Enables per-reviewer accuracy analytics: who disagrees with AI most often, by role, over time.

| Column | Type | Notes |
|---|---|---|
| id *(NEW)* | uuid PK | Primary key |
| name *(NEW)* | varchar | Clinician display name |
| role *(NEW)* | varchar | `WOCN` \| `wound_specialist` \| `home_health` \| `APP` \| `other` |
| email *(NEW)* | varchar | Used for login (no PHI — case data is de-identified) |
| created_at *(NEW)* | timestamp | Account creation datetime |

## Table 7 — validation_reviews

`reviewer_id` enables queries like: accuracy by clinician, by role, by skin tone, over time.

| Column | Type | Notes |
|---|---|---|
| id | uuid PK | Primary key |
| assessment_id | uuid FK | References `assessments.id` |
| reviewer_id *(NEW)* | uuid FK | References `clinicians.id` |
| ai_classification | enum | `improving` \| `stable` \| `deteriorating` \| null |
| ai_confidence | float | Confidence score at time of review · null if AI unavailable |
| clinician_classification | enum | Final accepted or overridden classification |
| match | boolean | True if ai = clinician · null if AI unavailable |
| ai_available | boolean | False records excluded from accuracy metrics |
| fitzpatrick_scale | enum | I–VI · nullable · for skin tone bias tracking |
| reviewer_verdict | enum | `correct` \| `partial` \| `incorrect` — entered in dashboard |
| reviewed_at | timestamp | Datetime clinician completed review |

## Table 8 — audit_logs

One row per service call. Answers: what was sent, what came back, which model, when.

| Column | Type | Notes |
|---|---|---|
| id | uuid PK | Primary key |
| assessment_id | uuid FK | References `assessments.id` |
| service_name | varchar | `vision` \| `longitudinal` \| `clinical_assessment` \| `explainability` \| `doc_generator` |
| prompt_sent | text | Full prompt text sent to AI model |
| response_received | text | Full response from AI model |
| model_version | varchar | Model string — e.g. `gpt-4.1` or `claude-sonnet-4-6` |
| latency_ms | integer | Round-trip time in milliseconds |
| success | boolean | False if call errored |
| error_message | text | Null unless `success = false` |
| created_at | timestamp | Log entry datetime |

## Table relationships

| From → To | Cardinality | Meaning |
|---|---|---|
| cases → assessments | 1 : many | One case has many assessments over time |
| assessments → images | 1 : many | Each assessment can have multiple wound photos |
| assessments → ai_findings | 1 : 0..1 | Each assessment produces at most one AI analysis |
| ai_findings → ai_classifications | 1 : 0..1 | Each AI finding produces at most one classification |
| assessments → validation_reviews | 1 : 0..1 | Each assessment gets one validation record |
| clinicians → validation_reviews | 1 : many | One clinician reviews many assessments over time |
| assessments → audit_logs | 1 : many | Multiple service calls logged per assessment |

## Design notes

- `area_cm2` and `volume_cm3` are computed once on save (`length × width` and `length × width × depth`) and stored. The longitudinal service reads `area_cm2` directly — no runtime calculation, no floating point inconsistency across queries.
- `area_delta_pct` in `ai_findings` now references stored `area_cm2` values from the current and prior assessment rows. This means the delta is always based on the same formula used everywhere else in the system.
- `clinicians` is a lookup table, not an auth table. V1 uses it for reviewer identity. V2 can add login fields (`hashed_password`, `last_login`) without schema migration.
- `reviewer_id` on `validation_reviews` enables queries that v1 could never answer: which clinician overrides AI most often, does override rate vary by role (WOCN vs. APP), does a specific reviewer show different patterns on darker skin tones.
- `reviewer_id` is nullable in V1 — if the validation dashboard is used without clinician login, records still write. The field populates as login is added.
- Images stored as URLs only. Postgres never holds binary image data — rows stay fast and the image store (S3/Cloudinary) handles CDN, access control, and resize-on-demand independently.
- `audit_logs` records every AI service call. When a healthcare executive asks "what prompt did you send to the model?", this table has the exact text, model version, and timestamp.

> This schema is ready for Claude Code. It can generate SQL migration files, FastAPI Pydantic models, API request/response shapes, and React form field definitions directly from these eight tables.
