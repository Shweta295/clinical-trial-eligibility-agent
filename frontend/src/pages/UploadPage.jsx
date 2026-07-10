import { useState, useCallback, useRef } from "react";
import { useNavigate } from "react-router-dom";
import { Upload, FileText, Image, FileUp, Loader2, CheckCircle2, Search, ShieldCheck, Brain, PenLine, Sparkles } from "lucide-react";
import { uploadPatientNote, getTrials } from "../api.js";
import VerdictBadge from "../components/VerdictBadge.jsx";

const ACCEPT = ".txt,.png,.jpg,.jpeg,.pdf";

const SAMPLE_TEMPLATES = [
  {
    label: "NSCLC Eligible Patient",
    text: `CLINICAL REFERRAL NOTE
Date: ${new Date().toLocaleDateString("en-US", { month: "2-digit", day: "2-digit", year: "numeric" })}
Patient: Sarah Mitchell
DOB: 05/12/1970 (Age 56)
Sex: Female

DIAGNOSIS: Non-small cell lung cancer (NSCLC), adenocarcinoma.
Stage IIIB (T4N2M0, AJCC 8th edition). Unresectable per tumor board consensus.

MOLECULAR TESTING:
- EGFR: Wild-type
- ALK: Not detected
- ROS1: Not detected
- PD-L1 TPS: 45%

ECOG PS: 1. Ambulatory, able to carry out light work.
Life expectancy > 6 months.

PMH: Hypertension (controlled on amlodipine 5mg), no autoimmune disease, no prior malignancy, no organ transplant, no pneumonitis/ILD history.

PRIOR THERAPY: No prior systemic therapy, chemotherapy, immunotherapy, or radiation for any indication. Not enrolled in any other trial.

INFECTIOUS DISEASE: HIV negative, HBsAg negative, HCV Ab negative. No active infections.

ALLERGIES: NKDA. No polysorbate 80 allergy. No mAb reactions.

MEDICATIONS: Amlodipine 5mg daily. No corticosteroids, no anticoagulants, no immunosuppressants.

LABS (within 14 days):
ANC: 4,200/uL, Platelets: 210,000/uL, Hemoglobin: 12.8 g/dL
Creatinine: 0.88 mg/dL, CrCl: 86 mL/min
AST: 22 U/L, ALT: 26 U/L, Total bilirubin: 0.5 mg/dL
INR: 1.0, aPTT: 27 sec

ECG: NSR, QTcF 408 ms. No heart block.
No cardiovascular events within 6 months. No NYHA heart failure.

TISSUE: FFPE block available from biopsy (within 60 days). Adequate material.
Brain MRI: No intracranial metastases.

REPRODUCTIVE: Postmenopausal. Pregnancy not applicable.
No live vaccines in past 12 months.

ASSESSMENT: Excellent candidate for Protocol ONC-2024-0471.`,
  },
  {
    label: "Heart Failure Patient",
    text: `CLINICAL NOTE
Date: ${new Date().toLocaleDateString("en-US", { month: "2-digit", day: "2-digit", year: "numeric" })}
Patient: James Wilson
DOB: 04/15/1955 (Age 71)
Sex: Male

DIAGNOSIS:
Heart failure with reduced ejection fraction (HFrEF).
NYHA Class III. LVEF 28% on echocardiogram (06/2026).
Ischemic cardiomyopathy, status post CABG (2020).

ECOG: 2 (limited by dyspnea on minimal exertion)

CURRENT MEDICATIONS:
Entresto 97/103mg BID, carvedilol 25mg BID, furosemide 40mg daily,
spironolactone 25mg daily, aspirin 81mg daily, atorvastatin 80mg daily.
No immunosuppressants, no corticosteroids.

LABS (07/05/2026):
BNP: 680 pg/mL, Creatinine: 1.4 mg/dL, eGFR: 48 mL/min,
K+: 4.8 mEq/L, Na+: 138 mEq/L, Hemoglobin: 12.1 g/dL,
AST: 34 U/L, ALT: 29 U/L, Bilirubin: 0.9 mg/dL.

PMH: Coronary artery disease s/p CABG, hypertension, hyperlipidemia,
type 2 diabetes (A1c 7.1 on metformin). No cancer. No autoimmune disease.
No organ transplant.

INFECTIOUS: HIV negative. No active infections.
ALLERGIES: NKDA.

Interested in clinical trial options for advanced heart failure.`,
  },
  {
    label: "Diabetes Patient",
    text: `REFERRAL NOTE
Date: ${new Date().toLocaleDateString("en-US", { month: "2-digit", day: "2-digit", year: "numeric" })}
Patient: Maria Garcia
DOB: 08/22/1968 (Age 57)
Sex: Female

DIAGNOSIS:
Type 2 Diabetes Mellitus, poorly controlled.
A1c: 9.2% (target <7%). BMI: 34.2 kg/m2.
Duration: 12 years.

CURRENT THERAPY:
Metformin 2000mg/day + glimepiride 4mg/day + empagliflozin 25mg/day.
Still not at goal despite triple therapy.

COMPLICATIONS:
- Mild nonproliferative diabetic retinopathy (bilateral)
- Microalbuminuria (ACR 45 mg/g)
- Peripheral neuropathy (feet, mild, sensory)

LABS (07/01/2026):
Fasting glucose: 186 mg/dL, A1c: 9.2%, Creatinine: 1.0 mg/dL,
eGFR: 72 mL/min, ALT: 42 U/L, AST: 38 U/L,
Total cholesterol: 218 mg/dL, LDL: 128 mg/dL, Triglycerides: 245 mg/dL,
Hemoglobin: 13.4 g/dL, Platelets: 220,000/uL.

PMH: Hypertension (on lisinopril 20mg), hyperlipidemia (atorvastatin 20mg).
No cardiovascular events. No cancer history. No autoimmune disease.
ECOG: 0. No organ transplant. HIV negative.

ALLERGIES: Sulfonamides (rash). No other drug allergies.

Interested in GLP-1 receptor agonist or novel diabetes clinical trial.`,
  },
  {
    label: "Minimal / Incomplete Note",
    text: `QUICK REFERRAL

Patient: David Park, 58M
Dx: Lung cancer, non-small cell, probably stage III.
Biopsy confirmed last month. No chemo yet.
Would like to try a clinical trial. Please evaluate.

— Dr. Thompson`,
  },
];

