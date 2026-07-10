const BASE = import.meta.env.VITE_API_URL || "/api";

export async function uploadPatientNote(file, text, trialId) {
  const form = new FormData();
  if (file) form.append("file", file);
  if (text) form.append("text", text);
  if (trialId) form.append("trial_id", trialId);

  const res = await fetch(`${BASE}/upload`, { method: "POST", body: form });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function getTrials() {
  const res = await fetch(`${BASE}/trials`);
  return res.json();
}

export async function getResults() {
  const res = await fetch(`${BASE}/results`);
  return res.json();
}

export async function getResultDetail(id) {
  const res = await fetch(`${BASE}/results/${id}`);
  if (!res.ok) throw new Error("Result not found");
  return res.json();
}

export async function getDashboardStats() {
  const res = await fetch(`${BASE}/dashboard-stats`);
  return res.json();
}

export async function downloadResultPdf(id) {
  const res = await fetch(`${BASE}/results/${id}/pdf`);
  if (!res.ok) throw new Error("PDF generation failed");
  const blob = await res.blob();
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `eligibility_report_${id}.pdf`;
  a.click();
  URL.revokeObjectURL(url);
}
