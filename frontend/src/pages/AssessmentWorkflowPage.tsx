import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { getAssessment } from "../api/assessments";
import { getAuditLog } from "../api/audit";
import {
  runClassify,
  runExplainability,
  runLongitudinal,
  runVision,
  generateNote,
} from "../api/pipeline";
import { uploadImage } from "../api/images";
import { ApiError } from "../api/client";
import type {
  AssessmentDetailOut,
  AuditLogOut,
  ClinicalAssessmentClassifyOut,
  ExplainabilityGenerateOut,
  LongitudinalAnalyzeOut,
  NotesGenerateOut,
  ReviewOut,
  VisionAnalyzeOut,
} from "../types/api";
import ConfidenceBadge from "../components/ConfidenceBadge";
import ClassificationBadge from "../components/ClassificationBadge";
import EvidenceTable from "../components/EvidenceTable";
import ReviewPanel from "../components/ReviewPanel";
import NoteEditor from "../components/NoteEditor";

// ── Step card wrapper ─────────────────────────────────────────────────────────

function StepCard({
  step,
  title,
  subtitle,
  done,
  active,
  children,
}: {
  step: number;
  title: string;
  subtitle?: string;
  done: boolean;
  active: boolean;
  children: React.ReactNode;
}) {
  return (
    <div
      className={`rounded-xl border p-5 transition-colors ${
        done
          ? "border-green-200 bg-green-50/40"
          : active
            ? "border-blue-200 bg-white"
            : "border-slate-200 bg-slate-50/50 opacity-50 pointer-events-none"
      }`}
    >
      <div className="flex items-center gap-3 mb-3">
        <div
          className={`w-7 h-7 rounded-full flex items-center justify-center text-xs font-bold shrink-0 ${
            done
              ? "bg-green-500 text-white"
              : active
                ? "bg-blue-600 text-white"
                : "bg-slate-200 text-slate-500"
          }`}
        >
          {done ? "✓" : step}
        </div>
        <div>
          <div className="text-sm font-semibold text-slate-800">{title}</div>
          {subtitle && (
            <div className="text-xs text-slate-500">{subtitle}</div>
          )}
        </div>
      </div>
      <div className="ml-10">{children}</div>
    </div>
  );
}

// ── Run button ────────────────────────────────────────────────────────────────

function RunButton({
  label,
  loading,
  error,
  onClick,
}: {
  label: string;
  loading: boolean;
  error: string | null;
  onClick: () => void;
}) {
  return (
    <div className="space-y-2">
      <button
        type="button"
        onClick={onClick}
        disabled={loading}
        className="px-4 py-2 rounded-lg bg-blue-600 text-white text-sm font-semibold hover:bg-blue-700 disabled:opacity-50 transition-colors"
      >
        {loading ? "Running…" : label}
      </button>
      {error && <p className="text-sm text-red-600">{error}</p>}
    </div>
  );
}

// ── Main page ─────────────────────────────────────────────────────────────────

