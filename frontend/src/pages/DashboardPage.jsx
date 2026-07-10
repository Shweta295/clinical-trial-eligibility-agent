import { useState, useEffect, useMemo } from "react";
import { Users, CheckCircle2, XCircle, AlertTriangle, Activity, Search, ChevronLeft, ChevronRight } from "lucide-react";
import { BarChart, Bar, XAxis, YAxis, Tooltip, Legend, ResponsiveContainer, CartesianGrid } from "recharts";
import { getDashboardStats } from "../api.js";
import StatCard from "../components/StatCard.jsx";

const PAGE_SIZE = 8;

export default function DashboardPage() {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [page, setPage] = useState(1);

  useEffect(() => {
    getDashboardStats().then(setStats).finally(() => setLoading(false));
  }, []);

  const trialEntries = useMemo(() => {
    if (!stats) return [];
    return Object.entries(stats.by_trial);
  }, [stats]);

  const filtered = useMemo(() => {
    if (!search.trim()) return trialEntries;
    const q = search.toLowerCase();
    return trialEntries.filter(
      ([id, t]) =>
        id.toLowerCase().includes(q) ||
        (t.trial_name || "").toLowerCase().includes(q) ||
        (t.condition || "").toLowerCase().includes(q)
    );
  }, [trialEntries, search]);

  const totalPages = Math.max(1, Math.ceil(filtered.length / PAGE_SIZE));
  const safePage = Math.min(page, totalPages);
  const paged = filtered.slice((safePage - 1) * PAGE_SIZE, safePage * PAGE_SIZE);

  useEffect(() => {
    setPage(1);
  }, [search]);

  if (loading) {
    return (
      <div className="p-8 flex items-center justify-center h-full">
        <p className="text-slate-400">Loading dashboard...</p>
      </div>
    );
  }

  if (!stats || stats.total_screenings === 0) {
    return (
      <div className="p-8 max-w-4xl mx-auto">
        <h2 className="text-2xl font-bold text-slate-800 mb-2">Dashboard</h2>
        <div className="mt-12 text-center text-slate-400">
          <Activity className="w-16 h-16 mx-auto mb-4 opacity-30" />
          <p className="text-lg">No screenings yet</p>
          <p className="text-sm mt-1">Upload a patient note to see stats here.</p>
        </div>
      </div>
    );
  }

  const chartData = Object.entries(stats.by_trial).map(([id, t]) => ({
    trial: id.length > 16 ? id.slice(0, 16) + "…" : id,
    Eligible: t.eligible,
    "Not Eligible": t.not_eligible,
    "Pending Data": t.pending_data,
  }));

  return (
    <div className="p-8 max-w-5xl mx-auto">
      <h2 className="text-2xl font-bold text-slate-800 mb-6">Dashboard</h2>

      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        <StatCard icon={Users} label="Patients Screened" value={stats.total_patients} color="teal" />
        <StatCard icon={CheckCircle2} label="Eligible" value={stats.eligible} color="emerald" />
        <StatCard icon={XCircle} label="Not Eligible" value={stats.not_eligible} color="red" />
        <StatCard icon={AlertTriangle} label="Pending Data" value={stats.pending_data} color="amber" />
      </div>

      <div className="bg-white rounded-2xl border border-slate-200 p-6">
        <h3 className="text-lg font-semibold text-slate-700 mb-4">Outcomes by Trial</h3>
        <ResponsiveContainer width="100%" height={340}>
          <BarChart data={chartData} barCategoryGap="20%">
            <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
            <XAxis dataKey="trial" tick={{ fontSize: 12 }} />
            <YAxis allowDecimals={false} tick={{ fontSize: 12 }} />
            <Tooltip
              contentStyle={{
                borderRadius: "12px",
                border: "1px solid #e2e8f0",
                boxShadow: "0 4px 12px rgba(0,0,0,0.08)",
              }}
            />
            <Legend />
            <Bar dataKey="Eligible" fill="#10b981" radius={[6, 6, 0, 0]} />
            <Bar dataKey="Not Eligible" fill="#ef4444" radius={[6, 6, 0, 0]} />
            <Bar dataKey="Pending Data" fill="#f59e0b" radius={[6, 6, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>

      {/* Per-trial table */}
      <div className="mt-6 bg-white rounded-2xl border border-slate-200 overflow-hidden">
        {/* Search */}
        <div className="p-4 border-b border-slate-100">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
            <input
              type="text"
              placeholder="Search by trial ID, name, or condition..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full pl-10 pr-4 py-2 rounded-xl border border-slate-200 bg-slate-50 text-sm
                text-slate-700 placeholder:text-slate-400 focus:outline-none focus:border-teal-400 focus:ring-2 focus:ring-teal-100"
            />
          </div>
        </div>

        <table className="w-full text-sm">
          <thead>
            <tr className="bg-slate-50 text-left text-slate-500">
              <th className="px-6 py-3 font-medium">Trial</th>
              <th className="px-4 py-3 font-medium text-center">Screenings</th>
              <th className="px-4 py-3 font-medium text-center">Eligible</th>
              <th className="px-4 py-3 font-medium text-center">Not Eligible</th>
              <th className="px-4 py-3 font-medium text-center">Pending</th>
              <th className="px-4 py-3 font-medium text-center">Rate</th>
            </tr>
          </thead>
          <tbody>
            {paged.map(([id, t]) => (
              <tr key={id} className="border-t border-slate-100">
                <td className="px-6 py-4">
                  <div className="flex items-center gap-2">
                    <p className="font-medium text-slate-800">{id}</p>
                    {t.condition && (
                      <span className="text-[10px] font-semibold px-2 py-0.5 rounded-full bg-teal-50 text-teal-700 border border-teal-200 whitespace-nowrap">
                        {t.condition}
                      </span>
                    )}
                  </div>
                  <p className="text-xs text-slate-400 truncate max-w-md mt-0.5">{t.trial_name}</p>
                </td>
                <td className="px-4 py-4 text-center font-medium">{t.total_screenings}</td>
                <td className="px-4 py-4 text-center text-emerald-600 font-medium">{t.eligible}</td>
                <td className="px-4 py-4 text-center text-red-600 font-medium">{t.not_eligible}</td>
                <td className="px-4 py-4 text-center text-amber-600 font-medium">{t.pending_data}</td>
                <td className="px-4 py-4 text-center font-semibold text-teal-700">{t.eligibility_rate}%</td>
              </tr>
            ))}
            {paged.length === 0 && (
              <tr>
                <td colSpan={6} className="px-6 py-8 text-center text-slate-400">
                  No trials match your search.
                </td>
              </tr>
            )}
          </tbody>
        </table>

        {/* Pagination */}
        {totalPages > 1 && (
          <div className="flex items-center justify-between px-6 py-4 border-t border-slate-100">
            <p className="text-sm text-slate-400">
              Showing {(safePage - 1) * PAGE_SIZE + 1}–{Math.min(safePage * PAGE_SIZE, filtered.length)} of {filtered.length} trials
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
      </div>
    </div>
  );
}
