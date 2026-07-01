import { useState } from "react";
import type { HealingClassification, ConfidenceTier } from "../types/api";
import ClassificationBadge from "./ClassificationBadge";
import ConfidenceBadge from "./ConfidenceBadge";

interface Props {
  noteDraft: string;
  classification: HealingClassification | null;
  confidenceTier: ConfidenceTier | null;
}

export default function NoteEditor({
  noteDraft,
  classification,
  confidenceTier,
}: Props) {
  const [copied, setCopied] = useState(false);

  async function copyNote() {
    await navigator.clipboard.writeText(noteDraft);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  }

  return (
    <div className="space-y-3">
      {/* Header row */}
      <div className="flex items-center justify-between flex-wrap gap-2">
        <div className="flex items-center gap-2 flex-wrap">
          {classification && (
            <ClassificationBadge classification={classification} />
          )}
          {classification && confidenceTier && (
            <ConfidenceBadge
              tier={confidenceTier}
              score={
                confidenceTier === "high"
                  ? 0.86
                  : confidenceTier === "medium"
                    ? 0.70
                    : 0.45
              }
            />
          )}
        </div>
        <button
          type="button"
          onClick={copyNote}
          className="px-3 py-1.5 rounded-lg border border-slate-200 bg-white text-sm text-slate-600 hover:bg-slate-50 transition-colors"
        >
          {copied ? "Copied!" : "Copy to clipboard"}
        </button>
      </div>

      {/* Note text */}
      <textarea
        readOnly
        rows={14}
        value={noteDraft}
        className="w-full rounded-lg border border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-700 font-mono leading-relaxed resize-none focus:outline-none cursor-text"
      />

      <p className="text-xs text-slate-400 italic">
        Progress note saved. Copy to your EHR system. For clinician review only
        — not a substitute for clinical judgment.
      </p>
    </div>
  );
}
