import type { HealingClassification } from "../types/api";

interface Props {
  classification: HealingClassification;
}

const STYLES: Record<HealingClassification, string> = {
  improving: "bg-green-100 text-green-800 border-green-200",
  stable: "bg-blue-100 text-blue-800 border-blue-200",
  deteriorating: "bg-red-100 text-red-800 border-red-200",
};

export default function ClassificationBadge({ classification }: Props) {
  return (
    <span
      className={`inline-block px-2.5 py-1 rounded-full text-xs font-semibold border capitalize ${STYLES[classification]}`}
    >
      {classification}
    </span>
  );
}