export default function UploadPage() {
  const [mode, setMode] = useState("file");
  const [file, setFile] = useState(null);
  const [text, setText] = useState("");
  const [dragOver, setDragOver] = useState(false);
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState(null);
  const [error, setError] = useState(null);
  const inputRef = useRef();
  const navigate = useNavigate();

  const onDrop = useCallback((e) => {
    e.preventDefault();
    setDragOver(false);
    const f = e.dataTransfer.files[0];
    if (f) setFile(f);
  }, []);

  const fileIcon = (name) => {
    if (!name) return FileUp;
    const ext = name.split(".").pop().toLowerCase();
    if (["png", "jpg", "jpeg"].includes(ext)) return Image;
    return FileText;
  };

  const canSubmit = mode === "file" ? !!file : text.trim().length > 20;

  const handleSubmit = async () => {
    if (!canSubmit) return;
    setLoading(true);
    setError(null);
    setResults(null);
    try {
      const data = mode === "file"
        ? await uploadPatientNote(file, null, null)
        : await uploadPatientNote(null, text, null);
      setResults(data.results);
    } catch (err) {
      setError(err.message || "Upload failed");
    } finally {
      setLoading(false);
    }
  };

  const Icon = fileIcon(file?.name);

  return (
    <div className="p-8 max-w-4xl mx-auto">
      <h2 className="text-2xl font-bold text-slate-800 mb-2">Upload Patient Note</h2>
      <p className="text-slate-500 mb-6">
        Upload a clinical note or type one directly to evaluate trial eligibility.
      </p>

      {/* Mode Tabs */}
      <div className="flex gap-1 bg-slate-100 p-1 rounded-xl mb-6 w-fit">
        <button
          onClick={() => setMode("file")}
          className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
            mode === "file"
              ? "bg-white text-teal-700 shadow-sm"
              : "text-slate-500 hover:text-slate-700"
          }`}
        >
          <Upload className="w-4 h-4" /> Upload File
        </button>
        <button
          onClick={() => setMode("text")}
          className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
            mode === "text"
              ? "bg-white text-teal-700 shadow-sm"
              : "text-slate-500 hover:text-slate-700"
          }`}
        >
          <PenLine className="w-4 h-4" /> Type / Paste
        </button>
      </div>

      {mode === "file" ? (
        /* File Upload */
        <div
          onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
          onDragLeave={() => setDragOver(false)}
          onDrop={onDrop}
          onClick={() => inputRef.current?.click()}
          className={`border-2 border-dashed rounded-2xl p-12 text-center cursor-pointer transition-colors ${
            dragOver
              ? "border-teal-500 bg-teal-50"
              : file
              ? "border-teal-300 bg-teal-50/50"
              : "border-slate-300 bg-white hover:border-teal-400 hover:bg-slate-50"
          }`}
        >
          <input
            ref={inputRef}
            type="file"
            accept={ACCEPT}
            className="hidden"
            onChange={(e) => setFile(e.target.files[0] || null)}
          />
          {file ? (
            <div className="flex flex-col items-center gap-3">
              <Icon className="w-12 h-12 text-teal-600" />
              <p className="text-lg font-medium text-teal-800">{file.name}</p>
              <p className="text-sm text-slate-500">
                {(file.size / 1024).toFixed(1)} KB — click or drop to replace
              </p>
            </div>
          ) : (
            <div className="flex flex-col items-center gap-3">
              <Upload className="w-12 h-12 text-slate-400" />
              <p className="text-lg font-medium text-slate-600">
                Drag & drop a patient note here
              </p>
              <p className="text-sm text-slate-400">or click to browse — .txt, .png, .jpg, .pdf</p>
            </div>
          )}
        </div>
      ) : (
        /* Text Input */
        <div>
          {/* Sample Templates */}
          <div className="mb-3">
            <div className="flex items-center gap-2 mb-2">
              <Sparkles className="w-4 h-4 text-teal-600" />
              <span className="text-sm font-medium text-slate-600">Load a sample template:</span>
            </div>
            <div className="flex flex-wrap gap-2">
              {SAMPLE_TEMPLATES.map((t, i) => (
                <button
                  key={i}
                  onClick={() => setText(t.text)}
                  className="px-3 py-1.5 text-xs font-medium rounded-lg border border-slate-200
                    bg-white text-slate-600 hover:border-teal-300 hover:text-teal-700
                    hover:bg-teal-50 transition-colors"
                >
                  {t.label}
                </button>
              ))}
            </div>
          </div>

          <textarea
            value={text}
            onChange={(e) => setText(e.target.value)}
            placeholder={"Paste or type a clinical note here...\n\nExample:\nCLINICAL NOTE\nPatient: John Smith, 58M\nDiagnosis: Non-small cell lung cancer, Stage IIIB\nECOG: 1\n..."}
            className="w-full h-80 p-4 rounded-2xl border-2 border-slate-200 bg-white text-sm
              text-slate-700 placeholder-slate-400 resize-y
              focus:outline-none focus:border-teal-400 focus:ring-2 focus:ring-teal-100
              transition-colors font-mono leading-relaxed"
          />
          <div className="flex items-center justify-between mt-2">
            <p className="text-xs text-slate-400">
              {text.length > 0 ? `${text.length} characters` : "Minimum 20 characters required"}
            </p>
            {text.length > 0 && (
              <button
                onClick={() => setText("")}
                className="text-xs text-slate-400 hover:text-red-500 transition-colors"
              >
                Clear
              </button>
            )}
          </div>
        </div>
      )}

      {/* Submit */}
      <button
        onClick={handleSubmit}
        disabled={!canSubmit || loading}
        className="mt-6 w-full py-3.5 rounded-xl font-semibold text-white transition-colors flex items-center justify-center gap-2
          bg-teal-600 hover:bg-teal-700 disabled:bg-slate-300 disabled:cursor-not-allowed"
      >
        {loading ? (
          <>
            <Loader2 className="w-5 h-5 animate-spin" />
            Analyzing eligibility...
          </>
        ) : (
          <>
            <CheckCircle2 className="w-5 h-5" />
            Analyze Eligibility
          </>
        )}
      </button>

      {error && (
        <div className="mt-4 p-4 bg-red-50 border border-red-200 rounded-xl text-red-700 text-sm">
          {error}
        </div>
      )}

      {/* Results */}
      {results && results.map((r, i) => {
        const steps = r.pipeline_steps || {};
        const semantic = steps.semantic_search || [];
        const hardRule = steps.hard_rule_screening || {};
        const hardDetails = hardRule.details || [];
        const aiDetails = (steps.ai_reasoning || {}).details || [];
        const hasPipeline = semantic.length > 0 || hardDetails.length > 0;

        return (
          <div key={i} className="mt-8 bg-white rounded-2xl border border-slate-200 overflow-hidden">
            <div className="p-6 border-b border-slate-100 flex items-center justify-between">
              <div>
                <h3 className="text-lg font-bold text-slate-800">
                  {r.patient?.name || r.patient?.id}
                </h3>
                <p className="text-sm text-slate-500">
                  {r.patient?.age}yo {r.patient?.sex} — {r.patient?.cancer_type}, Stage {r.patient?.stage}
                  {r.patient?.ECOG != null && `, ECOG ${r.patient.ECOG}`}
                </p>
                <p className="text-sm text-slate-400 mt-1">
                  Trial: {r.trial?.id} ({r.trial?.phase})
                </p>
              </div>
              <VerdictBadge verdict={r.eligibility} large />
            </div>

            <div className="p-6">
              <div className="grid grid-cols-3 gap-4 mb-6">
                <div className="text-center p-3 bg-emerald-50 rounded-xl">
                  <p className="text-2xl font-bold text-emerald-700">{r.summary?.met}</p>
                  <p className="text-xs text-emerald-600">Criteria Met</p>
                </div>
                <div className="text-center p-3 bg-red-50 rounded-xl">
                  <p className="text-2xl font-bold text-red-700">{r.summary?.not_met}</p>
                  <p className="text-xs text-red-600">Not Met</p>
                </div>
                <div className="text-center p-3 bg-amber-50 rounded-xl">
                  <p className="text-2xl font-bold text-amber-700">{r.summary?.cannot_determine}</p>
                  <p className="text-xs text-amber-600">Undetermined</p>
                </div>
              </div>

              {hasPipeline && (
                <div className="space-y-5">
                  {semantic.length > 0 && (
                    <div>
                      <div className="flex items-center gap-2 mb-3">
                        <Search className="w-4 h-4 text-teal-600" />
                        <h4 className="text-sm font-semibold text-slate-700">Step 1 — Semantic Trial Search</h4>
                      </div>
                      <div className="space-y-2">
                        {semantic.map((c) => {
                          const isCurrent = c.trial_id === r.trial?.id;
                          const pct = Math.round(c.similarity * 100);
                          return (
                            <div key={c.trial_id} className={`flex items-center gap-3 p-2 rounded-lg text-sm ${
                              isCurrent ? "bg-teal-50 border border-teal-200" : "bg-slate-50"
                            }`}>
                              <span className={`font-mono font-semibold w-20 shrink-0 ${
                                isCurrent ? "text-teal-700" : "text-slate-600"
                              }`}>{c.trial_id.length > 14 ? c.trial_id.slice(0, 14) + "…" : c.trial_id}</span>
                              <div className="flex-1 h-2.5 bg-slate-200 rounded-full overflow-hidden">
                                <div className={`h-full rounded-full ${isCurrent ? "bg-teal-500" : "bg-slate-400"}`}
                                     style={{ width: `${pct}%` }} />
                              </div>
                              <span className={`font-mono text-xs w-10 text-right ${
                                isCurrent ? "text-teal-700 font-bold" : "text-slate-500"
                              }`}>{pct}%</span>
                              {isCurrent && <span className="text-[9px] font-bold px-1 py-0.5 rounded bg-teal-200 text-teal-800">THIS</span>}
                            </div>
                          );
                        })}
                      </div>
                    </div>
                  )}

                  {hardDetails.length > 0 && (
                    <div>
                      <div className="flex items-center gap-2 mb-3">
                        <ShieldCheck className={`w-4 h-4 ${hardRule.passed === false ? "text-red-600" : "text-teal-600"}`} />
                        <h4 className="text-sm font-semibold text-slate-700">
                          Step 2 — Rule-Based Screening
                          <span className={`ml-2 text-xs font-medium px-2 py-0.5 rounded-full ${
                            hardRule.passed === false
                              ? "bg-red-100 text-red-700"
                              : "bg-emerald-100 text-emerald-700"
                          }`}>
                            {hardRule.met || 0} pass / {hardRule.not_met || 0} fail
                          </span>
                        </h4>
                      </div>
                      <div className="space-y-1.5">
                        {hardDetails.slice(0, 6).map((d, j) => (
                          <div key={j} className={`flex items-center gap-2 p-2 rounded-lg text-xs ${
                            d.verdict === "met" ? "bg-emerald-50" : d.verdict === "not_met" ? "bg-red-50" : "bg-amber-50"
                          }`}>
                            <div className={`w-1.5 h-1.5 rounded-full shrink-0 ${
                              d.verdict === "met" ? "bg-emerald-500" : d.verdict === "not_met" ? "bg-red-500" : "bg-amber-500"
                            }`} />
                            <span className="flex-1 text-slate-700 truncate">{d.criterion}</span>
                            <VerdictBadge verdict={d.verdict} />
                          </div>
                        ))}
                        {hardDetails.length > 6 && (
                          <p className="text-xs text-slate-400 pl-4">+ {hardDetails.length - 6} more rules</p>
                        )}
                      </div>
                    </div>
                  )}

                  {aiDetails.length > 0 && (
                    <div>
                      <div className="flex items-center gap-2 mb-3">
                        <Brain className="w-4 h-4 text-purple-600" />
                        <h4 className="text-sm font-semibold text-slate-700">
                          Step 3 — AI Clinical Reasoning
                          <span className="ml-2 text-xs font-medium px-2 py-0.5 rounded-full bg-purple-100 text-purple-700">
                            {aiDetails.length} criteria
                          </span>
                        </h4>
                      </div>
                      <div className="space-y-1.5">
                        {aiDetails.slice(0, 5).map((d, j) => (
                          <div key={j} className={`flex items-center gap-2 p-2 rounded-lg text-xs ${
                            d.verdict === "met" ? "bg-emerald-50" : d.verdict === "not_met" ? "bg-red-50" : "bg-amber-50"
                          }`}>
                            <div className={`w-1.5 h-1.5 rounded-full shrink-0 ${
                              d.verdict === "met" ? "bg-emerald-500" : d.verdict === "not_met" ? "bg-red-500" : "bg-amber-500"
                            }`} />
                            <span className="flex-1 text-slate-700 truncate">{d.criterion}</span>
                            <VerdictBadge verdict={d.verdict} />
                          </div>
                        ))}
                        {aiDetails.length > 5 && (
                          <p className="text-xs text-slate-400 pl-4">+ {aiDetails.length - 5} more criteria</p>
                        )}
                      </div>
                    </div>
                  )}
                </div>
              )}

              {!hasPipeline && (
                <>
                  {r.disqualifying?.length > 0 && (
                    <div className="mb-4">
                      <h4 className="text-sm font-semibold text-red-700 mb-2">Disqualifying</h4>
                      {r.disqualifying.map((d, j) => (
                        <div key={j} className="p-3 bg-red-50 rounded-lg mb-2 text-sm">
                          <p className="font-medium text-red-800">{d.criterion}</p>
                          <p className="text-red-600 mt-1">{d.reason}</p>
                        </div>
                      ))}
                    </div>
                  )}

                  {r.missing_data?.length > 0 && (
                    <div>
                      <h4 className="text-sm font-semibold text-amber-700 mb-2">Missing Data</h4>
                      {r.missing_data.slice(0, 5).map((m, j) => (
                        <div key={j} className="p-3 bg-amber-50 rounded-lg mb-2 text-sm">
                          <span className="font-medium text-amber-800">[{m.field}]</span>{" "}
                          <span className="text-amber-700">{m.data_needed}</span>
                        </div>
                      ))}
                      {r.missing_data.length > 5 && (
                        <p className="text-xs text-slate-400 mt-1">
                          + {r.missing_data.length - 5} more missing fields
                        </p>
                      )}
                    </div>
                  )}
                </>
              )}
            </div>
          </div>
        );
      })}
    </div>
  );
}
