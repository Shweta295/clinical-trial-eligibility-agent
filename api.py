import io
import json
import os
import shutil
import tempfile

from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

from db import init_db, seed_trials, SessionLocal, Trial, Result, Patient
from pipeline import run as run_pipeline

app = FastAPI(title="Clinical Trial Eligibility Agent", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup():
    init_db()
    seed_trials()


# ── POST /upload ───────────────────────────────────────────────────────────

@app.post("/upload")
async def upload_patient_note(
    file: UploadFile = File(None),
    text: str = Form(None),
    trial_id: str = Form(None),
):
    if file is None and text is None:
        raise HTTPException(400, "Provide either a file upload or text field")

    if file:
        suffix = os.path.splitext(file.filename)[1] or ".txt"
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
        try:
            shutil.copyfileobj(file.file, tmp)
            tmp.close()
            trial_ids = [trial_id] if trial_id else None
            results = run_pipeline(tmp.name, trial_ids=trial_ids, persist=True)
        finally:
            os.unlink(tmp.name)
    else:
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".txt", mode="w", encoding="utf-8")
        try:
            tmp.write(text)
            tmp.close()
            trial_ids = [trial_id] if trial_id else None
            results = run_pipeline(tmp.name, trial_ids=trial_ids, persist=True)
        finally:
            os.unlink(tmp.name)

    return {"results": results}


# ── GET /trials ────────────────────────────────────────────────────────────

@app.get("/trials")
def get_trials():
    session = SessionLocal()
    try:
        rows = session.query(Trial).all()
        return [
            {
                "id": t.id,
                "name": t.name,
                "phase": t.phase,
                "data": t.data,
            }
            for t in rows
        ]
    finally:
        session.close()


# ── GET /results ───────────────────────────────────────────────────────────

@app.get("/results")
def get_results():
    session = SessionLocal()
    try:
        rows = (
            session.query(Result, Patient)
            .join(Patient, Result.patient_id == Patient.id)
            .order_by(Result.created_at.desc())
            .all()
        )
        return [
            {
                "id": r.id,
                "patient_name": p.patient_name,
                "patient_id": p.patient_id,
                "source_file": p.source_file,
                "trial_id": r.trial_id,
                "eligibility": r.eligibility,
                "summary": r.summary,
                "created_at": r.created_at.isoformat() if r.created_at else None,
            }
            for r, p in rows
        ]
    finally:
        session.close()


# ── GET /results/{id}/pdf ─────────────────────────────────────────────────

