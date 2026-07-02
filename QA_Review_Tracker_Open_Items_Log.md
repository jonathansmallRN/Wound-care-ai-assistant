# QA Review Tracker — Open Items Log

**Project:** Wound Care AI Assistant  
**Stage:** Stage 7 — Ship-blocking stabilization and governance fixes  
**Last updated:** 2026-07-02  
**Branch:** `claude/compassionate-turing-ccowgn`

---

## Priority Group A — Ship-blocking security/data integrity fixes

### Item 1 — Image upload path traversal

| Field | Value |
|---|---|
| Severity | Critical |
| File | `backend/app/services/image_service.py` |
| Status | **RESOLVED** (commit `stage-7-final`) |
| Test coverage | `tests/test_image_security.py::TestPathTraversal` (5 tests, all pass) |

**Root cause:** `filename = upload.filename` was used directly as a filesystem path, allowing `../../../etc/passwd` or `..\\..\\evil.jpg` to escape the upload directory.

**Fix:** Introduced `_storage_filename(original, mime_type)` that:
1. Generates a UUID-based storage key per upload (e.g. `a1b2c3d4-…-ef56.jpg`)
2. Derives the extension from the MIME type first, falling back to stripping path components with `Path(original.replace("\\", "/")).name` and validating with regex `^\.[a-z0-9]{1,10}$`
3. The original filename never touches the filesystem — only the UUID key is used

**Verification:** `test_unix_traversal_filename_blocked`, `test_windows_traversal_filename_blocked`, `test_absolute_path_filename_blocked`, `test_null_byte_filename_safe`, `test_storage_url_within_media_base` — all pass.

---

### Item 2 — Duplicate filename overwrite

| Field | Value |
|---|---|
| Severity | Critical |
| File | `backend/app/services/image_service.py` |
| Status | **RESOLVED** (same fix as Item 1, commit `stage-7-final`) |
| Test coverage | `tests/test_image_security.py::TestDuplicateFilename` (2 tests, all pass) |

**Root cause:** Two uploads with the same original filename (e.g., `wound.jpg`) wrote to the same disk path, silently overwriting the first file.

**Fix:** UUID-based storage key means every upload produces a unique on-disk filename regardless of the original name. Two uploads of `wound.jpg` produce `<uuid1>.jpg` and `<uuid2>.jpg`.

**Verification:** `test_same_original_name_creates_separate_files` (asserts distinct filenames and both files exist on disk), `test_sequential_images_both_retrievable` (asserts distinct `image_id` records) — both pass.

---

## Priority Group B — High severity spec-alignment fixes

### Item 3 — fitzpatrick_scale required at backend/service layer

| Field | Value |
|---|---|
| Severity | High |
| File | `backend/app/services/review_service.py` |
| Status | **RESOLVED** (commit `3bcd279`) |
| Test coverage | `tests/test_review.py::TestFitzpatrickRequired` (5 tests, all pass) |

**Root cause:** `fitzpatrick_scale: FitzpatrickScale | None = None` in `ReviewRequest` was optional end-to-end; direct API callers could omit it, leaving `validation_reviews.fitzpatrick_scale` NULL and the skin-tone bias dashboard dark.

**Fix:** Added guard in `review_service.submit_review()` before override validation:
```python
if payload.fitzpatrick_scale is None:
    raise ValidationFailedError(
        "fitzpatrick_scale is required for skin-tone bias tracking in the validation dashboard."
    )
```

**Verification:** `test_accept_without_fitzpatrick_rejected`, `test_override_without_fitzpatrick_rejected`, `test_fitzpatrick_null_explicit_rejected` return HTTP 422 / VALIDATION_ERROR. `test_accept_with_fitzpatrick_succeeds`, `test_override_with_fitzpatrick_succeeds` succeed with valid scale — all 5 pass.

---

### Item 4 — Editable progress note persistence

| Field | Value |
|---|---|
| Severity | High |
| Files | `backend/app/schemas/notes.py`, `backend/app/services/notes_service.py`, `backend/app/routers/notes.py`, `frontend/src/api/client.ts`, `frontend/src/api/pipeline.ts`, `frontend/src/types/api.ts`, `frontend/src/components/NoteEditor.tsx`, `frontend/src/pages/AssessmentWorkflowPage.tsx` |
| Status | **RESOLVED** (commit `3bcd279`) |
| Test coverage | `tests/test_notes.py::TestNoteEditable` (4 tests, all pass) |

**Root cause:** `NoteEditor.tsx` was `readOnly`; there was no `PATCH /assessments/{id}/note` endpoint. Edits were lost on page refresh.

