# Wound Care AI Assistant — API Contract Specification (v2.0)

> Portfolio project · Clinical AI Strategist track · June 2026
> Purpose: Define all API endpoints, request/response schemas, and error handling for MVP development.

## API standards

| Standard | Value |
|---|---|
| Base URL | `/api/v1` |
| Content type | `application/json` |
| Authentication | MVP: none required · Future: JWT |
| Success shape | `{ "success": true, "data": { } }` |
| Error shape | `{ "success": false, "error_code": "...", "message": "..." }` |

---

## Case management

### `POST /cases` — Create new wound case

| Field | Type | Required | Notes |
|---|---|---|---|
| case_ref | string | Required | Human-readable identifier — no PHI |

**Request**

```json
{ "case_ref": "CASE-001" }
```

**Response**

```json
{
  "success": true,
  "data": {
    "id": "uuid",
    "case_ref": "CASE-001",
    "status": "active",
    "created_at": "2026-06-14T10:00:00Z"
  }
}
```

### `GET /cases/{case_id}` — Retrieve case with assessment count

**Response**

```json
{
  "success": true,
  "data": {
    "id": "uuid",
    "case_ref": "CASE-001",
    "status": "active",
    "assessment_count": 3
  }
}
```

---

## Assessments

### `POST /assessments` — Create assessment (returns computed area + volume)

| Field | Type | Required | Notes |
|---|---|---|---|
| case_id | uuid | Required | References `cases.id` |
| assessment_date | date | Required | ISO 8601 date string |
| length_cm | float | Required | Wound length |
| width_cm | float | Required | Wound width |
| depth_cm | float | Required | Wound depth |
| tissue_type | string | Required | `granulation` \| `slough` \| `eschar` \| `epithelial` \| `mixed` |
| drainage_amount | string | Required | `none` \| `minimal` \| `moderate` \| `heavy` |
| drainage_type | string | Required | `serous` \| `serosanguineous` \| `sanguineous` \| `purulent` |
| periwound | string | Required | `intact` \| `macerated` \| `erythema` \| `induration` |
| notes | string | Optional | Free-text clinician notes |

**Request**

```json
{
  "case_id": "uuid",
  "assessment_date": "2026-06-14",
  "length_cm": 4.2,
  "width_cm": 2.8,
  "depth_cm": 0.3,
  "tissue_type": "granulation",
  "drainage_amount": "moderate",
  "drainage_type": "serous",
  "periwound": "intact",
  "notes": "follow-up visit"
}
```

**Response**

```json
{
  "success": true,
  "data": {
    "assessment_id": "uuid",
    "is_baseline": false,
    "area_cm2": 11.76,
    "volume_cm3": 3.53,
    "review_status": "pending"
  }
}
```

### `GET /assessments/{assessment_id}` — Retrieve full assessment record

**Response**

```json
{
  "success": true,
  "data": {
    "assessment_id": "uuid",
    "case_id": "uuid",
    "assessment_date": "2026-06-14",
    "is_baseline": false,
    "length_cm": 4.2,
    "width_cm": 2.8,
    "depth_cm": 0.3,
    "area_cm2": 11.76,
    "volume_cm3": 3.53,
    "tissue_type": "granulation",
    "drainage_amount": "moderate",
    "review_status": "pending"
  }
}
```

---

## Image management

### `POST /images` — Upload wound image (multipart)

| Field | Type | Required | Notes |
|---|---|---|---|
| assessment_id | uuid | Required | Links image to assessment |
| image_file | file | Required | JPG, PNG, or HEIC · max 20 MB |

**Response**

```json
{
  "success": true,
  "data": {
    "image_id": "uuid",
    "storage_url": "https://s3.amazonaws.com/...",
    "filename": "wound_20260614.jpg",
    "file_size_bytes": 1048576
  }
}
```

---

## Vision service

### `POST /vision/analyze` — Run GPT-4.1 image analysis

**Request**

```json
{ "assessment_id": "uuid" }
```

**Response**

```json
{
  "success": true,
  "data": {
    "ai_finding_id": "uuid",
    "model_version": "gpt-4.1",
    "vision_output": "Granulation tissue present across 70% of wound bed.",
    "tissue_change": "improved",
    "drainage_change": "stable",
    "ai_available": true
  }
}
```

---

## Longitudinal service

### `POST /longitudinal/analyze` — Compare current vs prior assessment area

**Request**

```json
{ "assessment_id": "uuid" }
```

**Response**

```json
{
  "success": true,
  "data": {
    "previous_assessment_id": "uuid",
    "previous_area_cm2": 15.0,
    "current_area_cm2": 11.76,
    "area_delta_pct": 21.6,
    "tissue_change": "improved",
    "drainage_change": "stable"
  }
}
```

---

## Clinical assessment service

### `POST /clinical-assessment/classify` — Apply classification rules + confidence score

**Request**

```json
{ "assessment_id": "uuid" }
```

**Response**

```json
{
  "success": true,
  "data": {
    "classification": "improving",
    "confidence_score": 0.86,
    "confidence_tier": "high",
    "area_signal_score": 1.0,
    "tissue_signal_score": 0.8,
    "drainage_signal_score": 0.6
  }
}
```

---

## Explainability service

### `POST /explainability/generate` — Map each finding to supporting evidence (FR-7)

> **v2 fix:** Added `score`, `weight`, and `supports_classification` per finding — required for FR-7 evidence trail UI.

**Request**

```json
{ "assessment_id": "uuid" }
```

**Response**

