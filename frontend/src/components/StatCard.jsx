export default function StatCard({ icon: Icon, label, value, color }) {
  const colorMap = {
    teal: "bg-teal-50 text-teal-600",
    emerald: "bg-emerald-50 text-emerald-600",
    red: "bg-red-50 text-red-600",
    amber: "bg-amber-50 text-amber-600",
    slate: "bg-slate-50 text-slate-600",
  };
  const iconCls = colorMap[color] || colorMap.teal;
  return (
    <div className="bg-white rounded-2xl border border-slate-200 p-6 flex items-center gap-4">
      <div className={`w-12 h-12 rounded-xl flex items-center justify-center ${iconCls}`}>
        <Icon className="w-6 h-6" />
      </div>
      <div>
        <p className="text-2xl font-bold text-slate-800">{value}</p>
        <p className="text-sm text-slate-500">{label}</p>
      </div>
    </div>
  );
}