export default function AssessmentWorkflowPage() {
  const { assessmentId } = useParams<{ assessmentId: string }>();

  const [assessment, setAssessment] = useState<AssessmentDetailOut | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Pipeline results (local state for current session)
  const [visionResult, setVisionResult] = useState<VisionAnalyzeOut | null>(null);
  const [longitudinalResult, setLongitudinalResult] =
    useState<LongitudinalAnalyzeOut | null>(null);
  const [classifyResult, setClassifyResult] =
    useState<ClinicalAssessmentClassifyOut | null>(null);
  const [explainResult, setExplainResult] =
    useState<ExplainabilityGenerateOut | null>(null);
  const [reviewResult, setReviewResult] = useState<ReviewOut | null>(null);
  const [noteResult, setNoteResult] = useState<NotesGenerateOut | null>(null);

  // Per-step loading / error
  const [runningStep, setRunningStep] = useState<string | null>(null);
  const [stepError, setStepError] = useState<string | null>(null);

  // Image upload
  const [imageFile, setImageFile] = useState<File | null>(null);
  const [imageUploaded, setImageUploaded] = useState(false);
  const [uploadingImage, setUploadingImage] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);

  // Audit log
  const [auditLog, setAuditLog] = useState<AuditLogOut[]>([]);
  const [showAudit, setShowAudit] = useState(false);

  useEffect(() => {
    if (!assessmentId) return;
    getAssessment(assessmentId)
      .then(setAssessment)
      .catch((e) => setError(e.message ?? "Failed to load assessment."))
      .finally(() => setLoading(false));
  }, [assessmentId]);

  async function runStep<T>(
    key: string,
    fn: () => Promise<T>,
    onSuccess: (r: T) => void,
  ) {
    setRunningStep(key);
    setStepError(null);
    try {
      const result = await fn();
      onSuccess(result);
    } catch (e) {
      setStepError(
        e instanceof ApiError ? e.message : "Step failed. Try again.",
      );
    } finally {
      setRunningStep(null);
    }
  }

  async function handleUploadImage() {
    if (!imageFile || !assessmentId) return;
    setUploadingImage(true);
    setUploadError(null);
    try {
      await uploadImage(assessmentId, imageFile);
      setImageUploaded(true);
    } catch (e) {
      setUploadError(
        e instanceof ApiError ? e.message : "Image upload failed.",
      );
    } finally {
      setUploadingImage(false);
    }
  }

  async function loadAuditLog() {
    if (!assessmentId) return;
    try {
      const logs = await getAuditLog(assessmentId);
      setAuditLog(logs);
      setShowAudit(true);
    } catch {
      // non-critical — swallow
    }
  }

  // ── Completed assessment view ───────────────────────────────────────────────

  if (!loading && assessment && assessment.review_status !== "pending") {
    return (
      <div className="max-w-2xl mx-auto px-6 py-8 space-y-6">
        <Link
          to={`/cases/${assessment.case_id}`}
          className="text-sm text-slate-400 hover:text-slate-600 transition-colors"
        >
          ← Case
        </Link>

        <div className="flex items-center gap-3 flex-wrap">
          <h1 className="text-xl font-bold text-slate-900">
            Follow-up Assessment
          </h1>
          <span
            className={`inline-block px-2.5 py-1 rounded-full text-xs font-semibold border ${
              assessment.review_status === "accepted"
                ? "bg-green-100 text-green-700 border-green-200"
                : "bg-amber-100 text-amber-700 border-amber-200"
            }`}
          >
            {assessment.review_status}
          </span>
          {assessment.clinician_classification && (
            <ClassificationBadge
              classification={assessment.clinician_classification}
            />
          )}
        </div>

        {/* Measurements */}
        <div className="bg-white rounded-xl border border-slate-200 p-5">
          <h2 className="text-sm font-semibold text-slate-700 mb-3">
            Measurements —{" "}
            {new Date(assessment.assessment_date).toLocaleDateString("en-US", {
              year: "numeric",
              month: "long",
              day: "numeric",
            })}
          </h2>
          <dl className="grid grid-cols-3 gap-4 text-sm">
            {[
              ["Length", `${assessment.length_cm} cm`],
              ["Width", `${assessment.width_cm} cm`],
              ["Depth", `${assessment.depth_cm} cm`],
              ["Area", `${assessment.area_cm2.toFixed(2)} cm²`],
              ["Volume", `${assessment.volume_cm3.toFixed(2)} cm³`],
              ["Tissue", assessment.tissue_type],
              ["Drainage amount", assessment.drainage_amount],
              ["Drainage type", assessment.drainage_type],
              ["Periwound", assessment.periwound],
            ].map(([label, val]) => (
              <div key={label}>
                <dt className="text-xs text-slate-500">{label}</dt>
                <dd className="font-medium text-slate-800 capitalize">{val}</dd>
              </div>
            ))}
          </dl>
          {assessment.notes && (
            <p className="mt-3 text-sm text-slate-600 border-t border-slate-100 pt-3">
              {assessment.notes}
            </p>
          )}
        </div>

        {/* Override reason */}
        {assessment.override_reason && (
          <div className="bg-amber-50 border border-amber-200 rounded-xl p-4">
            <p className="text-xs font-semibold text-amber-700 mb-1">
              Override reason
            </p>
            <p className="text-sm text-amber-800">{assessment.override_reason}</p>
          </div>
        )}

        {/* Note */}
        {assessment.note_draft && (
          <div className="bg-white rounded-xl border border-slate-200 p-5">
            <h2 className="text-sm font-semibold text-slate-700 mb-3">
              Progress Note
            </h2>
            <NoteEditor
              noteDraft={assessment.note_draft}
              classification={assessment.clinician_classification}
              confidenceTier={null}
            />
          </div>
        )}

        {/* Audit log toggle */}
        <div>
          <button
            type="button"
            onClick={showAudit ? () => setShowAudit(false) : loadAuditLog}
            className="text-sm text-slate-400 hover:text-slate-600 underline"
          >
            {showAudit ? "Hide" : "Show"} audit log
          </button>
          {showAudit && auditLog.length > 0 && (
            <div className="mt-3 bg-white rounded-xl border border-slate-200 overflow-hidden">
              <table className="w-full text-xs">
                <thead className="bg-slate-50 border-b border-slate-200">
                  <tr>
                    <th className="text-left px-3 py-2 text-slate-500 font-medium">Service</th>
                    <th className="text-left px-3 py-2 text-slate-500 font-medium">Model</th>
                    <th className="text-right px-3 py-2 text-slate-500 font-medium">Latency</th>
                    <th className="text-center px-3 py-2 text-slate-500 font-medium">Success</th>
                    <th className="text-right px-3 py-2 text-slate-500 font-medium">Time</th>
                  </tr>
                </thead>
                <tbody>
                  {auditLog.map((log, i) => (
                    <tr key={i} className="border-b border-slate-100 last:border-0">
                      <td className="px-3 py-2 font-mono text-slate-700">{log.service_name}</td>
                      <td className="px-3 py-2 text-slate-500">{log.model_version ?? "—"}</td>
                      <td className="px-3 py-2 text-right text-slate-500">
                        {log.latency_ms != null ? `${log.latency_ms}ms` : "—"}
                      </td>
                      <td className="px-3 py-2 text-center">
                        {log.success ? (
                          <span className="text-green-600">✓</span>
                        ) : (
                          <span className="text-red-600">✗</span>
                        )}
                      </td>
                      <td className="px-3 py-2 text-right text-slate-400">
                        {new Date(log.created_at).toLocaleTimeString()}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>
    );
  }

  // ── Baseline view ───────────────────────────────────────────────────────────

  if (!loading && assessment?.is_baseline) {
    return (
      <div className="max-w-2xl mx-auto px-6 py-8 space-y-6">
        <Link
          to={`/cases/${assessment.case_id}`}
          className="text-sm text-slate-400 hover:text-slate-600 transition-colors"
        >
          ← Case
        </Link>

        <div className="flex items-center gap-3">
          <h1 className="text-xl font-bold text-slate-900">
            Baseline Assessment
          </h1>
          <span className="inline-block px-2.5 py-1 rounded-full text-xs font-semibold border bg-slate-100 text-slate-600 border-slate-200">
            Baseline
          </span>
        </div>

        <div className="bg-white rounded-xl border border-slate-200 p-5">
          <h2 className="text-sm font-semibold text-slate-700 mb-3">
            Measurements —{" "}
            {new Date(assessment.assessment_date).toLocaleDateString("en-US", {
              year: "numeric",
              month: "long",
              day: "numeric",
            })}
          </h2>
          <dl className="grid grid-cols-3 gap-4 text-sm">
            {[
              ["Length", `${assessment.length_cm} cm`],
              ["Width", `${assessment.width_cm} cm`],
              ["Depth", `${assessment.depth_cm} cm`],
              ["Area", `${assessment.area_cm2.toFixed(2)} cm²`],
              ["Volume", `${assessment.volume_cm3.toFixed(2)} cm³`],
              ["Tissue", assessment.tissue_type],
              ["Drainage amount", assessment.drainage_amount],
              ["Drainage type", assessment.drainage_type],
              ["Periwound", assessment.periwound],
            ].map(([label, val]) => (
              <div key={label}>
                <dt className="text-xs text-slate-500">{label}</dt>
                <dd className="font-medium text-slate-800 capitalize">{val}</dd>
              </div>
            ))}
          </dl>
          {assessment.notes && (
            <p className="mt-3 text-sm text-slate-600 border-t border-slate-100 pt-3">
              {assessment.notes}
            </p>
          )}
        </div>

        <div className="rounded-lg bg-blue-50 border border-blue-200 px-4 py-3 text-sm text-blue-700">
          Baseline assessment saved. No AI classification is generated for the
          first visit — it establishes the reference measurements for future
          comparisons.
        </div>
      </div>
    );
  }

  // ── Loading / error ─────────────────────────────────────────────────────────

  if (loading) {
    return (
      <div className="flex items-center justify-center py-24">
        <span className="text-sm text-slate-400">Loading…</span>
      </div>
    );
  }

  if (error || !assessment) {
    return (
      <div className="max-w-2xl mx-auto px-6 py-8">
        <div className="rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
          {error ?? "Assessment not found."}
        </div>
      </div>
    );
  }

  // ── Pipeline workflow (follow-up, pending) ──────────────────────────────────

  const pipelineDone = reviewResult !== null;
  const noteGenerated = noteResult !== null;

  return (
    <div className="max-w-2xl mx-auto px-6 py-8 space-y-4">
      {/* Header */}
      <Link
        to={`/cases/${assessment.case_id}`}
        className="text-sm text-slate-400 hover:text-slate-600 transition-colors"
      >
        ← Case
      </Link>

      <div>
        <h1 className="text-xl font-bold text-slate-900">
          Follow-up Assessment
        </h1>
        <p className="text-sm text-slate-500 mt-0.5">
          {new Date(assessment.assessment_date).toLocaleDateString("en-US", {
            year: "numeric",
            month: "long",
            day: "numeric",
          })}{" "}
          · Area: {assessment.area_cm2.toFixed(2)} cm²
        </p>
      </div>

      {/* Assessment summary */}
      <div className="bg-white rounded-xl border border-slate-200 p-4">
        <dl className="grid grid-cols-3 gap-3 text-xs">
          {[
            ["L × W × D", `${assessment.length_cm} × ${assessment.width_cm} × ${assessment.depth_cm} cm`],
            ["Area / Volume", `${assessment.area_cm2.toFixed(2)} cm² · ${assessment.volume_cm3.toFixed(2)} cm³`],
            ["Tissue", assessment.tissue_type],
            ["Drainage", `${assessment.drainage_amount} · ${assessment.drainage_type}`],
            ["Periwound", assessment.periwound],
          ].map(([label, val]) => (
            <div key={label}>
              <dt className="text-slate-400">{label}</dt>
              <dd className="font-medium text-slate-700 capitalize">{val}</dd>
            </div>
          ))}
        </dl>
        {assessment.notes && (
          <p className="mt-2 text-xs text-slate-500 border-t border-slate-100 pt-2">
            {assessment.notes}
          </p>
        )}
      </div>

      {/* Step 0 — Image upload (optional) */}
      <StepCard
        step={0}
        title="Upload Wound Image"
        subtitle="Optional — mock mode uses placeholder image"
        done={imageUploaded}
        active={!imageUploaded}
      >
        {!imageUploaded ? (
          <div className="space-y-2">
            <input
              type="file"
              accept="image/jpeg,image/png,image/heic"
              onChange={(e) => setImageFile(e.target.files?.[0] ?? null)}
              className="block text-sm text-slate-600 file:mr-3 file:py-1.5 file:px-3 file:rounded-lg file:border file:border-slate-200 file:text-sm file:font-medium file:bg-white file:text-slate-700 hover:file:bg-slate-50"
            />
            <div className="flex gap-2 items-center">
              <button
                type="button"
                onClick={handleUploadImage}
                disabled={!imageFile || uploadingImage}
                className="px-3 py-1.5 rounded-lg bg-blue-600 text-white text-xs font-semibold hover:bg-blue-700 disabled:opacity-50 transition-colors"
              >
                {uploadingImage ? "Uploading…" : "Upload"}
              </button>
              <button
                type="button"
                onClick={() => setImageUploaded(true)}
                className="text-xs text-slate-400 hover:text-slate-600 underline"
              >
                Skip (mock mode)
              </button>
            </div>
            {uploadError && (
              <p className="text-xs text-red-600">{uploadError}</p>
            )}
          </div>
        ) : (
          <p className="text-sm text-green-700">Image ready.</p>
        )}
      </StepCard>

      {/* Step 1 — Vision */}
      <StepCard
        step={1}
        title="Vision Analysis"
        subtitle="GPT-4.1 image analysis · extracts tissue and drainage findings"
        done={visionResult !== null}
        active={imageUploaded && visionResult === null}
      >
        {!visionResult ? (
          <RunButton
            label="Run Vision Analysis"
            loading={runningStep === "vision"}
            error={runningStep === null ? stepError : null}
            onClick={() =>
              runStep("vision", () => runVision(assessment.assessment_id), setVisionResult)
            }
          />
        ) : (
          <div className="space-y-2 text-sm">
            <div className="flex gap-4 text-xs">
              <span>
                Model:{" "}
                <strong className="text-slate-700">{visionResult.model_version}</strong>
              </span>
              <span>
                AI available:{" "}
                <strong className={visionResult.ai_available ? "text-green-700" : "text-red-700"}>
                  {visionResult.ai_available ? "Yes" : "No"}
                </strong>
              </span>
            </div>
            {visionResult.tissue_change && (
              <p className="text-slate-600">
                Tissue: <strong className="capitalize">{visionResult.tissue_change}</strong>
              </p>
            )}
            {visionResult.drainage_change && (
              <p className="text-slate-600">
                Drainage: <strong className="capitalize">{visionResult.drainage_change}</strong>
              </p>
            )}
            {visionResult.vision_output && (
              <details className="text-xs">
                <summary className="cursor-pointer text-slate-400 hover:text-slate-600">
                  Raw vision output
                </summary>
                <pre className="mt-2 whitespace-pre-wrap text-slate-600 bg-slate-50 p-2 rounded-lg">
                  {visionResult.vision_output}
                </pre>
              </details>
            )}
          </div>
        )}
      </StepCard>

      {/* Step 2 — Longitudinal */}
      <StepCard
        step={2}
        title="Longitudinal Analysis"
        subtitle="Calculates area delta % from prior visit using stored area_cm2"
        done={longitudinalResult !== null}
        active={visionResult !== null && longitudinalResult === null}
      >
        {!longitudinalResult ? (
          <RunButton
            label="Run Longitudinal Analysis"
            loading={runningStep === "longitudinal"}
            error={runningStep === null ? stepError : null}
            onClick={() =>
              runStep(
                "longitudinal",
                () => runLongitudinal(assessment.assessment_id),
                setLongitudinalResult,
              )
            }
          />
        ) : (
          <div className="text-sm space-y-1">
            <div className="flex gap-6 text-xs">
              <span>
                Previous: <strong>{longitudinalResult.previous_area_cm2.toFixed(2)} cm²</strong>
              </span>
              <span>
                Current: <strong>{assessment.area_cm2.toFixed(2)} cm²</strong>
              </span>
            </div>
            <p className="font-semibold text-slate-800">
              Area delta: {longitudinalResult.area_delta_pct >= 0 ? "+" : ""}
              {longitudinalResult.area_delta_pct.toFixed(1)}%
              <span className="ml-2 text-xs font-normal text-slate-500">
                {longitudinalResult.area_delta_pct > 10
                  ? "(improving — area reduced)"
                  : longitudinalResult.area_delta_pct < -10
                    ? "(deteriorating — area increased)"
                    : "(stable — within ±10%)"}
              </span>
            </p>
          </div>
        )}
      </StepCard>

      {/* Step 3 — Clinical Assessment */}
      <StepCard
        step={3}
        title="Clinical Assessment"
        subtitle="Applies classification rules · generates confidence score"
        done={classifyResult !== null}
        active={longitudinalResult !== null && classifyResult === null}
      >
        {!classifyResult ? (
          <RunButton
            label="Run Clinical Assessment"
            loading={runningStep === "classify"}
            error={runningStep === null ? stepError : null}
            onClick={() =>
              runStep("classify", () => runClassify(assessment.assessment_id), setClassifyResult)
            }
          />
        ) : (
          <div className="space-y-2">
            <div className="flex items-center gap-3 flex-wrap">
              <ClassificationBadge classification={classifyResult.classification} />
              <ConfidenceBadge
                tier={classifyResult.confidence_tier}
                score={classifyResult.confidence_score}
              />
            </div>
            <div className="text-xs text-slate-500 grid grid-cols-3 gap-2">
              <span>
                Area: {classifyResult.area_signal_score.toFixed(2)} ×0.50 ={" "}
                {(classifyResult.area_signal_score * 0.5).toFixed(3)}
              </span>
              <span>
                Tissue: {classifyResult.tissue_signal_score.toFixed(2)} ×0.30 ={" "}
                {(classifyResult.tissue_signal_score * 0.3).toFixed(3)}
              </span>
              <span>
                Drainage: {classifyResult.drainage_signal_score.toFixed(2)} ×0.20 ={" "}
                {(classifyResult.drainage_signal_score * 0.2).toFixed(3)}
              </span>
            </div>
          </div>
        )}
      </StepCard>

      {/* Step 4 — Explainability */}
      <StepCard
        step={4}
        title="Explainability"
        subtitle="Maps each signal to source evidence (FR-7)"
        done={explainResult !== null}
        active={classifyResult !== null && explainResult === null}
      >
        {!explainResult ? (
          <RunButton
            label="Generate Explainability"
            loading={runningStep === "explain"}
            error={runningStep === null ? stepError : null}
            onClick={() =>
              runStep(
                "explain",
                () => runExplainability(assessment.assessment_id),
                setExplainResult,
              )
            }
          />
        ) : (
          <EvidenceTable
            evidence={explainResult.evidence}
            classification={explainResult.classification}
            confidenceScore={explainResult.confidence_score}
          />
        )}
      </StepCard>

      {/* Step 5 — Clinician Review */}
      <StepCard
        step={5}
        title="Clinician Review"
        subtitle="Accept AI classification or override with documented reason"
        done={reviewResult !== null}
        active={explainResult !== null && reviewResult === null}
      >
        {!reviewResult && classifyResult ? (
          <ReviewPanel
            assessmentId={assessment.assessment_id}
            classifyResult={classifyResult}
            onComplete={(r) => {
              setReviewResult(r);
            }}
          />
        ) : reviewResult ? (
          <div className="space-y-2">
            <div className="flex items-center gap-3 flex-wrap">
              <span
                className={`inline-block px-2.5 py-1 rounded-full text-xs font-semibold border ${
                  reviewResult.review_status === "accepted"
                    ? "bg-green-100 text-green-700 border-green-200"
                    : "bg-amber-100 text-amber-700 border-amber-200"
                }`}
              >
                {reviewResult.review_status}
              </span>
              {reviewResult.final_classification && (
                <ClassificationBadge
                  classification={reviewResult.final_classification}
                />
              )}
            </div>
            {reviewResult.override_reason && (
              <p className="text-xs text-slate-600 bg-amber-50 border border-amber-100 rounded p-2">
                {reviewResult.override_reason}
              </p>
            )}
          </div>
        ) : null}
      </StepCard>

      {/* Step 6 — Progress Note */}
      <StepCard
        step={6}
        title="Progress Note"
        subtitle="Auto-generated from AI findings · editable before filing"
        done={noteGenerated}
        active={reviewResult !== null && !noteGenerated}
      >
        {!noteResult && reviewResult ? (
          <RunButton
            label="Generate Progress Note"
            loading={runningStep === "note"}
            error={runningStep === null ? stepError : null}
            onClick={() =>
              runStep(
                "note",
                () => generateNote(assessment.assessment_id),
                setNoteResult,
              )
            }
          />
        ) : noteResult ? (
          <NoteEditor
            noteDraft={noteResult.note_draft}
            classification={noteResult.classification}
            confidenceTier={noteResult.confidence_tier}
          />
        ) : null}
      </StepCard>

      {/* Workflow complete banner */}
      {noteGenerated && (
        <div className="rounded-xl border border-green-200 bg-green-50 px-5 py-4 text-center">
          <p className="text-sm font-semibold text-green-800">
            Assessment workflow complete.
          </p>
          <p className="text-xs text-green-700 mt-0.5">
            Progress note saved. Copy to your EHR system.
          </p>
          <Link
            to={`/cases/${assessment.case_id}`}
            className="mt-3 inline-block text-sm text-green-700 hover:text-green-900 underline"
          >
            ← Return to case
          </Link>
        </div>
      )}

      {/* Pipeline-wide error hint */}
      {!runningStep && stepError && !pipelineDone && (
        <p className="text-sm text-red-600 px-1">{stepError}</p>
      )}
    </div>
  );
}
