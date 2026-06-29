# Wound Care AI Assistant — System Architecture & Design Rationale (v2)

> Portfolio project · Clinical AI Strategist track · June 2026
> Updated: Clinical Assessment Service · Explainability Service · Validation Dashboard added.

## System Architecture

Five backend services across three layers. Original services handle image analysis, trend detection, and note generation. New services add clinical reasoning, explainability, and validation — designed before coding begins.

### Frontend layer — React + Tailwind · Vercel

| Component | Purpose |
|---|---|
| Image upload | Drag-drop, date stamp |
| Wound form | Measurements, tissue |
| Timeline view | Trend chart, images |
| Report panel | AI note, export PDF |

↓ HTTPS / multipart

### Backend + AI layer — Python + FastAPI · Render (original services)

| Component | Purpose |
|---|---|
| API gateway | FastAPI + auth |
| Vision service | GPT-4.1 image analysis |
| Longitudinal service | Trend classification |
| Doc generator | Claude progress note |

↓ data flows down through services

### New services — added before coding begins

| Component | Purpose |
|---|---|
| Clinical assessment service | Aggregate findings, apply clinical rules |
| Explainability service | Evidence trail · FR-7 |
| Validation dashboard | Case review, accuracy tracker, audit log |

↓ SQL / S3 calls

### Data layer — persistent storage

| Store | Purpose |
|---|---|
| Patient records | PostgreSQL — visits, measurements, notes |
| Image store | S3 / Cloudinary — wound photos by patient + date |
| AI audit log | Prompt + response, model version, validation records |

## New services — inputs, logic, outputs

| Service | Inputs | Core logic | Outputs |
|---|---|---|---|
| Clinical assessment service | Vision findings · Longitudinal delta · Doc draft | Apply clinical rules; combine area math with tissue assessment | Healing status · Key findings list |
| Explainability service | Assessment result · All intermediate outputs | Map each finding to supporting evidence; flag low-confidence output | Evidence list per finding · Confidence flags |
| Validation dashboard | All AI outputs · Clinician reviews | Case review panel · Accuracy tracker · Audit log viewer | Accuracy rate · Hallucination rate · Skin tone breakdown |

## Design rationale — original services

### Three distinct backend services (not one monolith)

Separating Vision, Longitudinal, and Doc Generator means each can be tested and swapped independently. When a better model is released, only that service changes.

- Enables A/B testing of AI models per service
- Reduces blast radius of failures
- Mirrors production healthcare AI system design

### Image store separate from PostgreSQL

Wound photos belong in object storage (S3/Cloudinary), not as binary blobs in a relational database. This keeps DB rows small and fast.

- Postgres blob storage degrades query performance at scale
- S3/Cloudinary provide CDN, resize-on-demand, access controls
- Architectural pattern consistent with production systems

### AI audit log as a first-class data entity

Every prompt and response is logged with model version and timestamp. Healthcare executives will always ask: "What did the AI say, and which version said it?" Without this log, that question cannot be answered.

- Enables post-hoc review if a clinician acts on AI output
- Supports model version comparison over time
- Demonstrates understanding of AI governance

### GPT-4.1 replaces GPT-4o

GPT-4o was retired from ChatGPT in February 2026. GPT-4.1 (April 2025) is the current recommended API model, with a 1M token context window and improved multimodal instruction-following.

- Use model string: `gpt-4.1`
- GPT-4.1 mini available for lower-cost tasks
- Architecture's service split makes future model changes straightforward

## Design rationale — new services

### Clinical assessment service — why separate from vision service

The vision service describes what the image looks like. The clinical assessment service decides what it means. Keeping these separate enforces a clean boundary: image observations in, clinical interpretation out. This also makes it easy to update clinical rules (e.g. PUSH Tool thresholds) without touching the AI model.

- Wound area reduction is math — compute it here, not in the AI
- Clinical rules are auditable and version-controlled independently
- Enables unit testing of classification logic without an AI call

### Explainability service — why FR-7 needs its own service

FR-7 requires the system to show *why* a conclusion was reached. Embedding this logic in other services makes it easy to skip under time pressure. A dedicated service with its own data contract enforces explainability as a first-class output, not an afterthought.

- Maps each finding to the specific evidence that supports it
- Flags low-confidence outputs for clinician attention
- Critical for responsible AI portfolio narrative

### Validation dashboard — why before coding begins

A validation dashboard designed after the app is built gets bolted on. One designed before coding becomes the source of truth for whether the AI is performing acceptably. Building it first forces the team to define "accurate enough" before a single line of application code is written.

- Case review panel: clinician marks each AI output as correct / partial / incorrect
- Accuracy tracker: classification accuracy, hallucination rate, skin tone breakdown
- Audit log viewer: prompt, response, model version, reviewer, timestamp
- Responds directly to the skin tone bias risk identified in the GPT evaluation

## MVP scope — V1 vs V2

New services are included in V1 because they define whether the AI is trustworthy — not just functional.

| Component | Service | V1 or V2 | Complexity |
|---|---|---|---|
| Image upload | Frontend | V1 | Low |
| Wound form | Frontend | V1 | Low |
| API gateway | Backend | V1 | Medium |
| Vision service | Backend | V1 | Medium |
| Longitudinal service | Backend | V1 | Medium |
| Patient records | Data | V1 | Low |
| Clinical assessment svc | Backend (new) | V1 | Medium |
| Explainability service | Backend (new) | V1 | Medium |
| Validation dashboard | Backend + Frontend (new) | V1 | Medium |
| Report panel | Frontend | V2 | Low |
| Doc generator | Backend | V2 | Medium |
| AI audit log | Data | V2 | Low |
| Timeline view | Frontend | V2 | Low |

V2 adds report panel, doc generator, full audit log, and timeline view. All are designed into the architecture from day one — V2 is an extension, not a rewrite.