**Fix:**
- Backend: `NoteUpdateRequest`, `NoteUpdateOut` schemas; `notes_service.update_note()`; `PATCH /api/v1/assessments/{assessment_id}/note` router
- Frontend: `patch()` helper in `api/client.ts`; `patchNote()` in `api/pipeline.ts`; `NoteUpdateOut` type; `NoteEditor.tsx` rewritten with editable textarea, Save button, saved/error state

**Verification:** `test_patch_saves_edit` (edit persists), `test_patch_idempotent_on_repeated_save` (last write wins), `test_patch_before_generation_fails` (422 if note not yet generated), `test_patch_baseline_fails` (422 for baselines) — all 4 pass.

---

### Item 5 — Audit logging for longitudinal and clinical_assessment

| Field | Value |
|---|---|
| Severity | High |
| Files | `backend/app/services/longitudinal_service.py`, `backend/app/services/clinical_assessment_service.py` |
| Status | **RESOLVED** (commit `3bcd279`) |
| Test coverage | `tests/test_audit.py::TestAuditCompleteness` (5 tests, all pass) |

**Root cause:** `longitudinal_service.py` and `clinical_assessment_service.py` had no `audit_service.log_call()` call; `GET /audit/{assessment_id}` showed only `vision`, `explainability`, and `notes`.

**Fix:** Both rule-based services now import `time` and `audit_service`, wrap the calculation in `time.monotonic()` timing, and call `log_call()` with `prompt_sent=None`, `model_version=None`, and a structured `response_received` summary string.

**Verification:** `test_all_five_services_in_audit_log` confirms `vision`, `longitudinal`, `clinical_assessment`, `explainability`, `notes` all appear in the audit log. `test_longitudinal_audit_entry_present`, `test_clinical_assessment_audit_entry_present`, `test_all_audit_entries_successful` — all 5 pass.

---

## Priority Group C — Governance and traceability polish

### Item 6 — "Skip mock mode" button gating

| Field | Value |
|---|---|
| Severity | Medium |
| Files | `frontend/src/pages/AssessmentWorkflowPage.tsx`, `docker-compose.yml`, `.env.example` |
| Status | **RESOLVED** (commit `3bcd279`) |

**Root cause:** The "Skip (mock mode)" button in `AssessmentWorkflowPage.tsx` was unconditionally rendered; no gate on `MOCK_AI_MODE`. In real AI mode, a user could bypass image upload entirely.

**Fix:**
- `docker-compose.yml` frontend service now passes `VITE_MOCK_AI_MODE: ${MOCK_AI_MODE:-true}`, mirroring the backend setting to the Vite build
- `AssessmentWorkflowPage.tsx` defines `const isMockMode = import.meta.env.VITE_MOCK_AI_MODE === "true"` and wraps the skip button in `{isMockMode && (...)}`
- `.env.example` documents `VITE_MOCK_AI_MODE=true` with explanation

**Final behavior:** Skip button visible only when `MOCK_AI_MODE=true` (default). When `MOCK_AI_MODE=false`, `VITE_MOCK_AI_MODE=false`, skip button is absent, and image upload is required before AI analysis can proceed.

---

### Item 7 — PHI / BAA warning

| Field | Value |
|---|---|
| Severity | Medium |
| Files | `README.md`, `backend/app/services/ai_client.py` |
| Status | **RESOLVED** (commit `3bcd279`) |

**Fix:**
- `README.md` "Real OpenAI calls" section opens with a blockquote BAA/HIPAA notice
- `ai_client.py:60` carries a 4-line comment at the `OpenAI(...)` init site: "PHI/BAA notice: wound images and patient measurements are transmitted to OpenAI when MOCK_AI_MODE=false. Ensure a Business Associate Agreement (BAA) with OpenAI is in place before using this with identifiable patient data."

---

### Item 8 — Confidence score transparency

| Field | Value |
|---|---|
| Severity | Medium |
| Files | `frontend/src/pages/AssessmentWorkflowPage.tsx`, `backend/app/services/clinical_assessment_service.py` |
| Status | **RESOLVED** |
| Test coverage | `tests/test_confidence.py::TestConfidenceFormula` (5 tests, all pass) |

**Existing UI display:** `AssessmentWorkflowPage.tsx` Step 3 already renders:
```
Area: {area_signal_score}×0.50 = {area_signal_score*0.5}
Tissue: {tissue_signal_score}×0.30 = {tissue_signal_score*0.3}
Drainage: {drainage_signal_score}×0.20 = {drainage_signal_score*0.2}
```

**Formula:** `confidence = area × 0.50 + tissue × 0.30 + drainage × 0.20` — enforced and tested.

