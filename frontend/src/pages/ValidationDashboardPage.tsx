import { useEffect, useState } from "react";
import {
  getValidationByReviewer,
  getValidationBySkinTone,
  getValidationSummary,
} from "../api/validation";
import type {
  FitzpatrickScale,
  ValidationByReviewerOut,
  ValidationBySkinToneOut,
  ValidationSummaryOut,
} from "../types/api";

function pct(v: number | null): string {
  if (v === null) return "—";
  return `${Math.round(v * 100)}%`;
}

function StatCard({
  label,
  value,
  sub,
  color,
}: {
  label: string;
  value: string;
  sub?: string;
  color?: "green" | "blue" | "amber" | "red";
}) {
  const colors: Record<string, string> = {
    green: "text-green-700",
    blue: "text-blue-700",
    amber: "text-amber-700",
    red: "text-red-600",
  };
  return (
    <div className="bg-white rounded-xl border border-slate-200 p-5">
      <p className="text-xs font-medium text-slate-500 uppercase tracking-wide">
        {label}
      </p>
      <p
        className={`text-3xl font-bold mt-1 ${color ? colors[color] : "text-slate-800"}`}
      >
        {value}
      </p>
      {sub && <p className="text-xs text-slate-400 mt-0.5">{sub}</p>}
    </div>
  );
}

const FITZPATRICK_DESCRIPTIONS: Record<FitzpatrickScale, string> = {
  I: "Very fair — always burns",
  II: "Fair — burns easily",
  III: "Medium — sometimes burns",
  IV: "Olive — rarely burns",
  V: "Brown — very rarely burns",
  VI: "Dark — never burns",
};

function AccuracyBar({ rate }: { rate: number | null }) {
  if (rate === null) return <span className="text-slate-400 text-xs">—</span>;
  const pctVal = Math.round(rate * 100);
  const color =
    pctVal >= 80
      ? "bg-green-500"
      : pctVal >= 60
        ? "bg-yellow-400"
        : "bg-red-400";
  return (
    <div className="flex items-center gap-2">
      <div className="flex-1 bg-slate-100 rounded-full h-2 max-w-24">
        <div
          className={`h-2 rounded-full ${color}`}
          style={{ width: `${pctVal}%` }}
        />
      </div>
      <span className="text-xs font-medium text-slate-700">{pctVal}%</span>
    </div>
  );
}

