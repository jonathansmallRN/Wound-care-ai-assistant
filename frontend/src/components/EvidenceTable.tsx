import type { EvidenceItem, HealingClassification } from "../types/api";

interface Props {
  evidence: EvidenceItem[];
  classification: HealingClassification;
  confidenceScore: number;
}

export default function EvidenceTable({
  evidence,
  classification,
  confidenceScore,
}: Props) {
  return (
    <div className="space-y-3">
      <div className="text-sm text-slate-600">
        <span className="font-medium">Classification:</span>{" "}
        <span className="capitalize font-semibold text-slate-800">
          {classification}
        </span>
        {"  ·  "}
        <span className="font-medium">Confidence:</span>{" "}
        <span className="font-semibold text-slate-800">
          {Math.round(confidenceScore * 100)}%
        </span>
      </div>

      <div className="text-xs font-medium text-slate-500 uppercase tracking-wide">
        Evidence trail (FR-7)
      </div>

      <table className="w-full text-sm border border-slate-200 rounded-lg overflow-hidden">
        <thead className="bg-slate-50">
          <tr>
            <th className="text-left px-3 py-2 text-xs font-medium text-slate-600 border-b border-slate-200">
              Finding
            </th>
            <th className="text-right px-3 py-2 text-xs font-medium text-slate-600 border-b border-slate-200">
              Score
            </th>
            <th className="text-right px-3 py-2 text-xs font-medium text-slate-600 border-b border-slate-200">
              Weight
            </th>
            <th className="text-right px-3 py-2 text-xs font-medium text-slate-600 border-b border-slate-200">
              Contribution
            </th>
            <th className="text-center px-3 py-2 text-xs font-medium text-slate-600 border-b border-slate-200">
              Signal
            </th>
          </tr>
        </thead>
        <tbody>
          {evidence.map((item, i) => (
            <tr
              key={i}
              className={i % 2 === 0 ? "bg-white" : "bg-slate-50/50"}
            >
              <td className="px-3 py-2 text-slate-700">{item.finding}</td>
              <td className="px-3 py-2 text-right text-slate-600">
                {item.score.toFixed(2)}
              </td>
              <td className="px-3 py-2 text-right text-slate-600">
                {Math.round(item.weight * 100)}%
              </td>
              <td className="px-3 py-2 text-right font-medium text-slate-700">
                {(item.score * item.weight).toFixed(3)}
              </td>
              <td className="px-3 py-2 text-center">
                {item.supports_classification === true ? (
                  <span className="text-green-600 font-medium text-xs">
                    Supports
                  </span>
                ) : item.supports_classification === false ? (
                  <span className="text-red-600 font-medium text-xs">
                    Against
                  </span>
                ) : (
                  <span className="text-slate-400 text-xs">Neutral</span>
                )}
              </td>
            </tr>
          ))}
        </tbody>
        <tfoot className="bg-slate-50 border-t border-slate-200">
          <tr>
            <td
              colSpan={3}
              className="px-3 py-2 text-xs font-semibold text-slate-600 text-right"
            >
              Total confidence:
            </td>
            <td className="px-3 py-2 text-right font-bold text-slate-800">
              {Math.round(confidenceScore * 100)}%
            </td>
            <td />
          </tr>
        </tfoot>
      </table>

      <p className="text-xs text-slate-400 italic">
        Formula: (area × 0.50) + (tissue × 0.30) + (drainage × 0.20). For
        clinician review only — not a clinical determination.
      </p>
    </div>
  );
}