**0.37 low-confidence reference case (live API + test):**
- Baseline 4×4×1 cm (16.0 cm²) → follow-up 3.8×3.8×1 cm (14.44 cm²), tissue=epithelial, drainage=minimal/serous
- `area_delta_pct = 9.8%` → STABLE → `area_signal = 1.0 − min(9.8/10.0, 1.0) = 0.02`
- `tissue_change = "improved"` → `tissue_signal = 0.8`
- `drainage_change = "stable"` → `drainage_signal = 0.6`
- `confidence = 0.02×0.50 + 0.8×0.30 + 0.6×0.20 = 0.010+0.240+0.120 = 0.37` ✓

`test_low_confidence_037_case` asserts all six fields (`classification`, `confidence_score`, `confidence_tier`, `area_signal_score`, `tissue_signal_score`, `drainage_signal_score`) — passes.

---

## Bonus fix — get_previous_assessment production bug

| Field | Value |
|---|---|
| Severity | Medium (latent production bug) |
| File | `backend/app/services/assessment_service.py` |
| Status | **RESOLVED** (commit `stage-7-final`) |

**Root cause:** `get_previous_assessment` used `Assessment.created_at < assessment.created_at` as the "earlier" predicate. Within a single PostgreSQL transaction, `now()` is evaluated once at transaction start — making both assessments created in the same transaction share the same `created_at`, so the query returns None. This manifested as 422 "No prior assessment found" in test scenarios and could also occur in production when two assessments are saved in rapid succession within the same db session context.

**Fix:** Changed primary comparator to `Assessment.assessment_date < assessment.assessment_date` (the clinician-entered date, always distinct between baseline and follow-up in practice).

---

## Summary table

| # | Item | Severity | Status | Tests |
|---|---|---|---|---|
| 1 | Path traversal in image upload | Critical | ✅ RESOLVED | 5/5 pass |
| 2 | Duplicate filename overwrite | Critical | ✅ RESOLVED | 2/2 pass |
| 3 | fitzpatrick_scale required (backend) | High | ✅ RESOLVED | 5/5 pass |
| 4 | Editable note persistence (PATCH) | High | ✅ RESOLVED | 4/4 pass |
| 5 | Audit logging — longitudinal + classify | High | ✅ RESOLVED | 5/5 pass |
| 6 | Skip mock mode gating | Medium | ✅ RESOLVED | UI-verified |
| 7 | PHI/BAA warning | Medium | ✅ RESOLVED | README + code |
| 8 | Confidence score transparency | Medium | ✅ RESOLVED | 5/5 pass |
| — | get_previous_assessment latent bug | Medium | ✅ RESOLVED | All pipeline tests |

**Total tests:** 26 passing, 0 failing  
**TypeScript:** 0 errors  
**Frontend build:** clean (218 kB)  
**Remaining open items:** None

---

## Files changed in Stage 7

| File | Change |
|---|---|
| `backend/app/services/image_service.py` | `_storage_filename()` UUID-based key; path traversal + overwrite fix |
| `backend/app/services/assessment_service.py` | `get_previous_assessment` uses `assessment_date` not `created_at` |
| `backend/app/services/review_service.py` | fitzpatrick_scale required guard |
| `backend/app/schemas/notes.py` | `NoteUpdateRequest`, `NoteUpdateOut` |
| `backend/app/services/notes_service.py` | `update_note()` |
| `backend/app/routers/notes.py` | `PATCH /assessments/{id}/note` |
| `backend/app/services/longitudinal_service.py` | audit logging |
| `backend/app/services/clinical_assessment_service.py` | audit logging |
| `backend/app/services/ai_client.py` | PHI/BAA comment |
| `backend/requirements.txt` | `pytest==8.3.5` added |
| `backend/tests/conftest.py` | Test fixtures (new) |
| `backend/tests/test_image_security.py` | 7 path traversal + overwrite tests (new) |
| `backend/tests/test_confidence.py` | 5 confidence formula tests (new) |
| `backend/tests/test_review.py` | 5 fitzpatrick enforcement tests (new) |
| `backend/tests/test_notes.py` | 4 PATCH note tests (new) |
| `backend/tests/test_audit.py` | 5 audit completeness tests (new) |
| `frontend/src/api/client.ts` | `patch()` helper |
| `frontend/src/api/pipeline.ts` | `patchNote()` |
| `frontend/src/types/api.ts` | `NoteUpdateOut` |
| `frontend/src/components/NoteEditor.tsx` | Editable + Save button |
| `frontend/src/pages/AssessmentWorkflowPage.tsx` | `isMockMode` gate; `assessmentId` prop |
| `docker-compose.yml` | `VITE_MOCK_AI_MODE` env var |
| `.env.example` | `VITE_MOCK_AI_MODE` documented |
| `README.md` | PHI/BAA notice |
| `QA_Review_Tracker_Open_Items_Log.md` | This file (new) |
