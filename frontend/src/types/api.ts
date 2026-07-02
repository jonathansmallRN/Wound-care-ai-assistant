// TypeScript types mirroring all backend Pydantic schemas.
// API envelope: { success: true, data: T } | { success: false, error_code: string, message: string }

export type CaseStatus = "active" | "archived";
export type ReviewStatus = "pending" | "accepted" | "overridden";
export type HealingClassification = "improving" | "stable" | "deteriorating";
export type ConfidenceTier = "high" | "medium" | "low";
export type FitzpatrickScale = "I" | "II" | "III" | "IV" | "V" | "VI";

// ── Cases ────────────────────────────────────────────────────────────────────

export interface CaseOut {
  id: string;
  case_ref: string;
  status: CaseStatus;
  created_at: string;
}

export interface CaseListItemOut {
  id: string;
  case_ref: string;
  status: CaseStatus;
  created_at: string;
  assessment_count: number;
}

export interface CaseDetailOut {
  id: string;
  case_ref: string;
  status: CaseStatus;
  assessment_count: number;
}

// ── Assessments ───────────────────────────────────────────────────────────────

export interface AssessmentCreate {
  case_id: string;
  assessment_date: string;
  length_cm: number;
  width_cm: number;
  depth_cm: number;
  tissue_type: string;
  drainage_amount: string;
  drainage_type: string;
  periwound: string;
  notes?: string;
}

export interface AssessmentCreateOut {
  assessment_id: string;
  is_baseline: boolean;
  area_cm2: number;
  volume_cm3: number;
  review_status: ReviewStatus;
}

export interface AssessmentDetailOut {
  assessment_id: string;
  case_id: string;
  assessment_date: string;
  is_baseline: boolean;
  length_cm: number;
  width_cm: number;
  depth_cm: number;
  area_cm2: number;
  volume_cm3: number;
  tissue_type: string;
  drainage_amount: string;
  drainage_type: string;
  periwound: string;
  notes: string | null;
  review_status: ReviewStatus;
  clinician_classification: HealingClassification | null;
  override_reason: string | null;
  note_draft: string | null;
  created_at: string;
}

// ── Pipeline ──────────────────────────────────────────────────────────────────

export interface VisionAnalyzeOut {
  ai_finding_id: string;
  model_version: string;
  vision_output: string | null;
  tissue_change: string | null;
  drainage_change: string | null;
  ai_available: boolean;
}

export interface LongitudinalAnalyzeOut {
  previous_assessment_id: string;
  previous_area_cm2: number;
  current_area_cm2: number;
  area_delta_pct: number;
  tissue_change: string | null;
  drainage_change: string | null;
}

export interface ClinicalAssessmentClassifyOut {
  classification: HealingClassification;
  confidence_score: number;
  confidence_tier: ConfidenceTier;
  area_signal_score: number;
  tissue_signal_score: number;
  drainage_signal_score: number;
}

export interface EvidenceItem {
  finding: string;
  score: number;
  weight: number;
  supports_classification: boolean | null;
}

export interface ExplainabilityGenerateOut {
  classification: HealingClassification;
  confidence_score: number;
  confidence_tier: ConfidenceTier;
  evidence: EvidenceItem[];
}

// ── Review ────────────────────────────────────────────────────────────────────

export interface ReviewRequest {
  assessment_id: string;
  reviewer_id?: string;
  review_status: "accepted" | "overridden";
  clinician_classification?: HealingClassification;
  override_reason?: string;
  fitzpatrick_scale?: FitzpatrickScale;
}

export interface ReviewOut {
  assessment_id: string;
  review_status: string;
  final_classification: HealingClassification | null;
  ai_classification: HealingClassification | null;
  override_reason: string | null;
  validation_record_id: string;
}

// ── Notes ─────────────────────────────────────────────────────────────────────

export interface NotesGenerateOut {
  note_id: string;
  note_draft: string;
  classification: HealingClassification | null;
  confidence_tier: ConfidenceTier | null;
}

export interface NoteUpdateOut {
  note_id: string;
  note_draft: string;
}

// ── Validation ────────────────────────────────────────────────────────────────

export interface ValidationSummaryOut {
  total_reviews: number;
  ai_available_count: number;
  accuracy_rate: number | null;
  override_rate: number | null;
  hallucination_rate: number | null;
}

export interface ValidationByReviewerOut {
  reviewer_id: string;
  reviewer_name: string;
  role: string;
  review_count: number;
  accuracy_rate: number | null;
  override_rate: number | null;
}

export interface ValidationBySkinToneOut {
  fitzpatrick_scale: FitzpatrickScale;
  review_count: number;
  accuracy_rate: number | null;
}

// ── Audit ─────────────────────────────────────────────────────────────────────

export interface AuditLogOut {
  service_name: string;
  model_version: string | null;
  latency_ms: number | null;
  success: boolean;
  created_at: string;
}
