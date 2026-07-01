import { useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { getCase } from "../api/cases";
import { listAssessmentsForCase } from "../api/assessments";
import type { AssessmentDetailOut, CaseDetailOut } from "../types/api";
import ClassificationBadge from "../components/ClassificationBadge";

function ReviewStatusBadge({ status }: { status: string }) {
  const styles: Record<string, string> = {
    pending: "bg-slate-100 text-slate-500",
    accepted: "bg-green-100 text-green-700",
    overridden: "bg-amber-100 text-amber-700",
  };
  return (
    <span
      className={`inline-block px-2 py-0.5 rounded text-xs font-medium ${styles[status] ?? "bg-slate-100 text-slate-500"}`}
    >
      {status}
    </span>
  );
}

export default function CaseDetailPage() {
  const { caseId } = useParams<{ caseId: string }>();
  const navigate = useNavigate();
  const [caseDetail, setCaseDetail] = useState<CaseDetailOut | null>(null);
  const [assessments, setAssessments] = useState<AssessmentDetailOut[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!caseId) return;
    Promise.all([getCase(caseId), listAssessmentsForCase(caseId)])
      .then(([c, a]) => {
        setCaseDetail(c);
        // Sort chronologically
        setAssessments(
          [...a].sort(
            (x, y) =>
              new Date(x.assessment_date).getTime() -
              new Date(y.assessment_date).getTime(),
          ),
        );
      })
      .catch((e) => setError(e.message ?? "Failed to load case."))
      .finally(() => setLoading(false));
  }, [caseId]);

  if (loading) {
    return (
      <div className="flex items-center justify-center py-24">
        <span className="text-sm text-slate-400">Loading…</span>
      </div>
    );
  }

  if (error || !caseDetail) {
    return (
      <div className="max-w-2xl mx-auto px-6 py-8">
        <div className="rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
          {error ?? "Case not found."}
        </div>
        <Link
          to="/"
          className="mt-4 inline-block text-sm text-blue-600 hover:text-blue-800"
        >
          ← Back to cases
        </Link>
      </div>
    );
  }

  return (
    <div className="max-w-3xl mx-auto px-6 py-8 space-y-6">
      {/* Breadcrumb */}
      <Link
        to="/"
        className="text-sm text-slate-400 hover:text-slate-600 transition-colors"
      >
        ← Cases
      </Link>

      {/* Case header */}
      <div className="bg-white rounded-xl border border-slate-200 p-6">
        <div className="flex items-start justify-between">
          <div>
            <h1 className="text-xl font-bold text-slate-900">
              {caseDetail.case_ref}
            </h1>
            <p className="text-sm text-slate-500 mt-0.5">
              Status:{" "}
              <span className="capitalize font-medium text-slate-700">
                {caseDetail.status}
              </span>
              {"  ·  "}
              {caseDetail.assessment_count} assessment
              {caseDetail.assessment_count !== 1 ? "s" : ""}
            </p>
          </div>
          <button
            onClick={() => navigate(`/cases/${caseId}/assessments/new`)}
            className="px-4 py-2 rounded-lg bg-blue-600 text-white text-sm font-semibold hover:bg-blue-700 transition-colors"
          >
            + Add Assessment
          </button>
        </div>
      </div>

      {/* Assessment timeline */}
      <div>
        <h2 className="text-sm font-semibold text-slate-600 uppercase tracking-wide mb-3">
          Assessment Timeline
        </h2>

        {assessments.length === 0 ? (
          <div className="text-center py-12 rounded-xl border-2 border-dashed border-slate-200">
            <p className="text-slate-500 font-medium">No assessments yet.</p>
            <p className="text-slate-400 text-sm mt-1">
              Add a baseline assessment to start tracking this wound.
            </p>
            <button
              onClick={() => navigate(`/cases/${caseId}/assessments/new`)}
              className="mt-4 px-4 py-2 rounded-lg bg-blue-600 text-white text-sm font-semibold hover:bg-blue-700 transition-colors"
            >
              Add Baseline Assessment
            </button>
          </div>
        ) : (
          <div className="space-y-3">
            {assessments.map((a, idx) => (
              <div
                key={a.assessment_id}
                className="bg-white rounded-xl border border-slate-200 p-4 flex items-center gap-4"
              >
                {/* Timeline indicator */}
                <div className="flex flex-col items-center shrink-0 w-8">
                  <div
                    className={`w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold ${
                      a.is_baseline
                        ? "bg-slate-200 text-slate-600"
                        : "bg-blue-100 text-blue-700"
                    }`}
                  >
                    {a.is_baseline ? "B" : idx}
                  </div>
                  {idx < assessments.length - 1 && (
                    <div className="w-0.5 h-3 bg-slate-200 mt-1" />
                  )}
                </div>

                {/* Assessment info */}
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 flex-wrap">
                    <span className="font-medium text-slate-800 text-sm">
                      {new Date(a.assessment_date).toLocaleDateString("en-US", {
                        year: "numeric",
                        month: "short",
                        day: "numeric",
                      })}
                    </span>
                    <span className="text-xs text-slate-400">
                      {a.is_baseline ? "Baseline" : "Follow-up"}
                    </span>
                    <ReviewStatusBadge status={a.review_status} />
                    {a.clinician_classification && (
                      <ClassificationBadge
                        classification={a.clinician_classification}
                      />
                    )}
                  </div>
                  <p className="text-xs text-slate-500 mt-0.5">
                    {a.area_cm2.toFixed(1)} cm² · {a.tissue_type} ·{" "}
                    {a.drainage_amount} {a.drainage_type} drainage
                  </p>
                </div>

                {/* Action */}
                {!a.is_baseline && (
                  <Link
                    to={`/assessments/${a.assessment_id}`}
                    className="shrink-0 text-sm text-blue-600 hover:text-blue-800 font-medium"
                  >
                    {a.review_status === "pending" ? "Run pipeline →" : "View →"}
                  </Link>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
