import { useState } from "react";
import type {
  ClinicalAssessmentClassifyOut,
  FitzpatrickScale,
  HealingClassification,
  ReviewOut,
} from "../types/api";
import { submitReview } from "../api/pipeline";
import { ApiError } from "../api/client";
import ConfidenceBadge from "./ConfidenceBadge";
import ClassificationBadge from "./ClassificationBadge";

interface Props {
  assessmentId: string;
  classifyResult: ClinicalAssessmentClassifyOut;
  onComplete: (result: ReviewOut) => void;
}

const FITZPATRICK_OPTIONS: FitzpatrickScale[] = [
  "I",
  "II",
  "III",
  "IV",
  "V",
  "VI",
];

const CLASSIFICATION_OPTIONS: HealingClassification[] = [
  "improving",
  "stable",
  "deteriorating",
];

export default function ReviewPanel({
  assessmentId,
  classifyResult,
  onComplete,
}: Props) {
  const [mode, setMode] = useState<"accept" | "override" | null>(null);
  const [fitzpatrick, setFitzpatrick] = useState<FitzpatrickScale | "">("");
  const [overrideClass, setOverrideClass] =
    useState<HealingClassification | "">("");
  const [overrideReason, setOverrideReason] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const isLowConfidence = classifyResult.confidence_tier === "low";

  async function handleAccept() {
    if (!fitzpatrick) {
      setError("Please select a Fitzpatrick skin tone scale value.");
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const result = await submitReview({
        assessment_id: assessmentId,
        review_status: "accepted",
        fitzpatrick_scale: fitzpatrick,
      });
      onComplete(result);
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Review submission failed.");
    } finally {
      setLoading(false);
    }
  }

  async function handleOverride() {
    if (!overrideClass) {
      setError("Please select a classification.");
      return;
    }
    if (!overrideReason.trim()) {
      setError("Override reason is required.");
      return;
    }
    if (!fitzpatrick) {
      setError("Please select a Fitzpatrick skin tone scale value.");
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const result = await submitReview({
        assessment_id: assessmentId,
        review_status: "overridden",
        clinician_classification: overrideClass,
        override_reason: overrideReason.trim(),
        fitzpatrick_scale: fitzpatrick,
      });
      onComplete(result);
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Review submission failed.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="space-y-4">
      {/* AI result summary */}
      <div className="bg-slate-50 rounded-lg p-4 space-y-2 border border-slate-200">
        <div className="flex items-center gap-3 flex-wrap">
          <span className="text-sm font-medium text-slate-700">
            AI Classification:
          </span>
          <ClassificationBadge classification={classifyResult.classification} />
          <ConfidenceBadge
            tier={classifyResult.confidence_tier}
            score={classifyResult.confidence_score}
          />
        </div>
        <div className="text-xs text-slate-500 grid grid-cols-3 gap-2 pt-1">
          <span>
            Area signal: {classifyResult.area_signal_score.toFixed(2)} ×0.50
          </span>
          <span>
            Tissue signal: {classifyResult.tissue_signal_score.toFixed(2)} ×0.30
          </span>
          <span>
            Drainage signal: {classifyResult.drainage_signal_score.toFixed(2)}{" "}
            ×0.20
          </span>
        </div>
      </div>

      {/* Fitzpatrick selector (required for both paths) */}
      <div>
        <label className="block text-sm font-medium text-slate-700 mb-1">
          Fitzpatrick Skin Tone Scale{" "}
          <span className="text-red-500">*</span>
          <span className="ml-1 text-xs font-normal text-slate-400">
            (required for bias tracking)
          </span>
        </label>
        <div className="flex gap-2">
          {FITZPATRICK_OPTIONS.map((f) => (
            <button
              key={f}
              type="button"
              onClick={() => setFitzpatrick(f)}
              className={`w-10 h-10 rounded-lg border-2 text-sm font-semibold transition-colors ${
                fitzpatrick === f
                  ? "border-blue-500 bg-blue-50 text-blue-700"
                  : "border-slate-200 bg-white text-slate-600 hover:border-slate-300"
              }`}
            >
              {f}
            </button>
          ))}
        </div>
        <p className="mt-1 text-xs text-slate-400">
          I = Very fair · VI = Very dark · used to detect skin-tone bias in AI
          accuracy
        </p>
      </div>

      {/* Low confidence warning */}
      {isLowConfidence && (
        <div className="rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
          <strong>Low AI confidence (&lt;60%).</strong> The Accept path is
          unavailable. A clinician override is required before note generation.
        </div>
      )}

      {/* Decision buttons */}
      {mode === null && (
        <div className="flex gap-3">
          <button
            type="button"
            disabled={isLowConfidence}
            onClick={() => setMode("accept")}
            className="flex-1 py-2.5 rounded-lg bg-green-600 text-white text-sm font-semibold hover:bg-green-700 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
          >
            Accept AI Classification
          </button>
          <button
            type="button"
            onClick={() => setMode("override")}
            className="flex-1 py-2.5 rounded-lg bg-amber-500 text-white text-sm font-semibold hover:bg-amber-600 transition-colors"
          >
            Override
          </button>
        </div>
      )}

      {/* Accept confirmation */}
      {mode === "accept" && (
        <div className="rounded-lg border border-green-200 bg-green-50 p-4 space-y-3">
          <p className="text-sm text-green-800">
            Accept AI classification:{" "}
            <strong className="capitalize">
              {classifyResult.classification}
            </strong>{" "}
            at {Math.round(classifyResult.confidence_score * 100)}% confidence.
          </p>
          {error && (
            <p className="text-sm text-red-600">{error}</p>
          )}
          <div className="flex gap-2">
            <button
              type="button"
              onClick={handleAccept}
              disabled={loading}
              className="px-4 py-2 rounded-lg bg-green-600 text-white text-sm font-semibold hover:bg-green-700 disabled:opacity-50 transition-colors"
            >
              {loading ? "Submitting…" : "Confirm Accept"}
            </button>
            <button
              type="button"
              onClick={() => { setMode(null); setError(null); }}
              className="px-4 py-2 rounded-lg border border-slate-200 text-slate-600 text-sm hover:bg-slate-50 transition-colors"
            >
              Back
            </button>
          </div>
        </div>
      )}

      {/* Override form */}
      {mode === "override" && (
        <div className="rounded-lg border border-amber-200 bg-amber-50 p-4 space-y-3">
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">
              Clinician Classification <span className="text-red-500">*</span>
            </label>
            <div className="flex gap-2">
              {CLASSIFICATION_OPTIONS.map((c) => (
                <button
                  key={c}
                  type="button"
                  onClick={() => setOverrideClass(c)}
                  className={`px-3 py-1.5 rounded-lg border text-sm font-medium capitalize transition-colors ${
                    overrideClass === c
                      ? "border-amber-500 bg-amber-100 text-amber-800"
                      : "border-slate-200 bg-white text-slate-600 hover:border-slate-300"
                  }`}
                >
                  {c}
                </button>
              ))}
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">
              Override Reason <span className="text-red-500">*</span>
            </label>
            <textarea
              rows={3}
              value={overrideReason}
              onChange={(e) => setOverrideReason(e.target.value)}
              placeholder="Explain why the AI classification is being overridden…"
              className="w-full rounded-lg border border-slate-200 px-3 py-2 text-sm text-slate-700 focus:outline-none focus:ring-2 focus:ring-amber-400 resize-none bg-white"
            />
          </div>

          {error && (
            <p className="text-sm text-red-600">{error}</p>
          )}

          <div className="flex gap-2">
            <button
              type="button"
              onClick={handleOverride}
              disabled={loading}
              className="px-4 py-2 rounded-lg bg-amber-500 text-white text-sm font-semibold hover:bg-amber-600 disabled:opacity-50 transition-colors"
            >
              {loading ? "Submitting…" : "Confirm Override"}
            </button>
            <button
              type="button"
              onClick={() => { setMode(null); setError(null); }}
              className="px-4 py-2 rounded-lg border border-slate-200 text-slate-600 text-sm hover:bg-slate-50 transition-colors"
            >
              Back
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