@app.get("/results/{result_id}/pdf")
def get_result_pdf(result_id: int):
    session = SessionLocal()
    try:
        r = session.get(Result, result_id)
        if not r:
            raise HTTPException(404, "Result not found")
        p = session.get(Patient, r.patient_id)
        t = session.get(Trial, r.trial_id)
    finally:
        session.close()

    fr = r.full_result or {}
    patient = fr.get("patient", {})
    summary = fr.get("summary", r.summary or {})

    buf = io.BytesIO()
    _build_pdf(buf, r, p, t, patient, summary, fr)
    buf.seek(0)

    patient_name = (p.patient_name if p else "patient").replace(" ", "_")
    filename = f"eligibility_report_{patient_name}_{r.trial_id}.pdf"

    return StreamingResponse(
        buf,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


def _build_pdf(buf, r, p, t, patient, summary, fr):
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.platypus import (
        SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable,
    )

    doc = SimpleDocTemplate(
        buf, pagesize=letter,
        leftMargin=0.75 * inch, rightMargin=0.75 * inch,
        topMargin=0.75 * inch, bottomMargin=0.75 * inch,
    )

    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle("SectionHead", parent=styles["Heading2"], fontSize=12,
                              textColor=colors.HexColor("#0f766e"), spaceAfter=6))
    styles.add(ParagraphStyle("CellText", parent=styles["Normal"], fontSize=8,
                              leading=10, textColor=colors.HexColor("#334155")))
    styles.add(ParagraphStyle("CellBold", parent=styles["CellText"], fontSize=8,
                              textColor=colors.HexColor("#1e293b"),
                              fontName="Helvetica-Bold"))

    TEAL = colors.HexColor("#0d9488")
    GREEN = colors.HexColor("#059669")
    RED = colors.HexColor("#dc2626")
    AMBER = colors.HexColor("#d97706")
    LIGHT_GRAY = colors.HexColor("#f1f5f9")

    verdict_color = {
        "ELIGIBLE": GREEN, "NOT_ELIGIBLE": RED, "PENDING_DATA": AMBER,
    }
    row_verdict_color = {
        "met": colors.HexColor("#ecfdf5"),
        "not_met": colors.HexColor("#fef2f2"),
        "cannot_determine": colors.HexColor("#fffbeb"),
    }

    story = []

    # ── Header ──
    story.append(Paragraph("CLINICAL TRIAL ELIGIBILITY REPORT", styles["Title"]))
    story.append(Spacer(1, 4))
    story.append(HRFlowable(width="100%", thickness=2, color=TEAL))
    story.append(Spacer(1, 12))

    # ── Patient info ──
    story.append(Paragraph("Patient Information", styles["SectionHead"]))
    name = p.patient_name if p else patient.get("name", "Unknown")
    age = patient.get("age", "?")
    sex = patient.get("sex", "?")
    cancer = patient.get("cancer_type", "?")
    hist = patient.get("histology", "?")
    stage = patient.get("stage", "?")
    ecog = patient.get("ECOG", "?")

    info_data = [
        ["Patient:", name, "Age/Sex:", f"{age} / {sex}"],
        ["Diagnosis:", f"{cancer} — {hist}", "Stage:", str(stage)],
        ["ECOG PS:", str(ecog), "Source:", p.source_file if p else "—"],
    ]
    info_table = Table(info_data, colWidths=[1.0 * inch, 2.5 * inch, 0.9 * inch, 2.5 * inch])
    info_table.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTNAME", (2, 0), (2, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("TEXTCOLOR", (0, 0), (-1, -1), colors.HexColor("#334155")),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))
    story.append(info_table)
    story.append(Spacer(1, 12))

    # ── Trial info ──
    story.append(Paragraph("Trial Information", styles["SectionHead"]))
    trial_id = r.trial_id
    trial_name = t.name if t else "—"
    trial_phase = t.phase if t else "—"
    story.append(Paragraph(f"<b>{trial_id}</b> ({trial_phase})", styles["Normal"]))
    story.append(Paragraph(trial_name, styles["Normal"]))
    story.append(Spacer(1, 12))

    # ── Verdict ──
    elig = r.eligibility
    vc = verdict_color.get(elig, TEAL)
    verdict_label = elig.replace("_", " ")
    story.append(Paragraph("Eligibility Determination", styles["SectionHead"]))
    verdict_data = [[
        Paragraph(f'<font color="{vc.hexval()}">{verdict_label}</font>',
                  ParagraphStyle("V", fontSize=16, fontName="Helvetica-Bold", alignment=1)),
    ]]
    vt = Table(verdict_data, colWidths=[7 * inch])
    vt.setStyle(TableStyle([
        ("BOX", (0, 0), (-1, -1), 1.5, vc),
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f8fafc")),
        ("TOPPADDING", (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
    ]))
    story.append(vt)
    story.append(Spacer(1, 4))

    met = summary.get("met", 0)
    not_met = summary.get("not_met", 0)
    undet = summary.get("cannot_determine", 0)
    total = summary.get("total_criteria", met + not_met + undet)
    story.append(Paragraph(
        f"<b>{met}</b> criteria met &nbsp;|&nbsp; <b>{not_met}</b> not met &nbsp;|&nbsp; "
        f"<b>{undet}</b> undetermined &nbsp;(of {total} total)",
        ParagraphStyle("SummaryLine", parent=styles["Normal"], fontSize=9, alignment=1),
    ))
    story.append(Spacer(1, 16))

    # ── Criteria breakdown ──
    all_criteria = []
    for c in (r.disqualifying or []):
        all_criteria.append(("not_met", c.get("criterion", ""), c.get("source", ""),
                             c.get("reason", "")))
    for c in (r.missing_data or []):
        all_criteria.append(("cannot_determine", c.get("criterion", ""),
                             c.get("field", ""), c.get("data_needed", "")))
    for c in (r.criteria_met or []):
        all_criteria.append(("met", c.get("criterion", ""), c.get("source", ""),
                             c.get("reason", "")))

    if all_criteria:
        story.append(Paragraph("Criterion-by-Criterion Breakdown", styles["SectionHead"]))

        header = [
            Paragraph("<b>Criterion</b>", styles["CellBold"]),
            Paragraph("<b>Source</b>", styles["CellBold"]),
            Paragraph("<b>Verdict</b>", styles["CellBold"]),
            Paragraph("<b>Justification</b>", styles["CellBold"]),
        ]
        table_data = [header]

        verdict_labels = {"met": "MET", "not_met": "NOT MET", "cannot_determine": "UNDETERMINED"}
        for verdict, criterion, source, reason in all_criteria:
            vl = verdict_labels.get(verdict, verdict)
            vc2 = {"met": GREEN, "not_met": RED, "cannot_determine": AMBER}.get(verdict, TEAL)
            table_data.append([
                Paragraph(criterion[:120], styles["CellText"]),
                Paragraph(source[:40], styles["CellText"]),
                Paragraph(f'<font color="{vc2.hexval()}"><b>{vl}</b></font>', styles["CellText"]),
                Paragraph(reason[:150], styles["CellText"]),
            ])

        col_widths = [2.4 * inch, 0.9 * inch, 0.9 * inch, 2.8 * inch]
        criteria_table = Table(table_data, colWidths=col_widths, repeatRows=1)

        ts = [
            ("BACKGROUND", (0, 0), (-1, 0), TEAL),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, LIGHT_GRAY]),
        ]
        for i, (verdict, *_) in enumerate(all_criteria, start=1):
            bg = row_verdict_color.get(verdict)
            if bg and verdict != "met":
                ts.append(("BACKGROUND", (0, i), (-1, i), bg))

        criteria_table.setStyle(TableStyle(ts))
        story.append(criteria_table)

    # ── Footer ──
    story.append(Spacer(1, 20))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#cbd5e1")))
    story.append(Spacer(1, 6))
    ts_str = r.created_at.strftime("%Y-%m-%d %H:%M UTC") if r.created_at else "—"
    story.append(Paragraph(
        f"Generated by TrialScreen AI Eligibility Agent &nbsp;|&nbsp; {ts_str}",
        ParagraphStyle("Footer", parent=styles["Normal"], fontSize=7,
                       textColor=colors.HexColor("#94a3b8"), alignment=1),
    ))

    doc.build(story)


