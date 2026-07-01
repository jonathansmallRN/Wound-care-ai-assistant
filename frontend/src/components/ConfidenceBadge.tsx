import type { ConfidenceTier } from "../types/api";

interface Props {
  tier: ConfidenceTier;
  score: number;
}

const TIER_STYLES: Record<ConfidenceTier, string> = {
  high: "bg-green-100 text-green-800 border-green-200",
  medium: "bg-yellow-100 text-yellow-800 border-yellow-200",
  low: "bg-red-100 text-red-800 border-red-200",
};

const TIER_LABELS: Record<ConfidenceTier, string> = {
  high: "High",
  medium: "Medium",
  low: "Low — manual review required",
};

export default function ConfidenceBadge({ tier, score }: Props) {
  return (
    <span
      className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium border ${TIER_STYLES[tier]}`}
    >
      <span
        className={`w-2 h-2 rounded-full ${
          tier === "high"
            ? "bg-green-500"
            : tier === "medium"
              ? "bg-yellow-500"
              : "bg-red-500"
        }`}
      />
      {Math.round(score * 100)}% · {TIER_LABELS[tier]}
    </span>
  );
}