export default function ValidationDashboardPage() {
  const [summary, setSummary] = useState<ValidationSummaryOut | null>(null);
  const [byReviewer, setByReviewer] = useState<ValidationByReviewerOut[]>([]);
  const [bySkinTone, setBySkinTone] = useState<ValidationBySkinToneOut[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    Promise.all([
      getValidationSummary(),
      getValidationByReviewer(),
      getValidationBySkinTone(),
    ])
      .then(([s, r, t]) => {
        setSummary(s);
        setByReviewer(r);
        setBySkinTone(t);
      })
      .catch((e) => setError(e.message ?? "Failed to load validation data."))
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center py-24">
        <span className="text-sm text-slate-400">Loading…</span>
      </div>
    );
  }

  if (error) {
    return (
      <div className="max-w-2xl mx-auto px-6 py-8">
        <div className="rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
          {error}
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto px-6 py-8 space-y-8">
      {/* Header */}
      <div>
        <h1 className="text-xl font-bold text-slate-900">
          Validation Dashboard
        </h1>
        <p className="text-sm text-slate-500 mt-0.5">
          AI accuracy · override rates · skin-tone bias tracking (Fitzpatrick
          I–VI)
        </p>
      </div>

      {/* Summary cards */}
      {summary && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <StatCard
            label="Total Reviews"
            value={String(summary.total_reviews)}
            sub="All assessments reviewed"
          />
          <StatCard
            label="AI Accuracy"
            value={pct(summary.accuracy_rate)}
            sub="AI matched clinician"
            color={
              summary.accuracy_rate !== null
                ? summary.accuracy_rate >= 0.8
                  ? "green"
                  : summary.accuracy_rate >= 0.6
                    ? "amber"
                    : "red"
                : undefined
            }
          />
          <StatCard
            label="Override Rate"
            value={pct(summary.override_rate)}
            sub="Clinician changed AI result"
            color={
              summary.override_rate !== null
                ? summary.override_rate > 0.3
                  ? "red"
                  : summary.override_rate > 0.15
                    ? "amber"
                    : "green"
                : undefined
            }
          />
          <StatCard
            label="Hallucination Rate"
            value={pct(summary.hallucination_rate)}
            sub={
              summary.hallucination_rate === null
                ? "No verdicts recorded yet"
                : "Marked incorrect by clinician"
            }
            color={
              summary.hallucination_rate !== null
                ? summary.hallucination_rate > 0.1
                  ? "red"
                  : "green"
                : undefined
            }
          />
        </div>
      )}

      {/* By Reviewer */}
      <div>
        <h2 className="text-sm font-semibold text-slate-700 uppercase tracking-wide mb-3">
          Accuracy by Reviewer
        </h2>
        <div className="bg-white rounded-xl border border-slate-200 overflow-hidden">
          {byReviewer.length === 0 ? (
            <p className="text-sm text-slate-400 text-center py-8">
              No review data yet.
            </p>
          ) : (
            <table className="w-full text-sm">
              <thead className="bg-slate-50 border-b border-slate-200">
                <tr>
                  <th className="text-left px-4 py-3 text-xs font-semibold text-slate-500 uppercase tracking-wide">
                    Reviewer
                  </th>
                  <th className="text-left px-4 py-3 text-xs font-semibold text-slate-500 uppercase tracking-wide">
                    Role
                  </th>
                  <th className="text-right px-4 py-3 text-xs font-semibold text-slate-500 uppercase tracking-wide">
                    Reviews
                  </th>
                  <th className="text-left px-4 py-3 text-xs font-semibold text-slate-500 uppercase tracking-wide">
                    AI Accuracy
                  </th>
                  <th className="text-right px-4 py-3 text-xs font-semibold text-slate-500 uppercase tracking-wide">
                    Override Rate
                  </th>
                </tr>
              </thead>
              <tbody>
                {byReviewer.map((r, i) => (
                  <tr
                    key={r.reviewer_id}
                    className={`border-b border-slate-100 ${i === byReviewer.length - 1 ? "border-0" : ""}`}
                  >
                    <td className="px-4 py-3 font-medium text-slate-800">
                      {r.reviewer_name}
                    </td>
                    <td className="px-4 py-3 text-slate-500 text-xs capitalize">
                      {r.role.replace(/_/g, " ")}
                    </td>
                    <td className="px-4 py-3 text-right text-slate-600">
                      {r.review_count}
                    </td>
                    <td className="px-4 py-3">
                      <AccuracyBar rate={r.accuracy_rate} />
                    </td>
                    <td className="px-4 py-3 text-right text-slate-600">
                      {pct(r.override_rate)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </div>

      {/* By Skin Tone (Fitzpatrick) */}
      <div>
        <h2 className="text-sm font-semibold text-slate-700 uppercase tracking-wide mb-1">
          Accuracy by Fitzpatrick Skin Tone
        </h2>
        <p className="text-xs text-slate-400 mb-3">
          Identifies skin-tone bias in AI wound classification accuracy
        </p>
        <div className="bg-white rounded-xl border border-slate-200 overflow-hidden">
          {bySkinTone.length === 0 ? (
            <p className="text-sm text-slate-400 text-center py-8">
              No skin tone data recorded yet.
            </p>
          ) : (
            <table className="w-full text-sm">
              <thead className="bg-slate-50 border-b border-slate-200">
                <tr>
                  <th className="text-left px-4 py-3 text-xs font-semibold text-slate-500 uppercase tracking-wide">
                    Scale
                  </th>
                  <th className="text-left px-4 py-3 text-xs font-semibold text-slate-500 uppercase tracking-wide">
                    Description
                  </th>
                  <th className="text-right px-4 py-3 text-xs font-semibold text-slate-500 uppercase tracking-wide">
                    Reviews
                  </th>
                  <th className="text-left px-4 py-3 text-xs font-semibold text-slate-500 uppercase tracking-wide">
                    AI Accuracy
                  </th>
                </tr>
              </thead>
              <tbody>
                {bySkinTone.map((t, i) => (
                  <tr
                    key={t.fitzpatrick_scale}
                    className={`border-b border-slate-100 ${i === bySkinTone.length - 1 ? "border-0" : ""}`}
                  >
                    <td className="px-4 py-3">
                      <span className="inline-flex items-center justify-center w-7 h-7 rounded-full border-2 border-slate-200 text-xs font-bold text-slate-700">
                        {t.fitzpatrick_scale}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-slate-500 text-xs">
                      {FITZPATRICK_DESCRIPTIONS[t.fitzpatrick_scale]}
                    </td>
                    <td className="px-4 py-3 text-right text-slate-600">
                      {t.review_count}
                    </td>
                    <td className="px-4 py-3">
                      <AccuracyBar rate={t.accuracy_rate} />
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
        <p className="mt-2 text-xs text-slate-400 italic">
          Accuracy gaps across skin tone categories may indicate bias in AI
          wound analysis. Skin type documented at time of clinician review.
        </p>
      </div>

      {/* AI available context */}
      {summary && (
        <div className="rounded-lg bg-slate-50 border border-slate-200 px-4 py-3 text-xs text-slate-500">
          <strong>{summary.ai_available_count}</strong> of{" "}
          <strong>{summary.total_reviews}</strong> reviews have AI data. Records
          where AI was unavailable are excluded from accuracy metrics.
        </div>
      )}
    </div>
  );
}
