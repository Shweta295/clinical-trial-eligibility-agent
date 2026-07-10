import { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import {
  ArrowLeft, Download, Loader2, Search, ShieldCheck, Brain, ChevronDown, ChevronUp,
} from "lucide-react";
import { getResultDetail, downloadResultPdf } from "../api.js";
import VerdictBadge from "../components/VerdictBadge.jsx";

function SimilarityBar({ score, isCurrentTrial }) {
  const pct = Math.round(score * 100);
  const width = `${pct}%`;
  return (
    <div className="flex items-center gap-3">
      <div className="flex-1 h-3 bg-slate-100 rounded-full overflow-hidden">
        <div
          className={`h-full rounded-full transition-all ${
            isCurrentTrial ? "bg-teal-500" : "bg-slate-300"
          }`}
          style={{ width }}
        />
      </div>
      <span className={`text-sm font-mono font-semibold w-14 text-right ${
        isCurrentTrial ? "text-teal-700" : "text-slate-500"
      }`}>
        {pct}%
      </span>
    </div>
  );
}

function StepHeader({ number, title, icon: Icon, status, children }) {
  const [open, setOpen] = useState(true);
  const statusColors = {
    complete: "bg-emerald-100 text-emerald-700 border-emerald-200",
    failed: "bg-red-100 text-red-700 border-red-200",
    active: "bg-teal-100 text-teal-700 border-teal-200",
  };
  const connectorColor = status === "failed" ? "bg-red-200" : "bg-teal-200";

  return (
    <div className="relative">
      {number < 4 && (
        <div className={`absolute left-6 top-14 w-0.5 ${connectorColor}`}
             style={{ height: "calc(100% - 3.5rem)" }} />
      )}
      <button
        onClick={() => setOpen(!open)}
        className="w-full flex items-center gap-4 group"
      >
        <div className={`w-12 h-12 rounded-2xl flex items-center justify-center border-2 shrink-0
          ${status === "failed"
            ? "border-red-300 bg-red-50"
            : "border-teal-300 bg-teal-50"}`}
        >
          <Icon className={`w-5 h-5 ${
            status === "failed" ? "text-red-600" : "text-teal-600"
          }`} />
        </div>
        <div className="flex-1 text-left">
          <div className="flex items-center gap-2">
            <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
              Step {number}
            </span>
            {status && (
              <span className={`text-xs px-2 py-0.5 rounded-full border font-medium ${statusColors[status]}`}>
                {status === "complete" ? "Passed" : status === "failed" ? "Failed" : "Active"}
              </span>
            )}
          </div>
          <h3 className="text-base font-bold text-slate-800">{title}</h3>
        </div>
        {open ? <ChevronUp className="w-5 h-5 text-slate-400" /> : <ChevronDown className="w-5 h-5 text-slate-400" />}
      </button>
      {open && (
        <div className="ml-16 mt-4 mb-8">{children}</div>
      )}
    </div>
  );
}

export default function ResultDetailPage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(true);
  const [downloading, setDownloading] = useState(false);

  useEffect(() => {
    getResultDetail(id).then(setResult).finally(() => setLoading(false));
  }, [id]);

  if (loading) {
    return (
      <div className="p-8 flex items-center justify-center h-full">
        <Loader2 className="w-6 h-6 animate-spin text-teal-500" />
      </div>
    );
  }

  if (!result) {
    return (
      <div className="p-8">
        <p className="text-red-500">Result not found.</p>
      </div>
    );
  }

  const fr = result.full_result || {};
  const patient = fr.patient || {};
  const summary = fr.summary || result.summary || {};
  const steps = fr.pipeline_steps || {};
  const semanticSearch = steps.semantic_search || [];
  const hardRule = steps.hard_rule_screening || {};
  const aiReasoning = steps.ai_reasoning || {};

  const hardDetails = hardRule.details || [];
  const aiDetails = aiReasoning.details || [];

  const allCriteria = [
    ...(result.disqualifying || []).map((c) => ({ ...c, verdict: "not_met" })),
    ...(result.missing_data || []).map((c) => ({
      criterion: c.criterion,
      field: c.field,
      reason: c.data_needed,
      verdict: "cannot_determine",
    })),
    ...(result.criteria_met || []).map((c) => ({ ...c, verdict: "met" })),
  ];

  const hasPipelineSteps = semanticSearch.length > 0 || hardDetails.length > 0;

  return (
    <div className="p-8 max-w-4xl mx-auto">
      <button
        onClick={() => navigate(-1)}
        className="flex items-center gap-2 text-sm text-teal-700 hover:text-teal-900 mb-6"
      >
        <ArrowLeft className="w-4 h-4" /> Back
      </button>

      {/* Header */}
      <div className="bg-white rounded-2xl border border-slate-200 p-6 mb-6">
        {/* Top row: verdict + download */}
        <div className="flex items-center justify-between mb-4">
          <div className={`inline-flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-bold ${
            result.eligibility === "ELIGIBLE"
              ? "bg-emerald-50 text-emerald-700 border border-emerald-200"
              : result.eligibility === "NOT_ELIGIBLE"
              ? "bg-red-50 text-red-700 border border-red-200"
              : "bg-amber-50 text-amber-700 border border-amber-200"
          }`}>
            <span className={`w-2.5 h-2.5 rounded-full ${
              result.eligibility === "ELIGIBLE" ? "bg-emerald-500"
                : result.eligibility === "NOT_ELIGIBLE" ? "bg-red-500" : "bg-amber-500"
            }`} />
            {result.eligibility === "ELIGIBLE" ? "Eligible" : result.eligibility === "NOT_ELIGIBLE" ? "Not Eligible" : "Pending Data"}
          </div>
          <button
            onClick={async () => {
              setDownloading(true);
              try { await downloadResultPdf(id); } finally { setDownloading(false); }
            }}
            disabled={downloading}
            className="inline-flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-medium
              bg-teal-600 text-white hover:bg-teal-700 shadow-sm
              disabled:opacity-50 transition-colors"
          >
            {downloading
              ? <><Loader2 className="w-4 h-4 animate-spin" /> Generating...</>
              : <><Download className="w-4 h-4" /> Download PDF</>
            }
          </button>
        </div>

        {/* Patient info */}
        <h2 className="text-xl font-bold text-slate-800">
          {result.patient_name || result.patient_id}
        </h2>
        <p className="text-sm text-slate-500 mt-1">
          {patient.age}yo {patient.sex} — {patient.cancer_type}, Stage {patient.stage}
          {patient.ECOG != null && `, ECOG ${patient.ECOG}`}
        </p>
        <p className="text-sm text-slate-400 mt-1">
          Trial: {result.trial_id}
          {result.created_at && (
            <span className="ml-3">{new Date(result.created_at).toLocaleString()}</span>
          )}
        </p>

        {/* Summary counters */}
        <div className="grid grid-cols-3 gap-4 mt-5">
          <div className="text-center p-3 bg-emerald-50 rounded-xl">
            <p className="text-2xl font-bold text-emerald-700">{summary.met || 0}</p>
            <p className="text-xs text-emerald-600">Met</p>
          </div>
          <div className="text-center p-3 bg-red-50 rounded-xl">
            <p className="text-2xl font-bold text-red-700">{summary.not_met || 0}</p>
            <p className="text-xs text-red-600">Not Met</p>
          </div>
          <div className="text-center p-3 bg-amber-50 rounded-xl">
            <p className="text-2xl font-bold text-amber-700">{summary.cannot_determine || 0}</p>
            <p className="text-xs text-amber-600">Undetermined</p>
          </div>
        </div>
      </div>

      {/* AI Pipeline Steps */}
      {hasPipelineSteps ? (
        <div className="bg-white rounded-2xl border border-slate-200 p-6 mb-6">
          <h3 className="text-lg font-bold text-slate-800 mb-1">AI Pipeline</h3>
          <p className="text-sm text-slate-400 mb-6">
            Three-stage eligibility analysis from semantic search to clinical reasoning
          </p>

          {/* Step 1 — Semantic Search */}
          <StepHeader
            number={1}
            title="Semantic Trial Search"
            icon={Search}
            status="complete"
          >
            <p className="text-sm text-slate-500 mb-4">
              Top {semanticSearch.length} candidate trials ranked by vector similarity (Voyage AI + pgvector)
            </p>
            <div className="space-y-3 max-h-[500px] overflow-y-auto pr-1">
              {semanticSearch.map((c) => {
                const isCurrent = c.trial_id === result.trial_id;
                return (
                  <div key={c.trial_id}
                    className={`p-3 rounded-xl border ${
                      isCurrent
                        ? "border-teal-200 bg-teal-50/50"
                        : "border-slate-100 bg-slate-50/50"
                    }`}
                  >
                    <div className="flex items-center justify-between mb-1.5">
                      <div className="flex items-center gap-2">
                        <span className={`text-sm font-semibold ${
                          isCurrent ? "text-teal-800" : "text-slate-700"
                        }`}>
                          {c.trial_id}
                        </span>
                        {isCurrent && (
                          <span className="text-[10px] font-bold px-1.5 py-0.5 rounded bg-teal-200 text-teal-800 uppercase">
                            This trial
                          </span>
                        )}
                        {c.forced && (
                          <span className="text-[10px] font-bold px-1.5 py-0.5 rounded bg-amber-200 text-amber-800 uppercase">
                            Forced
                          </span>
                        )}
                      </div>
                      <span className="text-xs text-slate-400">{c.phase}</span>
                    </div>
                    <p className="text-xs text-slate-500 mb-2 truncate">{c.trial_name}</p>
                    <SimilarityBar score={c.similarity} isCurrentTrial={isCurrent} />
                  </div>
                );
              })}
            </div>
          </StepHeader>

          {/* Step 2 — Hard-Rule Screening */}
          <StepHeader
            number={2}
            title="Rule-Based Screening"
            icon={ShieldCheck}
            status={hardRule.passed === false ? "failed" : "complete"}
          >
            <p className="text-sm text-slate-500 mb-4">
              Deterministic hard-rule filter — {hardRule.met || 0} passed, {hardRule.not_met || 0} failed, {hardRule.cannot_determine || 0} undetermined
            </p>
            <div className="space-y-2">
              {hardDetails.map((r, i) => {
                const colors = {
                  met: { bg: "bg-emerald-50", border: "border-emerald-200", dot: "bg-emerald-500", text: "text-emerald-800" },
                  not_met: { bg: "bg-red-50", border: "border-red-200", dot: "bg-red-500", text: "text-red-800" },
                  cannot_determine: { bg: "bg-amber-50", border: "border-amber-200", dot: "bg-amber-500", text: "text-amber-800" },
                };
                const c = colors[r.verdict] || colors.cannot_determine;
                return (
                  <div key={i} className={`p-3 rounded-lg border ${c.bg} ${c.border}`}>
                    <div className="flex items-start gap-2">
                      <div className={`w-2 h-2 rounded-full mt-1.5 shrink-0 ${c.dot}`} />
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 flex-wrap">
                          <span className={`text-sm font-medium ${c.text}`}>
                            {r.criterion}
                          </span>
                          {r.is_exclusion && (
                            <span className="text-[10px] px-1.5 py-0.5 rounded bg-slate-200 text-slate-600 font-medium uppercase">
                              Exclusion
                            </span>
                          )}
                        </div>
                        <p className="text-xs text-slate-600 mt-1">{r.reason}</p>
                      </div>
                      <VerdictBadge verdict={r.verdict} />
                    </div>
                  </div>
                );
              })}
              {hardDetails.length === 0 && (
                <p className="text-sm text-slate-400 italic">No hard rules evaluated for this trial</p>
              )}
            </div>
          </StepHeader>

          {/* Step 3 — AI Clinical Reasoning */}
          <StepHeader
            number={3}
            title="AI Clinical Reasoning"
            icon={Brain}
            status={result.eligibility === "NOT_ELIGIBLE" ? "failed" : "complete"}
          >
            <p className="text-sm text-slate-500 mb-4">
              Claude evaluated {aiDetails.length} remaining criteria requiring clinical judgment
            </p>
            <div className="space-y-2">
              {aiDetails.map((r, i) => {
                const colors = {
                  met: { bg: "bg-emerald-50", border: "border-emerald-200", dot: "bg-emerald-500", text: "text-emerald-800" },
                  not_met: { bg: "bg-red-50", border: "border-red-200", dot: "bg-red-500", text: "text-red-800" },
                  cannot_determine: { bg: "bg-amber-50", border: "border-amber-200", dot: "bg-amber-500", text: "text-amber-800" },
                };
                const c = colors[r.verdict] || colors.cannot_determine;
                return (
                  <div key={i} className={`p-3 rounded-lg border ${c.bg} ${c.border}`}>
                    <div className="flex items-start gap-2">
                      <div className={`w-2 h-2 rounded-full mt-1.5 shrink-0 ${c.dot}`} />
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 flex-wrap">
                          <span className={`text-sm font-medium ${c.text}`}>
                            {r.criterion}
                          </span>
                          {r.is_exclusion && (
                            <span className="text-[10px] px-1.5 py-0.5 rounded bg-slate-200 text-slate-600 font-medium uppercase">
                              Exclusion
                            </span>
                          )}
                          <span className="text-[10px] px-1.5 py-0.5 rounded bg-purple-100 text-purple-700 font-medium">
                            {r.type === "judgment_call" ? "Judgment" : "Hard Rule"}
                          </span>
                        </div>
                        <p className="text-xs text-slate-600 mt-1">{r.reason}</p>
                      </div>
                      <VerdictBadge verdict={r.verdict} />
                    </div>
                  </div>
                );
              })}
              {aiDetails.length === 0 && (
                <p className="text-sm text-slate-400 italic">No additional criteria evaluated by AI</p>
              )}
            </div>
          </StepHeader>

          {/* Final Verdict */}
          <div className="flex items-center gap-4 mt-2">
            <div className={`w-12 h-12 rounded-2xl flex items-center justify-center border-2 shrink-0 ${
              result.eligibility === "ELIGIBLE"
                ? "border-emerald-300 bg-emerald-50"
                : result.eligibility === "NOT_ELIGIBLE"
                ? "border-red-300 bg-red-50"
                : "border-amber-300 bg-amber-50"
            }`}>
              <span className="text-lg">
                {result.eligibility === "ELIGIBLE" ? "✓" : result.eligibility === "NOT_ELIGIBLE" ? "✗" : "?"}
              </span>
            </div>
            <div className="flex items-center gap-3">
              <div>
                <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
                  Final Verdict
                </span>
                <h3 className="text-base font-bold text-slate-800">Eligibility Determination</h3>
              </div>
              <VerdictBadge verdict={result.eligibility} large />
            </div>
          </div>
        </div>
      ) : (
        /* Fallback: flat criteria table for results without pipeline_steps */
        <div className="bg-white rounded-2xl border border-slate-200 overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="bg-slate-50 text-left text-slate-500">
                  <th className="px-6 py-3 font-medium">Criterion</th>
                  <th className="px-4 py-3 font-medium">Type</th>
                  <th className="px-4 py-3 font-medium">Verdict</th>
                  <th className="px-4 py-3 font-medium">Justification</th>
                </tr>
              </thead>
              <tbody>
                {allCriteria.map((c, i) => (
                  <tr key={i} className="border-t border-slate-100 align-top">
                    <td className="px-6 py-3 max-w-xs">
                      <p className="text-slate-700 leading-snug">{c.criterion}</p>
                    </td>
                    <td className="px-4 py-3 text-slate-500 whitespace-nowrap">
                      {c.source || c.field || "—"}
                    </td>
                    <td className="px-4 py-3">
                      <VerdictBadge verdict={c.verdict} />
                    </td>
                    <td className="px-4 py-3 text-slate-600 max-w-sm">
                      {c.reason || c.data_needed || "—"}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