# ── GET /results/{id} ─────────────────────────────────────────────────────

@app.get("/results/{result_id}")
def get_result_detail(result_id: int):
    session = SessionLocal()
    try:
        r = session.get(Result, result_id)
        if not r:
            raise HTTPException(404, "Result not found")
        p = session.get(Patient, r.patient_id)
        return {
            "id": r.id,
            "patient_name": p.patient_name if p else None,
            "patient_id": p.patient_id if p else None,
            "source_file": p.source_file if p else None,
            "trial_id": r.trial_id,
            "eligibility": r.eligibility,
            "summary": r.summary,
            "disqualifying": r.disqualifying,
            "missing_data": r.missing_data,
            "criteria_met": r.criteria_met,
            "full_result": r.full_result,
            "created_at": r.created_at.isoformat() if r.created_at else None,
        }
    finally:
        session.close()


# ── GET /dashboard-stats ──────────────────────────────────────────────────

@app.get("/dashboard-stats")
def dashboard_stats():
    session = SessionLocal()
    try:
        results = session.query(Result).all()
        trials = session.query(Trial).all()
        patients = session.query(Patient).all()

        total_patients = len(patients)
        total_screenings = len(results)

        eligible = sum(1 for r in results if r.eligibility == "ELIGIBLE")
        not_eligible = sum(1 for r in results if r.eligibility == "NOT_ELIGIBLE")
        pending = sum(1 for r in results if r.eligibility == "PENDING_DATA")

        by_trial = {}
        for t in trials:
            trial_results = [r for r in results if r.trial_id == t.id]
            total = len(trial_results)
            by_trial[t.id] = {
                "trial_name": t.name,
                "phase": t.phase,
                "total_screenings": total,
                "eligible": sum(1 for r in trial_results if r.eligibility == "ELIGIBLE"),
                "not_eligible": sum(1 for r in trial_results if r.eligibility == "NOT_ELIGIBLE"),
                "pending_data": sum(1 for r in trial_results if r.eligibility == "PENDING_DATA"),
                "eligibility_rate": (
                    round(sum(1 for r in trial_results if r.eligibility == "ELIGIBLE") / total * 100, 1)
                    if total > 0 else 0.0
                ),
            }

        return {
            "total_patients": total_patients,
            "total_screenings": total_screenings,
            "eligible": eligible,
            "not_eligible": not_eligible,
            "pending_data": pending,
            "eligibility_rate": round(eligible / total_screenings * 100, 1) if total_screenings > 0 else 0.0,
            "by_trial": by_trial,
        }
    finally:
        session.close()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True)
