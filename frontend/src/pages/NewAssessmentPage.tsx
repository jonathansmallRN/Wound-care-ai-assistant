import { useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { createAssessment } from "../api/assessments";
import { ApiError } from "../api/client";

const TISSUE_TYPES = ["granulation", "slough", "eschar", "epithelial", "mixed"];
const DRAINAGE_AMOUNTS = ["none", "minimal", "moderate", "heavy"];
const DRAINAGE_TYPES = ["serous", "serosanguineous", "sanguineous", "purulent"];
const PERIWOUND_OPTIONS = ["intact", "macerated", "erythema", "induration"];

function SelectField({
  label,
  value,
  options,
  onChange,
  required,
}: {
  label: string;
  value: string;
  options: string[];
  onChange: (v: string) => void;
  required?: boolean;
}) {
  return (
    <div>
      <label className="block text-sm font-medium text-slate-700 mb-1">
        {label} {required && <span className="text-red-500">*</span>}
      </label>
      <select
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="w-full rounded-lg border border-slate-200 px-3 py-2 text-sm text-slate-700 focus:outline-none focus:ring-2 focus:ring-blue-400 bg-white"
      >
        <option value="">Select…</option>
        {options.map((o) => (
          <option key={o} value={o} className="capitalize">
            {o}
          </option>
        ))}
      </select>
    </div>
  );
}

function NumberField({
  label,
  value,
  onChange,
  step = "0.1",
}: {
  label: string;
  value: string;
  onChange: (v: string) => void;
  step?: string;
}) {
  return (
    <div>
      <label className="block text-sm font-medium text-slate-700 mb-1">
        {label} <span className="text-red-500">*</span>
      </label>
      <div className="relative">
        <input
          type="number"
          min="0"
          step={step}
          value={value}
          onChange={(e) => onChange(e.target.value)}
          className="w-full rounded-lg border border-slate-200 px-3 py-2 pr-10 text-sm text-slate-700 focus:outline-none focus:ring-2 focus:ring-blue-400"
        />
        <span className="absolute right-3 top-1/2 -translate-y-1/2 text-xs text-slate-400">
          cm
        </span>
      </div>
    </div>
  );
}

export default function NewAssessmentPage() {
  const { caseId } = useParams<{ caseId: string }>();
  const navigate = useNavigate();

  const [date, setDate] = useState(new Date().toISOString().slice(0, 10));
  const [length, setLength] = useState("");
  const [width, setWidth] = useState("");
  const [depth, setDepth] = useState("");
  const [tissueType, setTissueType] = useState("");
  const [drainageAmount, setDrainageAmount] = useState("");
  const [drainageType, setDrainageType] = useState("");
  const [periwound, setPeriwound] = useState("");
  const [notes, setNotes] = useState("");

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Computed preview
  const area =
    length && width ? (parseFloat(length) * parseFloat(width)).toFixed(2) : null;
  const volume =
    length && width && depth
      ? (parseFloat(length) * parseFloat(width) * parseFloat(depth)).toFixed(2)
      : null;

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    const missing = [];
    if (!date) missing.push("assessment date");
    if (!length) missing.push("length");
    if (!width) missing.push("width");
    if (!depth) missing.push("depth");
    if (!tissueType) missing.push("tissue type");
    if (!drainageAmount) missing.push("drainage amount");
    if (!drainageType) missing.push("drainage type");
    if (!periwound) missing.push("periwound");
    if (missing.length > 0) {
      setError(`Required fields missing: ${missing.join(", ")}.`);
      return;
    }
    if (!caseId) return;

    setLoading(true);
    setError(null);
    try {
      const result = await createAssessment({
        case_id: caseId,
        assessment_date: date,
        length_cm: parseFloat(length),
        width_cm: parseFloat(width),
        depth_cm: parseFloat(depth),
        tissue_type: tissueType,
        drainage_amount: drainageAmount,
        drainage_type: drainageType,
        periwound,
        notes: notes.trim() || undefined,
      });

      if (result.is_baseline) {
        // Baseline — auto-saved, no review step. Go back to case.
        navigate(`/cases/${caseId}`, {
          state: { message: "Baseline assessment saved." },
        });
      } else {
        // Follow-up — go to the AI pipeline workflow.
        navigate(`/assessments/${result.assessment_id}`);
      }
    } catch (e) {
      setError(
        e instanceof ApiError ? e.message : "Failed to save assessment.",
      );
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="max-w-2xl mx-auto px-6 py-8">
      <div className="mb-6">
        <Link
          to={`/cases/${caseId}`}
          className="text-sm text-slate-400 hover:text-slate-600 transition-colors"
        >
          ← Case
        </Link>
        <h1 className="text-xl font-bold text-slate-900 mt-2">
          New Assessment
        </h1>
        <p className="text-sm text-slate-500 mt-0.5">
          If this is the first assessment for this case, it will be stored as
          the baseline — no AI classification is generated.
        </p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Date */}
        <div className="bg-white rounded-xl border border-slate-200 p-5 space-y-4">
          <h2 className="text-sm font-semibold text-slate-700">Visit date</h2>
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">
              Assessment Date <span className="text-red-500">*</span>
            </label>
            <input
              type="date"
              value={date}
              onChange={(e) => setDate(e.target.value)}
              className="rounded-lg border border-slate-200 px-3 py-2 text-sm text-slate-700 focus:outline-none focus:ring-2 focus:ring-blue-400"
            />
          </div>
        </div>

        {/* Measurements */}
        <div className="bg-white rounded-xl border border-slate-200 p-5 space-y-4">
          <h2 className="text-sm font-semibold text-slate-700">
            Wound measurements
          </h2>
          <div className="grid grid-cols-3 gap-4">
            <NumberField label="Length" value={length} onChange={setLength} />
            <NumberField label="Width" value={width} onChange={setWidth} />
            <NumberField label="Depth" value={depth} onChange={setDepth} />
          </div>
          {area && (
            <div className="rounded-lg bg-slate-50 px-3 py-2 text-xs text-slate-600 flex gap-4">
              <span>
                Area: <strong>{area} cm²</strong>
              </span>
              {volume && (
                <span>
                  Volume: <strong>{volume} cm³</strong>
                </span>
              )}
              <span className="text-slate-400">
                (computed on save; stored — not recalculated)
              </span>
            </div>
          )}
        </div>

        {/* Clinical observations */}
        <div className="bg-white rounded-xl border border-slate-200 p-5 space-y-4">
          <h2 className="text-sm font-semibold text-slate-700">
            Clinical observations
          </h2>
          <div className="grid grid-cols-2 gap-4">
            <SelectField
              label="Tissue Type"
              value={tissueType}
              options={TISSUE_TYPES}
              onChange={setTissueType}
              required
            />
            <SelectField
              label="Drainage Amount"
              value={drainageAmount}
              options={DRAINAGE_AMOUNTS}
              onChange={setDrainageAmount}
              required
            />
            <SelectField
              label="Drainage Type"
              value={drainageType}
              options={DRAINAGE_TYPES}
              onChange={setDrainageType}
              required
            />
            <SelectField
              label="Periwound Condition"
              value={periwound}
              options={PERIWOUND_OPTIONS}
              onChange={setPeriwound}
              required
            />
          </div>
        </div>

        {/* Notes */}
        <div className="bg-white rounded-xl border border-slate-200 p-5 space-y-3">
          <h2 className="text-sm font-semibold text-slate-700">
            Clinician notes
          </h2>
          <textarea
            rows={3}
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
            placeholder="Optional clinical notes for this visit…"
            className="w-full rounded-lg border border-slate-200 px-3 py-2 text-sm text-slate-700 focus:outline-none focus:ring-2 focus:ring-blue-400 resize-none"
          />
        </div>

        {/* Error */}
        {error && (
          <div className="rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
            {error}
          </div>
        )}

        {/* Submit */}
        <div className="flex gap-3">
          <button
            type="submit"
            disabled={loading}
            className="flex-1 py-2.5 rounded-lg bg-blue-600 text-white text-sm font-semibold hover:bg-blue-700 disabled:opacity-50 transition-colors"
          >
            {loading ? "Saving…" : "Save Assessment"}
          </button>
          <Link
            to={`/cases/${caseId}`}
            className="px-5 py-2.5 rounded-lg border border-slate-200 text-slate-600 text-sm hover:bg-slate-50 transition-colors"
          >
            Cancel
          </Link>
        </div>
      </form>
    </div>
  );
}