```json
{
  "success": true,
  "data": {
    "classification": "improving",
    "confidence_score": 0.86,
    "confidence_tier": "high",
    "evidence": [
      {
        "finding": "Area reduced 21.6%",
        "score": 1.0,
        "weight": 0.50,
        "supports_classification": true
      },
      {
        "finding": "Increased granulation tissue",
        "score": 0.8,
        "weight": 0.30,
        "supports_classification": true
      },
      {
        "finding": "Drainage unchanged",
        "score": 0.6,
        "weight": 0.20,
        "supports_classification": null
      }
    ]
  }
}
```

---

## Review workflow

### `POST /review` — Accept or override AI classification

> **v2 fix:** Response now returns final classification + review_status so frontend can update without a second fetch.

| Field | Type | Required | Notes |
|---|---|---|---|
| assessment_id | uuid | Required | Assessment being reviewed |
| reviewer_id | uuid | Optional | References `clinicians.id` — nullable in V1 |
| review_status | string | Required | `accepted` \| `overridden` |
| clinician_classification | string | Required if overridden | `improving` \| `stable` \| `deteriorating` |
| override_reason | string | Required if overridden | Free text — enforced server-side |

**Request**

```json
{
  "assessment_id": "uuid",
  "reviewer_id": "uuid",
  "review_status": "overridden",
  "clinician_classification": "stable",
  "override_reason": "Tissue appears unchanged on visual inspection"
}
```

**Response**

```json
{
  "success": true,
  "data": {
    "assessment_id": "uuid",
    "review_status": "overridden",
    "final_classification": "stable",
    "ai_classification": "improving",
    "override_reason": "Tissue appears unchanged on visual inspection",
    "validation_record_id": "uuid"
  }
}
```

---

## Progress note generation

### `POST /notes/generate` — Generate clinician-editable progress note

**Request**

```json
{ "assessment_id": "uuid" }
```

**Response**

```json
{
  "success": true,
  "data": {
    "note_id": "uuid",
    "note_draft": "Wound dimensions decreased from prior assessment...",
    "classification": "improving",
    "confidence_tier": "high"
  }
}
```

---

## Validation dashboard

### `GET /validation/summary` — Overall AI accuracy metrics

**Response**

```json
{
  "success": true,
  "data": {
    "total_reviews": 142,
    "ai_available_count": 138,
    "accuracy_rate": 0.91,
    "override_rate": 0.12,
    "hallucination_rate": 0.03
  }
}
```

### `GET /validation/by-reviewer` — Accuracy broken down by clinician

> **v2 fix:** Added `reviewer_id` to response — enables drill-down links to per-reviewer detail view.

**Response**

```json
{
  "success": true,
  "data": [
    {
      "reviewer_id": "uuid",
      "reviewer_name": "Jane Smith",
      "role": "WOCN",
      "review_count": 48,
      "accuracy_rate": 0.94,
      "override_rate": 0.08
    }
  ]
}
```

### `GET /validation/by-skin-tone` — Accuracy by Fitzpatrick skin type (bias tracking)

**Response**

```json
{
  "success": true,
  "data": [
    { "fitzpatrick_scale": "I",   "review_count": 22, "accuracy_rate": 0.95 },
    { "fitzpatrick_scale": "II",  "review_count": 31, "accuracy_rate": 0.94 },
    { "fitzpatrick_scale": "III", "review_count": 28, "accuracy_rate": 0.91 },
    { "fitzpatrick_scale": "IV",  "review_count": 19, "accuracy_rate": 0.89 },
    { "fitzpatrick_scale": "V",   "review_count": 12, "accuracy_rate": 0.83 },
    { "fitzpatrick_scale": "VI",  "review_count": 8,  "accuracy_rate": 0.81 }
  ]
}
```

---

## Audit logs

### `GET /audit/{assessment_id}` — All AI service calls for one assessment

**Response**

```json
{
  "success": true,
  "data": [
    {
      "service_name": "vision",
      "model_version": "gpt-4.1",
      "latency_ms": 1200,
      "success": true,
      "created_at": "2026-06-14T10:01:22Z"
    },
    {
      "service_name": "clinical_assessment",
      "model_version": "rule_engine_v1",
      "latency_ms": 45,
      "success": true,
      "created_at": "2026-06-14T10:01:23Z"
    }
  ]
}
```

---

## AI failure path

If any AI service call fails (timeout, API error, malformed response), the system returns a structured error and enables the manual assessment path.

```json
{
  "success": false,
  "error_code": "AI_UNAVAILABLE",
  "message": "Vision service unavailable — please complete assessment manually"
}
```

| Error code | Trigger | System behaviour |
|---|---|---|
| AI_UNAVAILABLE | Vision API timeout or error | Enable manual path · set `ai_available = false` |
| AI_LOW_CONFIDENCE | `confidence_score < 0.60` | Flag for manual review · do not auto-generate note |
| UPLOAD_FAILED | Image upload error | Prompt re-upload · do not write partial record |
| VALIDATION_ERROR | Missing required field | Return field-level error list · block submission |
| OVERRIDE_INCOMPLETE | Override with no reason | Block save · `override_reason` is required |

---

## Service → endpoint mapping

| Service | Method | Endpoint | Writes to |
|---|---|---|---|
| Vision service | POST | `/vision/analyze` | ai_findings |
| Longitudinal service | POST | `/longitudinal/analyze` | ai_findings (delta) |
| Clinical assessment svc | POST | `/clinical-assessment/classify` | ai_classifications |
| Explainability service | POST | `/explainability/generate` | ai_classifications (evidence_json) |
| Review workflow | POST | `/review` | assessments + validation_reviews |
| Note generator | POST | `/notes/generate` | assessments (note_draft) |
| Validation dashboard | GET | `/validation/*` | read-only |
| Audit log | GET | `/audit/{assessment_id}` | read-only |

> This document drives FastAPI route generation, Pydantic request/response models, and React API client functions. Claude Code can scaffold all three directly from the endpoint definitions above.
