import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { createCase } from "../api/cases";
import { ApiError } from "../api/client";

export default function NewCasePage() {
  const navigate = useNavigate();
  const [caseRef, setCaseRef] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!caseRef.trim()) {
      setError("Case reference is required.");
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const created = await createCase(caseRef.trim());
      navigate(`/cases/${created.id}`);
    } catch (e) {
      setError(
        e instanceof ApiError ? e.message : "Failed to create case.",
      );
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="max-w-lg mx-auto px-6 py-8">
      <div className="mb-6">
        <Link
          to="/"
          className="text-sm text-slate-400 hover:text-slate-600 transition-colors"
        >
          ← Cases
        </Link>
        <h1 className="text-xl font-bold text-slate-900 mt-2">New Case</h1>
        <p className="text-sm text-slate-500 mt-0.5">
          No PHI — the case reference is a de-identified identifier only.
        </p>
      </div>

      <form
        onSubmit={handleSubmit}
        className="bg-white rounded-xl border border-slate-200 p-6 space-y-5"
      >
        <div>
          <label
            htmlFor="case_ref"
            className="block text-sm font-medium text-slate-700 mb-1"
          >
            Case Reference <span className="text-red-500">*</span>
          </label>
          <input
            id="case_ref"
            type="text"
            value={caseRef}
            onChange={(e) => setCaseRef(e.target.value)}
            placeholder="e.g. PT-2026-0042"
            className="w-full rounded-lg border border-slate-200 px-3 py-2 text-sm text-slate-700 focus:outline-none focus:ring-2 focus:ring-blue-400"
          />
          <p className="mt-1 text-xs text-slate-400">
            Use a de-identified code — never include patient name or DOB.
          </p>
        </div>

        {error && (
          <div className="rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">
            {error}
          </div>
        )}

        <div className="flex gap-3 pt-1">
          <button
            type="submit"
            disabled={loading}
            className="flex-1 py-2.5 rounded-lg bg-blue-600 text-white text-sm font-semibold hover:bg-blue-700 disabled:opacity-50 transition-colors"
          >
            {loading ? "Creating…" : "Create Case"}
          </button>
          <Link
            to="/"
            className="px-4 py-2.5 rounded-lg border border-slate-200 text-slate-600 text-sm hover:bg-slate-50 transition-colors"
          >
            Cancel
          </Link>
        </div>
      </form>
    </div>
  );
}
