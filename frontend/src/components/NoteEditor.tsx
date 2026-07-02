import { useState } from "react";
import type { HealingClassification, ConfidenceTier } from "../types/api";
import ClassificationBadge from "./ClassificationBadge";
import ConfidenceBadge from "./ConfidenceBadge";
import { patchNote } from "../api/pipeline";

interface Props {
  assessmentId: string;
  noteDraft: string;
  classification: HealingClassification | null;
  confidenceTier: ConfidenceTier | null;
}

export default function NoteEditor({
  assessmentId,
  noteDraft,
  classification,
  confidenceTier,
}: Props) {
  const [text, setText] = useState(noteDraft);
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);
  const [saveError, setSaveError] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);

  const isDirty = text !== noteDraft && !saved;

  async function copyNote() {
    await navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  }

  async function saveNote() {
    setSaving(true);
    setSaveError(null);
    try {
      await patchNote(assessmentId, text);
      setSaved(true);
      setTimeout(() => setSaved(false), 3000);
    } catch (e) {
      setSaveError(e instanceof Error ? e.message : "Save failed.");
    } finally {
      setSaving(false);
    }
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
        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={saveNote}
            disabled={saving || (!isDirty && !saved)}
            className="px-3 py-1.5 rounded-lg border border-blue-200 bg-blue-600 text-sm text-white hover:bg-blue-700 disabled:opacity-50 transition-colors"
          >
            {saving ? "Saving…" : saved ? "Saved" : "Save"}
          </button>
          <button
            type="button"
            onClick={copyNote}
            className="px-3 py-1.5 rounded-lg border border-slate-200 bg-white text-sm text-slate-600 hover:bg-slate-50 transition-colors"
          >
            {copied ? "Copied!" : "Copy to clipboard"}
          </button>
        </div>
      </div>

      {/* Note text */}
      <textarea
        rows={14}
        value={text}
        onChange={(e) => {
          setText(e.target.value);
          setSaved(false);
        }}
        className="w-full rounded-lg border border-slate-200 bg-white px-4 py-3 text-sm text-slate-700 font-mono leading-relaxed resize-y focus:outline-none focus:ring-2 focus:ring-blue-200"
      />

      {saveError && (
        <p className="text-xs text-red-600">{saveError}</p>
      )}

      <p className="text-xs text-slate-400 italic">
        Edit before copying to your EHR. Changes are saved to this assessment.
        For clinician review only — not a substitute for clinical judgment.
      </p>
    </div>
  );
}
