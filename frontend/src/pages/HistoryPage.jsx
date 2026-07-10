import { useState, useEffect, useMemo } from "react";
import { useNavigate } from "react-router-dom";
import { Clock, ChevronRight, Search, ChevronLeft, Filter } from "lucide-react";
import { getResults } from "../api.js";
import VerdictBadge from "../components/VerdictBadge.jsx";

const PAGE_SIZE = 10;

const FILTERS = [
  { key: "ALL", label: "All", bg: "bg-slate-100", text: "text-slate-700", activeBg: "bg-slate-700", activeText: "text-white" },
  { key: "ELIGIBLE", label: "Eligible", bg: "bg-emerald-50", text: "text-emerald-700", activeBg: "bg-emerald-600", activeText: "text-white" },
  { key: "NOT_ELIGIBLE", label: "Not Eligible", bg: "bg-red-50", text: "text-red-700", activeBg: "bg-red-600", activeText: "text-white" },
  { key: "PENDING_DATA", label: "Pending Data", bg: "bg-amber-50", text: "text-amber-700", activeBg: "bg-amber-500", activeText: "text-white" },
];

export default function HistoryPage() {
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [verdictFilter, setVerdictFilter] = useState("ALL");
  const [page, setPage] = useState(1);
  const navigate = useNavigate();

  useEffect(() => {
    getResults().then(setResults).finally(() => setLoading(false));
  }, []);

  const filtered = useMemo(() => {
    let list = results;

    if (verdictFilter !== "ALL") {
      list = list.filter((r) => r.eligibility === verdictFilter);
    }

    if (search.trim()) {
      const q = search.toLowerCase();
      list = list.filter(
        (r) =>
          (r.patient_name || "").toLowerCase().includes(q) ||
          (r.trial_id || "").toLowerCase().includes(q) ||
          (r.trial_condition || "").toLowerCase().includes(q) ||
          (r.eligibility || "").toLowerCase().includes(q)
      );
    }

    return list;
  }, [results, search, verdictFilter]);

  const counts = useMemo(() => {
    const c = { ALL: results.length, ELIGIBLE: 0, NOT_ELIGIBLE: 0, PENDING_DATA: 0 };
    for (const r of results) {
      if (r.eligibility in c) c[r.eligibility]++;
    }
    return c;
  }, [results]);

  const totalPages = Math.max(1, Math.ceil(filtered.length / PAGE_SIZE));
  const safePage = Math.min(page, totalPages);
  const paged = filtered.slice((safePage - 1) * PAGE_SIZE, safePage * PAGE_SIZE);

  useEffect(() => {
    setPage(1);
  }, [search, verdictFilter]);

  if (loading) {
    return (
      <div className="p-8 flex items-center justify-center h-full">
        <p className="text-slate-400">Loading history...</p>
      </div>
    );
  }

  return (
    <div className="p-8 max-w-4xl mx-auto">
      <h2 className="text-2xl font-bold text-slate-800 mb-2">Screening History</h2>
      <p className="text-slate-500 mb-6">All past eligibility evaluations, most recent first.</p>

      {results.length === 0 ? (
        <div className="text-center text-slate-400 mt-16">
          <Clock className="w-16 h-16 mx-auto mb-4 opacity-30" />
          <p className="text-lg">No screenings yet</p>
        </div>
      ) : (
        <>
          {/* Search */}
          <div className="relative mb-4">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
            <input
              type="text"
              placeholder="Search by patient name, trial ID, condition, or verdict..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full pl-10 pr-4 py-2.5 rounded-xl border border-slate-200 bg-white text-sm
                text-slate-700 placeholder:text-slate-400 focus:outline-none focus:border-teal-400 focus:ring-2 focus:ring-teal-100"
            />
          </div>

          {/* Verdict filter chips */}
          <div className="flex items-center gap-2 mb-5">
            <Filter className="w-4 h-4 text-slate-400" />
            {FILTERS.map((f) => {
              const active = verdictFilter === f.key;
              return (
                <button
                  key={f.key}
                  onClick={() => setVerdictFilter(f.key)}
                  className={`px-3 py-1.5 rounded-lg text-xs font-semibold border transition-colors ${
                    active
                      ? `${f.activeBg} ${f.activeText} border-transparent`
                      : `${f.bg} ${f.text} border-slate-200 hover:opacity-80`
                  }`}
                >
                  {f.label}
                  <span className={`ml-1.5 ${active ? "opacity-80" : "opacity-60"}`}>
                    {counts[f.key]}
                  </span>
                </button>
              );
            })}
          </div>

          {filtered.length === 0 ? (
            <p className="text-center text-slate-400 mt-8">No results match your filters.</p>
          ) : (
            <>
              <div className="space-y-3">
                {paged.map((r) => (
                  <button
                    key={r.id}
                    onClick={() => navigate(`/results/${r.id}`)}
                    className="w-full bg-white rounded-2xl border border-slate-200 p-5 flex items-center gap-4
                      hover:border-teal-300 hover:shadow-sm transition-all text-left"
                  >
                    <div className="flex-1 min-w-0">
                      <p className="font-semibold text-slate-800 truncate">
                        {r.patient_name || r.patient_id}
                      </p>
                      <p className="text-sm text-slate-500 mt-0.5">
                        Trial: {r.trial_id}
                        {r.trial_condition && (
                          <span className="ml-2 text-[10px] font-semibold px-2 py-0.5 rounded-full bg-teal-50 text-teal-700 border border-teal-200">
                            {r.trial_condition}
                          </span>
                        )}
                      </p>
                      <p className="text-xs text-slate-400 mt-1">
                        {r.created_at ? new Date(r.created_at).toLocaleString() : ""}
                      </p>
                    </div>
                    <VerdictBadge verdict={r.eligibility} />
                    <ChevronRight className="w-5 h-5 text-slate-300" />
                  </button>
                ))}
              </div>

              {/* Pagination */}
              {totalPages > 1 && (
                <div className="flex items-center justify-between mt-6">
                  <p className="text-sm text-slate-400">
                    Showing {(safePage - 1) * PAGE_SIZE + 1}–{Math.min(safePage * PAGE_SIZE, filtered.length)} of {filtered.length}
                  </p>
                  <div className="flex items-center gap-2">
                    <button
                      onClick={() => setPage((p) => Math.max(1, p - 1))}
                      disabled={safePage === 1}
                      className="p-2 rounded-lg border border-slate-200 text-slate-500 hover:bg-slate-50
                        disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
                    >
                      <ChevronLeft className="w-4 h-4" />
                    </button>
                    {Array.from({ length: totalPages }, (_, i) => i + 1).map((n) => (
                      <button
                        key={n}
                        onClick={() => setPage(n)}
                        className={`w-8 h-8 rounded-lg text-sm font-medium transition-colors ${
                          n === safePage
                            ? "bg-teal-600 text-white"
                            : "border border-slate-200 text-slate-500 hover:bg-slate-50"
                        }`}
                      >
                        {n}
                      </button>
                    ))}
                    <button
                      onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                      disabled={safePage === totalPages}
                      className="p-2 rounded-lg border border-slate-200 text-slate-500 hover:bg-slate-50
                        disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
                    >
                      <ChevronRight className="w-4 h-4" />
                    </button>
                  </div>
                </div>
              )}
            </>
          )}
        </>
      )}
    </div>
  );
}
