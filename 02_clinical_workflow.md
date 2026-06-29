# Wound Care AI Assistant — Clinical Workflow (v2)

> Portfolio project · Clinical AI Strategist track · June 2026
> Updated: Confidence score formula · AI failure path · Edge cases · Prohibited outputs · Service order corrected.

## 1. New case workflow

- Create new case (Case ID + assessment date — no PHI required)
- Upload wound image (JPG, PNG, or HEIC · max 20 MB)
- Enter assessment data: Length, Width, Depth, Tissue type, Drainage amount, Drainage type, Periwound condition, Notes
- Save assessment

## 2. First assessment logic

If no prior assessment exists, store as baseline assessment. No healing classification is generated.

Generate baseline documentation and save. Baseline note is auto-saved — no clinician review step required for the first visit. Record is flagged as baseline in the database (`is_baseline = true`) and excluded from accuracy metrics.

## 3. Follow-up assessment workflow

**Corrected service order:**

1. Upload new image
2. Enter updated measurements
3. **Vision service** — GPT-4.1 image analysis → extract findings
4. **Longitudinal service** — calculate area delta and change signals
5. **Clinical assessment service** — apply rules → generate classification

> The vision service describes. The longitudinal service calculates. The clinical assessment service decides. Each stage's output is the next stage's input.

## 4. Healing classification logic

| Classification | Rule |
|---|---|
| Improving | Area reduction > 10% AND granulation same or better AND drainage stable or improved |
| Stable | Area change between -10% and +10% |
| Deteriorating | Area increase OR increased slough OR worsening drainage |

## 5. Confidence scoring formula

Confidence is a weighted sum of three signal scores. Each signal is scored 0.0–1.0 based on how strongly it supports the classification.

| Signal | Weight | Basis |
|---|---|---|
| Area change | 50% | Strongest objective indicator — derived from clinician-entered measurements |
| Tissue change | 30% | Visual assessment from GPT-4.1 image analysis |
| Drainage change | 20% | Clinical observation entered by clinician |

**Formula:**

```
confidence = (area_score × 0.50) + (tissue_score × 0.30) + (drainage_score × 0.20)
```

**Example — classification: Improving**

```
area_score     = 1.0  (area reduced 22%)
tissue_score   = 0.8  (increased granulation)
drainage_score = 0.6  (drainage unchanged — neutral signal)

confidence = (1.0 × 0.50) + (0.8 × 0.30) + (0.6 × 0.20) = 0.86 → 86%
```

| Tier | Score | UI color | Action |
|---|---|---|---|
| High | ≥ 80% | Green | Proceed to clinician review |
| Medium | 60–79% | Yellow | Proceed — clinician attention flagged |
| Low | < 60% | Red | Manual review required before note generation |

## 6. Explainability requirements (FR-7)

The explainability service maps each finding to the evidence that supports it. Both the classification and the confidence score must be traceable to source data.

**Example output:**

```
Classification: Improving
Confidence: 86% (High — green)
Evidence:
  Area reduced 22%        → supports Improving (score 1.0, weight 50%)
  Increased granulation   → supports Improving (score 0.8, weight 30%)
  Drainage unchanged      → neutral signal     (score 0.6, weight 20%)
```

## 7. AI failure path

If the AI analysis call fails (timeout, API error, or low-quality response), the system must not block the clinician.

- Display error message: "AI analysis unavailable — please complete manually"
- Clinician enters classification manually (Improving / Stable / Deteriorating)
- Clinician enters manual findings in free-text field
- Record saved with `ai_available = false`
- Confidence score field left null
- Record excluded from accuracy metrics in validation dashboard
- Audit log entry created with failure reason and timestamp

## 8. Clinician review workflow

After AI analysis completes successfully:

**Accept path:**

- Clinician reviews AI result + evidence + confidence score
- Clinician views side-by-side image comparison + AI findings
- Accept → Generate note → Clinician edits note → Save

**Override path:**

- Clinician selects correct classification (Improving / Stable / Deteriorating)
- Clinician enters override reason (free text — required field)
- Override saved alongside original AI classification
- Both classifications written to validation log

## 9. Validation workflow

Every completed assessment writes a validation record. This record is the source of truth for the validation dashboard.

| Field | Type | Notes |
|---|---|---|
| ai_classification | enum | Improving / Stable / Deteriorating / null |
| ai_confidence_score | float | 0.0–1.0 · null if AI unavailable |
| clinician_classification | enum | Final accepted or overridden value |
| match | boolean | True if AI = clinician · null if AI unavailable |
| override_reason | text | Required when clinician overrides |
| ai_available | boolean | False excludes record from accuracy metrics |
| fitzpatrick_scale | enum | I–VI · for skin tone bias tracking |

## 10. Progress note generation

- Generated after clinician accepts or overrides AI classification
- Pre-populated with: objective measurements, AI findings, healing classification, confidence tier
- Clinician can edit all fields before saving
- Saved note stored in assessments table linked to assessment ID
- Note used as input to doc generator service for V2 PDF export

## 11. Edge cases

| Scenario | System behaviour |
|---|---|
| First upload — no prior visit | Store as baseline. Skip classification. Auto-save baseline note. No review step. |
| Area = 0% change, tissue worsening | Longitudinal delta triggers Deteriorating via tissue rule, not area rule. Classification still generated. |
| Clinician closes browser mid-review | Assessment saved as `pending_review`. Clinician can resume. Note not generated until review is complete. |
| Image upload fails | Prompt re-upload. Do not proceed to AI analysis. No partial record written. |
| Measurements not entered | Block form submission. All measurement fields required before saving. |
| AI returns conflicting signals | Clinical assessment service applies rules in order: area first, then tissue, then drainage. First rule to fire wins. |

## 12. Prohibited AI outputs

The following outputs are prohibited from all AI-generated content — note drafts, findings, clinical considerations, and explainability text. **These constraints must be enforced in every Claude prompt template.**

| Prohibited output | Rule |
|---|---|
| Wound diagnosis | System may not name a wound type (e.g. Stage III pressure injury, diabetic foot ulcer). |
| Dressing recommendation | System may not suggest specific dressing products or categories. |
| Medication recommendation | System may not suggest any pharmaceutical intervention. |
| Infection determination | System may not state or imply a wound is infected. |
| Prognosis | System may not predict healing timeline or outcome. |
| Treatment plan | System may not describe a course of treatment. |
| Replacement of judgment | All output is for clinician review only. System must not frame conclusions as final. |

These constraints map directly to the PRD "Out of Scope" section and must be included verbatim in system prompt templates for both the doc generator and the explainability service.
