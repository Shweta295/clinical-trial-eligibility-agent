import { Routes, Route, NavLink } from "react-router-dom";
import { Upload, BarChart3, History, Activity } from "lucide-react";
import UploadPage from "./pages/UploadPage.jsx";
import DashboardPage from "./pages/DashboardPage.jsx";
import HistoryPage from "./pages/HistoryPage.jsx";
import ResultDetailPage from "./pages/ResultDetailPage.jsx";

const NAV = [
  { to: "/", icon: Upload, label: "Upload" },
  { to: "/dashboard", icon: BarChart3, label: "Dashboard" },
  { to: "/history", icon: History, label: "History" },
];

export default function App() {
  return (
    <div className="min-h-screen flex">
      {/* Sidebar — sticky so it stays visible when main content scrolls */}
      <aside className="w-64 bg-teal-800 text-white flex flex-col shrink-0 sticky top-0 h-screen">
        <div className="p-6 border-b border-teal-700">
          <div className="flex items-center gap-3">
            <Activity className="w-8 h-8 text-teal-200" />
            <div>
              <h1 className="text-lg font-bold leading-tight">TrialScreen</h1>
              <p className="text-xs text-teal-300">AI Eligibility Agent</p>
            </div>
          </div>
        </div>
        <nav className="flex-1 p-4 space-y-1">
          {NAV.map(({ to, icon: Icon, label }) => (
            <NavLink
              key={to}
              to={to}
              end={to === "/"}
              className={({ isActive }) =>
                `flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-medium transition-colors ${
                  isActive
                    ? "bg-teal-700 text-white"
                    : "text-teal-200 hover:bg-teal-700/50 hover:text-white"
                }`
              }
            >
              <Icon className="w-5 h-5" />
              {label}
            </NavLink>
          ))}
        </nav>
        <div className="p-4 text-xs text-teal-400 border-t border-teal-700">
          Powered by Claude AI
        </div>
      </aside>

      {/* Main content */}
      <main className="flex-1 overflow-auto">
        <Routes>
          <Route path="/" element={<UploadPage />} />
          <Route path="/dashboard" element={<DashboardPage />} />
          <Route path="/history" element={<HistoryPage />} />
          <Route path="/results/:id" element={<ResultDetailPage />} />
        </Routes>
      </main>
    </div>
  );
}
