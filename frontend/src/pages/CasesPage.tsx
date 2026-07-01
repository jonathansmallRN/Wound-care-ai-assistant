import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { listCases } from "../api/cases";
import type { CaseListItemOut } from "../types/api";

function StatusBadge({ status }: { status: string }) {
  return (
    <span
      className={`inline-block px-2 py-0.5 rounded text-xs font-medium ${
        status === "active"
          ? "bg-green-100 text-green-700"
          : "bg-slate-100 text-slate-500"
      }`}
    >
      {status}
    </span>
  );
}

export default function CasesPage() {
  const navigate = useNavigate();
  const [cases, setCases] = useState<CaseListItemOut[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    listCases()
      .then(setCases)
      .catch((e) => setError(e.message ?? "Failed to load cases."))
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="max-w-4xl mx-auto px-6 py-8">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-xl font-bold text-slate-900">Cases</h1>
          <p className="text-sm text-slate-500 mt-0.5">
            One case per wound tracked over time — no PHI stored.
          </p>
        </div>
        <button
          onClick={() => navigate("/cases/new")}
          className="px-4 py-2 rounded-lg bg-blue-600 text-white text-sm font-semibold hover:bg-blue-700 transition-colors"
        >
          + New Case
        </button>
      </div>

      {/* Error */}
      {error && (
        <div className="mb-4 rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
          {error}
        </div>
      )}

      {/* Loading */}
      {loading && (
        <div className="text-sm text-slate-400 py-12 text-center">
          Loading cases…
        </div>
      )}

      {/* Empty state */}
      {!loading && !error && cases.length === 0 && (
        <div className="text-center py-16 rounded-xl border-2 border-dashed border-slate-200">
          <p className="text-slate-500 font-medium">No cases yet.</p>
          <p className="text-slate-400 text-sm mt-1">
            Create your first case to get started.
          </p>
          <button
            onClick={() => navigate("/cases/new")}
            className="mt-4 px-4 py-2 rounded-lg bg-blue-600 text-white text-sm font-semibold hover:bg-blue-700 transition-colors"
          >
            Create Case
          </button>
        </div>
      )}

      {/* Cases table */}
      {!loading && cases.length > 0 && (
        <div className="bg-white rounded-xl border border-slate-200 overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-slate-50 border-b border-slate-200">
              <tr>
                <th className="text-left px-4 py-3 text-xs font-semibold text-slate-500 uppercase tracking-wide">
                  Case Reference
                </th>
                <th className="text-left px-4 py-3 text-xs font-semibold text-slate-500 uppercase tracking-wide">
                  Status
                </th>
                <th className="text-right px-4 py-3 text-xs font-semibold text-slate-500 uppercase tracking-wide">
                  Assessments
                </th>
                <th className="text-right px-4 py-3 text-xs font-semibold text-slate-500 uppercase tracking-wide">
                  Created
                </th>
                <th className="px-4 py-3" />
              </tr>
            </thead>
            <tbody>
              {cases.map((c, i) => (
                <tr
                  key={c.id}
                  className={`border-b border-slate-100 hover:bg-slate-50 transition-colors ${
                    i === cases.length - 1 ? "border-0" : ""
                  }`}
                >
                  <td className="px-4 py-3 font-medium text-slate-800">
                    {c.case_ref}
                  </td>
                  <td className="px-4 py-3">
                    <StatusBadge status={c.status} />
                  </td>
                  <td className="px-4 py-3 text-right text-slate-600">
                    {c.assessment_count}
                  </td>
                  <td className="px-4 py-3 text-right text-slate-400 text-xs">
                    {new Date(c.created_at).toLocaleDateString()}
                  </td>
                  <td className="px-4 py-3 text-right">
                    <Link
                      to={`/cases/${c.id}`}
                      className="text-blue-600 hover:text-blue-800 font-medium text-xs"
                    >
                      View →
                    </Link>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
