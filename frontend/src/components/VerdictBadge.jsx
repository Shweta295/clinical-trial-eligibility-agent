const STYLES = {
  ELIGIBLE: "bg-emerald-100 text-emerald-800 border-emerald-200",
  NOT_ELIGIBLE: "bg-red-100 text-red-800 border-red-200",
  PENDING_DATA: "bg-amber-100 text-amber-800 border-amber-200",
  met: "bg-emerald-50 text-emerald-700",
  not_met: "bg-red-50 text-red-700",
  cannot_determine: "bg-amber-50 text-amber-700",
};

const LABELS = {
  ELIGIBLE: "Eligible",
  NOT_ELIGIBLE: "Not Eligible",
  PENDING_DATA: "Pending Data",
  met: "Met",
  not_met: "Not Met",
  cannot_determine: "Undetermined",
};

export default function VerdictBadge({ verdict, large }) {
  const cls = STYLES[verdict] || "bg-slate-100 text-slate-600";
  const label = LABELS[verdict] || verdict;
  return (
    <span
      className={`inline-flex items-center font-semibold rounded-full border ${cls} ${
        large ? "px-4 py-1.5 text-sm" : "px-2.5 py-0.5 text-xs"
      }`}
    >
      {label}
    </span>
  );
}
