import anthropic
import json
import os

import voyageai
from dotenv import load_dotenv

from config import VOYAGE_MODEL
from utils import ingest_document

load_dotenv()

client = anthropic.Anthropic()
vo = voyageai.Client(api_key=os.environ.get("VOYAGE_API_KEY", ""))

# ═══════════════════════════════════════════════════════════════════════════
# Stage 1 — Entity Extraction via Claude Tool Use
# ═══════════════════════════════════════════════════════════════════════════

EXTRACT_TOOL = {
    "name": "save_patient_profile",
    "description": "Save the structured patient profile extracted from a clinical note.",
    "input_schema": {
        "type": "object",
        "properties": {
            "patient_id": {"type": "string"},
            "patient_name": {"type": "string"},
            "age": {"type": "integer"},
            "sex": {"type": "string", "enum": ["male", "female"]},
            "cancer_type": {"type": "string"},
            "histology": {"type": "string"},
            "stage": {"type": "string"},
            "is_metastatic": {"type": ["boolean", "null"]},
            "ECOG": {"type": ["integer", "null"]},
            "EGFR_status": {"type": ["string", "null"], "enum": ["wild_type", "sensitizing_mutation", "not_tested", None]},
            "ALK_status": {"type": ["string", "null"], "enum": ["positive", "negative", "not_tested", None]},
            "ROS1_status": {"type": ["string", "null"], "enum": ["positive", "negative", "not_tested", None]},
            "HER2_status": {"type": ["string", "null"], "enum": ["positive", "negative", "equivocal", "not_tested", None]},
            "PD_L1_TPS": {"type": ["number", "null"]},
            "ANC": {"type": ["number", "null"]},
            "platelets": {"type": ["number", "null"]},
            "hemoglobin": {"type": ["number", "null"]},
            "serum_creatinine": {"type": ["number", "null"]},
            "creatinine_clearance": {"type": ["number", "null"]},
            "AST": {"type": ["number", "null"]},
            "ALT": {"type": ["number", "null"]},
            "total_bilirubin": {"type": ["number", "null"]},
            "INR": {"type": ["number", "null"]},
            "aPTT": {"type": ["number", "null"]},
            "LVEF_percent": {"type": ["number", "null"]},
            "QTcF_ms": {"type": ["number", "null"]},
            "prior_systemic_therapies": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "drug_name": {"type": "string"},
                        "drug_class": {"type": "string"},
                        "setting": {"type": "string"},
                        "end_date": {"type": ["string", "null"]}
                    },
                    "required": ["drug_name", "drug_class"],
                    "additionalProperties": False
                }
            },
            "prior_radiation": {"type": ["boolean", "null"]},
            "prior_radiation_details": {"type": ["string", "null"], "description": "Site, date, and current status of prior radiation if any"},
            "has_measurable_disease": {"type": ["boolean", "null"]},
            "brain_mets_status": {"type": ["string", "null"], "enum": ["none", "active", "treated_stable", None]},
            "brain_mets_treatment_date": {"type": ["string", "null"]},
            "brain_mets_details": {"type": ["string", "null"], "description": "Treatment type, stability, steroid status"},
            "active_autoimmune_disease": {"type": ["boolean", "null"]},
            "autoimmune_details": {"type": ["string", "null"]},
            "active_infection": {"type": ["boolean", "null"]},
            "HIV_status": {"type": ["string", "null"], "enum": ["positive", "negative", "unknown", None]},
            "hepatitis_B_status": {"type": ["string", "null"], "enum": ["positive", "negative", "prior_exposure_controlled", "unknown", None]},
            "hepatitis_C_status": {"type": ["string", "null"], "enum": ["positive", "negative", "unknown", None]},
            "other_active_malignancy": {"type": ["boolean", "null"]},
            "prior_organ_transplant": {"type": ["boolean", "null"]},
            "pneumonitis_ILD_history": {"type": ["boolean", "null"]},
            "on_systemic_corticosteroids": {"type": ["boolean", "null"]},
            "corticosteroid_dose_mg_day": {"type": ["number", "null"]},
            "on_anticoagulation": {"type": ["boolean", "null"]},
            "allergy_polysorbate_80": {"type": ["boolean", "null"]},
            "severe_mab_reaction": {"type": ["boolean", "null"]},
            "concurrent_trial": {"type": ["boolean", "null"]},
            "cardiovascular_events_6mo": {"type": ["boolean", "null"]},
            "NYHA_class": {"type": ["string", "null"]},
            "heart_block_degree": {"type": ["string", "null"]},
            "pacemaker": {"type": ["boolean", "null"]},
            "cumulative_anthracycline_dose": {"type": ["number", "null"]},
            "pregnancy_status": {"type": ["string", "null"], "enum": ["not_applicable", "negative", "positive", "not_tested", None]},
            "contraception_agreed": {"type": ["boolean", "null"]},
            "life_expectancy_stated": {"type": ["boolean", "null"], "description": "Whether the note explicitly states life expectancy > 3 months"},
            "tissue_available": {"type": ["boolean", "null"]},
            "tissue_date": {"type": ["string", "null"]},
            "last_live_vaccine_date": {"type": ["string", "null"]},
            "lab_collection_date": {"type": ["string", "null"]},
            "notes": {"type": "string", "description": "Clinically relevant details, borderline findings, flags"}
        },
        "required": ["patient_id", "age", "sex", "cancer_type", "histology", "stage"],
        "additionalProperties": False
    }
}


def extract_patient_profile(clinical_text: str) -> dict:
    response = client.messages.create(
        model="claude-sonnet-5",
        max_tokens=4096,
        thinking={"type": "adaptive"},
        system=(
            "You are a clinical data extraction specialist. Extract every available data point "
            "from the clinical note into a structured patient profile by calling save_patient_profile. "
            "Rules:\n"
            "- For fields not mentioned or not determinable, pass null.\n"
            "- Do NOT guess or infer. Only use explicitly stated data.\n"
            "- For prior_systemic_therapies, list every anticancer drug (chemo, immunotherapy, targeted, etc.).\n"
            "- For brain_mets_status: 'treated_stable' means treated with post-treatment imaging showing stability.\n"
            "- For hepatitis_B_status: use 'prior_exposure_controlled' if HBsAg negative but anti-HBc positive with undetectable DNA.\n"
            "- For life_expectancy_stated: true only if the note explicitly says life expectancy > 3 months.\n"
            "- Capture borderline/nuanced details in the notes field.\n"
            "- Be precise with dates, values, and drug names."
        ),
        tools=[EXTRACT_TOOL],
        tool_choice={"type": "tool", "name": "save_patient_profile"},
        messages=[{"role": "user", "content": f"Extract the patient profile:\n\n{clinical_text}"}],
    )

    for block in response.content:
        if block.type == "tool_use" and block.name == "save_patient_profile":
            return block.input
    raise RuntimeError("Extraction tool was not called")


# ═══════════════════════════════════════════════════════════════════════════
# Stage 2 — Hard-Rule Filter (Pure Python)
# ═══════════════════════════════════════════════════════════════════════════

def _val(profile, key):
    v = profile.get(key)
    return v if v is not None else None


def check_hard_rules(profile: dict, trial: dict) -> list:
    results = []
    all_criteria = (
        [(c, False) for c in trial["inclusion_criteria"]]
        + [(c, True) for c in trial["exclusion_criteria"]]
    )

    for criterion, is_exclusion in all_criteria:
        if criterion["type"] != "hard_rule":
            continue

        field = criterion["field_required"]
        text = criterion["criterion_text"].lower()
        v = None  # verdict
        r = None  # reason

        # ── Demographics ──
        if field == "age":
            age = _val(profile, "age")
            if age is not None:
                v, r = ("met", f"Patient age is {age}") if age >= 18 else ("not_met", f"Age {age} < 18")
            else:
                v, r = "cannot_determine", "Age not documented"

        elif field in ("ECOG_performance_status",) and ("0 or 1" in text or "0-1" in text):
            ecog = _val(profile, "ECOG")
            if ecog is not None:
                v, r = ("met", f"ECOG PS {ecog}") if ecog <= 1 else ("not_met", f"ECOG PS {ecog}, requires 0-1")
            else:
                v, r = "cannot_determine", "ECOG not documented"

        # ── Diagnosis / Stage ──
        elif field in ("diagnosis_stage", "diagnosis", "disease_stage", "histology"):
            cancer = (profile.get("cancer_type") or "").lower()
            stage = (profile.get("stage") or "").upper()

            if "small-cell" in text and "mixed" in text:
                hist = (profile.get("histology") or "").lower()
                hist_words = hist.split()
                has_small_cell = False
                for j, w in enumerate(hist_words):
                    if w == "small-cell" or (w == "small" and j + 1 < len(hist_words) and hist_words[j+1] == "cell"):
                        context_start = max(0, j - 3)
                        context = " ".join(hist_words[context_start:j])
                        if "no" not in context and "non" not in context and "without" not in context:
                            has_small_cell = True
                if not has_small_cell:
                    v, r = "met", f"Histology: {hist}, no small-cell component"
                else:
                    v, r = "not_met", f"Small-cell component: {hist}"

            elif "nsclc" in text or "non-small cell" in text or "non-small-cell" in text:
                if "nsclc" in cancer or "non-small cell" in cancer or "non-small-cell" in cancer:
                    if "stage iii" in text:
                        import re as _re
                        if _re.search(r"III", stage):
                            v, r = "met", f"{cancer}, Stage {stage}"
                        else:
                            v, r = "not_met", f"Stage {stage}, requires Stage III"
                    else:
                        v, r = "met", f"Cancer type: {cancer}"
                else:
                    v, r = "not_met", f"Cancer type: {cancer}, requires NSCLC"

            elif "her2" in text and ("breast" in text or "locally advanced" in text or "metastatic" in text):
                her2 = _val(profile, "HER2_status")
                if "breast" in cancer:
                    if her2 == "positive":
                        v, r = "met", "HER2+ breast cancer confirmed"
                    elif her2 in ("negative", "equivocal"):
                        v, r = "not_met", f"HER2 status: {her2}"
                    else:
                        v, r = "cannot_determine", "HER2 status not tested/documented"
                else:
                    v, r = "not_met", f"Cancer type: {cancer}, requires breast cancer"

        # ── Lab Values ──
        elif field == "lab_ANC":
            val = _val(profile, "ANC")
            if val is not None:
                v, r = ("met", f"ANC {val}/uL") if val >= 1500 else ("not_met", f"ANC {val}/uL < 1500")
            else:
                v, r = "cannot_determine", "ANC not documented"

        elif field == "lab_platelets":
            val = _val(profile, "platelets")
            if val is not None:
                v, r = ("met", f"Platelets {val}/uL") if val >= 100000 else ("not_met", f"Platelets {val}/uL < 100,000")
            else:
                v, r = "cannot_determine", "Platelets not documented"

        elif field == "lab_hemoglobin":
            val = _val(profile, "hemoglobin")
            if val is not None:
                v, r = ("met", f"Hgb {val} g/dL") if val >= 9.0 else ("not_met", f"Hgb {val} g/dL < 9.0")
            else:
                v, r = "cannot_determine", "Hemoglobin not documented"

        elif field in ("lab_creatinine", "lab_creatinine_or_CrCl"):
            crcl = _val(profile, "creatinine_clearance")
            cr = _val(profile, "serum_creatinine")
            if crcl is not None:
                if crcl >= 50:
                    v, r = "met", f"CrCl {crcl} mL/min (>=50)"
                else:
                    v, r = "not_met", f"CrCl {crcl} mL/min (<50)"
            elif cr is not None:
                v, r = "met", f"Creatinine {cr} mg/dL (CrCl not calculated, needs ULN check)"
            else:
                v, r = "cannot_determine", "Creatinine/CrCl not documented"

        elif field == "lab_AST_ALT":
            ast = _val(profile, "AST")
            alt = _val(profile, "ALT")
            if ast is not None and alt is not None:
                v, r = "met", f"AST {ast}, ALT {alt} U/L"
            else:
                v, r = "cannot_determine", "AST/ALT not documented"

        elif field == "lab_bilirubin":
            val = _val(profile, "total_bilirubin")
            if val is not None:
                v, r = "met", f"Bilirubin {val} mg/dL"
            else:
                v, r = "cannot_determine", "Bilirubin not documented"

        elif field == "lab_coagulation":
            inr = _val(profile, "INR")
            if inr is not None:
                v, r = "met", f"INR {inr}, aPTT {_val(profile, 'aPTT')}"
            else:
                v, r = "cannot_determine", "Coagulation labs not documented"

        # ── Mutations ──
        elif field == "EGFR_ALK_mutation_status":
            egfr = _val(profile, "EGFR_status")
            alk = _val(profile, "ALK_status")
            if egfr and alk:
                if egfr == "wild_type" and alk == "negative":
                    v, r = "met", "EGFR wild-type, ALK negative"
                elif egfr == "sensitizing_mutation" or alk == "positive":
                    v, r = "not_met", f"EGFR: {egfr}, ALK: {alk}"
                else:
                    v, r = "cannot_determine", f"EGFR: {egfr}, ALK: {alk}"
            else:
                v, r = "cannot_determine", f"EGFR: {egfr or 'untested'}, ALK: {alk or 'untested'}"

        elif field == "ROS1_status":
            ros1 = _val(profile, "ROS1_status")
            if ros1 == "negative":
                v, r = "met", "ROS1 negative"
            elif ros1 == "positive":
                v, r = "not_met", "ROS1 positive"
            else:
                v, r = "cannot_determine", "ROS1 not tested"

        elif field == "HER2_status" and is_exclusion:
            her2 = _val(profile, "HER2_status")
            if her2 == "positive":
                v, r = "met", "HER2 positive (not low/negative)"
            elif her2 in ("negative", "equivocal"):
                v, r = "not_met", f"HER2: {her2}"
            elif her2 == "not_tested":
                v, r = "cannot_determine", "HER2 not tested"
            else:
                v, r = "cannot_determine", "HER2 not documented"

        # ── Cardiac ──
        elif field in ("QTc_interval", "QTcF"):
            qtc = _val(profile, "QTcF_ms")
            sex = profile.get("sex", "")
            if qtc is not None:
                limit = 470 if sex == "female" else 450
                v, r = ("met", f"QTcF {qtc} ms (limit {limit})") if qtc <= limit else ("not_met", f"QTcF {qtc} ms > {limit}")
            else:
                v, r = "cannot_determine", "QTcF not documented"

        elif field == "cardiovascular_history":
            cv = _val(profile, "cardiovascular_events_6mo")
            if cv is not None:
                v, r = ("met", "No CV events within 6 months") if not cv else ("not_met", "CV event within 6 months")
            else:
                v, r = "cannot_determine", "CV history not documented"

        elif field == "cardiac_conduction_status":
            hb = _val(profile, "heart_block_degree")
            pm = _val(profile, "pacemaker")
            if hb in (None, "none", "first_degree"):
                v, r = "met", "No significant heart block"
            elif hb in ("second_degree", "third_degree") and pm:
                v, r = "met", f"{hb} block with pacemaker"
            elif hb in ("second_degree", "third_degree"):
                v, r = "not_met", f"{hb} block, no pacemaker"
            else:
                v, r = "cannot_determine", "Conduction status not documented"

        # ── Prior Therapy ──
        elif field == "prior_therapy_history" and ("no prior systemic" in text):
            therapies = profile.get("prior_systemic_therapies") or []
            if len(therapies) == 0:
                v, r = "met", "No prior systemic therapies"
            else:
                names = [t["drug_name"] for t in therapies]
                v, r = "not_met", f"Prior therapy: {', '.join(names)}"

        # ── Simple boolean exclusions ──
        elif field == "transplant_history":
            tx = _val(profile, "prior_organ_transplant")
            if tx is not None:
                v, r = ("met", "No transplant history") if not tx else ("not_met", "Prior transplant")
            else:
                v, r = "cannot_determine", "Transplant history not documented"

        elif field in ("hypersensitivity_history", "allergy_history"):
            ps80 = _val(profile, "allergy_polysorbate_80")
            mab = _val(profile, "severe_mab_reaction")
            if ps80 is False and mab is False:
                v, r = "met", "No polysorbate 80 allergy, no severe mAb reactions"
            elif ps80 is True or mab is True:
                v, r = "not_met", f"PS80 allergy: {ps80}, severe mAb reaction: {mab}"
            else:
                v, r = "cannot_determine", "Allergy history incomplete"

        elif field in ("concurrent_trial_enrollment", "concurrent_trial_participation"):
            ct = _val(profile, "concurrent_trial")
            if ct is not None:
                v, r = ("met", "No concurrent trial") if not ct else ("not_met", "Concurrent trial enrollment")
            else:
                v, r = "cannot_determine", "Concurrent trial status unknown"

        elif field in ("pregnancy_test", "pregnancy_status"):
            preg = _val(profile, "pregnancy_status")
            sex = profile.get("sex")
            if sex == "male":
                v, r = "met", "Male — not applicable"
            elif preg in ("negative", "not_applicable"):
                v, r = "met", f"Pregnancy: {preg}"
            elif preg == "positive":
                v, r = "not_met", "Pregnant"
            else:
                v, r = "cannot_determine", "Pregnancy status not documented"

        if v is None:
            continue

        results.append({
            "criterion": criterion["criterion_text"],
            "field": field,
            "type": "hard_rule",
            "is_exclusion": is_exclusion,
            "verdict": v,
            "reason": r,
            "source": "rule_engine"
        })

    return results


# ═══════════════════════════════════════════════════════════════════════════
# Stage 3 & 4 — LLM Reasoning + Missing-Info Detection
# ═══════════════════════════════════════════════════════════════════════════

def evaluate_with_llm(profile: dict, trial: dict, already_checked: set) -> list:
    unchecked = []
    for c in trial["inclusion_criteria"] + trial["exclusion_criteria"]:
        is_excl = c in trial["exclusion_criteria"]
        key = (c["criterion_text"], c["field_required"])
        if c["type"] == "judgment_call" or key not in already_checked:
            unchecked.append({**c, "is_exclusion": is_excl})

    if not unchecked:
        return []

    criteria_list = "\n".join(
        f"{i+1}. [{'EXCLUSION' if c['is_exclusion'] else 'INCLUSION'}] (field: {c['field_required']}) {c['criterion_text']}"
        for i, c in enumerate(unchecked)
    )

    response = client.messages.create(
        model="claude-sonnet-5",
        max_tokens=8000,
        thinking={"type": "adaptive"},
        system=(
            "You are a clinical trial eligibility reviewer. Evaluate each criterion against the patient profile.\n\n"
            "Return a JSON array. Each element:\n"
            '{"n": <criterion_number>, "verdict": "met"|"not_met"|"cannot_determine", "reason": "<one sentence>"}\n\n'
            "Rules:\n"
            "- INCLUSION 'met' = patient satisfies it. 'not_met' = patient fails.\n"
            "- EXCLUSION 'met' = patient does NOT have the excluded condition (passes).\n"
            "  EXCLUSION 'not_met' = patient HAS the excluded condition (disqualified).\n"
            "- 'cannot_determine' = data missing. State exactly what's needed.\n"
            "- Cite specific values, dates, drug names from the profile.\n"
            "- If a field is null, verdict MUST be 'cannot_determine' unless the criterion is inapplicable.\n"
            "- For borderline cases, explain the specific concern.\n"
            "- No markdown fencing. Return only the JSON array."
        ),
        messages=[{
            "role": "user",
            "content": (
                f"PATIENT PROFILE:\n{json.dumps(profile, indent=2, default=str)}\n\n"
                f"CRITERIA:\n{criteria_list}"
            )
        }],
    )

    text = next(b.text for b in response.content if b.type == "text").strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1].rsplit("```", 1)[0].strip()

    verdicts = json.loads(text)

    results = []
    for vd in verdicts:
        idx = vd["n"] - 1
        if idx < 0 or idx >= len(unchecked):
            continue
        c = unchecked[idx]
        results.append({
            "criterion": c["criterion_text"],
            "field": c["field_required"],
            "type": c["type"],
            "is_exclusion": c["is_exclusion"],
            "verdict": vd["verdict"],
            "reason": vd["reason"],
            "source": "llm_reasoning"
        })

    return results


# ═══════════════════════════════════════════════════════════════════════════
# Stage 5 — Eligibility Determination & Structured Result
# ═══════════════════════════════════════════════════════════════════════════

def determine_eligibility(results: list) -> str:
    if any(r["verdict"] == "not_met" for r in results):
        return "NOT_ELIGIBLE"
    if any(r["verdict"] == "cannot_determine" for r in results):
        return "PENDING_DATA"
    return "ELIGIBLE"


def build_result(profile: dict, trial: dict, all_results: list,
                  pipeline_steps: dict = None) -> dict:
    eligibility = determine_eligibility(all_results)

    result = {
        "patient": {
            "id": profile.get("patient_id"),
            "name": profile.get("patient_name"),
            "age": profile.get("age"),
            "sex": profile.get("sex"),
            "cancer_type": profile.get("cancer_type"),
            "histology": profile.get("histology"),
            "stage": profile.get("stage"),
            "ECOG": profile.get("ECOG"),
        },
        "trial": {
            "id": trial["trial_id"],
            "name": trial["trial_name"],
            "phase": trial["phase"],
        },
        "eligibility": eligibility,
        "summary": {
            "total_criteria": len(all_results),
            "met": sum(1 for r in all_results if r["verdict"] == "met"),
            "not_met": sum(1 for r in all_results if r["verdict"] == "not_met"),
            "cannot_determine": sum(1 for r in all_results if r["verdict"] == "cannot_determine"),
        },
        "disqualifying": [
            {"criterion": r["criterion"], "reason": r["reason"], "source": r["source"]}
            for r in all_results if r["verdict"] == "not_met"
        ],
        "missing_data": [
            {"criterion": r["criterion"], "field": r["field"], "data_needed": r["reason"]}
            for r in all_results if r["verdict"] == "cannot_determine"
        ],
        "criteria_met": [
            {"criterion": r["criterion"], "reason": r["reason"], "source": r["source"]}
            for r in all_results if r["verdict"] == "met"
        ],
    }

    if pipeline_steps:
        result["pipeline_steps"] = pipeline_steps

    return result


# ═══════════════════════════════════════════════════════════════════════════
# Console Report Printer
# ═══════════════════════════════════════════════════════════════════════════

def print_report(result: dict):
    p = result["patient"]
    t = result["trial"]
    s = result["summary"]
    elig = result["eligibility"]

    symbol = {"ELIGIBLE": "PASS", "NOT_ELIGIBLE": "FAIL", "PENDING_DATA": "PENDING"}[elig]

    print(f"\n{'=' * 78}")
    print("  CLINICAL TRIAL ELIGIBILITY REPORT")
    print(f"{'=' * 78}")
    print(f"  Patient:  {p.get('name') or p.get('id', '?')}")
    print(f"  Age/Sex:  {p.get('age', '?')} / {p.get('sex', '?')}    ECOG: {p.get('ECOG', '?')}")
    print(f"  Dx:       {p.get('cancer_type', '?')} — {p.get('histology', '?')}, Stage {p.get('stage', '?')}")
    print(f"  Trial:    {t['id']} ({t['phase']})")

    name = t["name"]
    print(f"  Protocol: {name[:72] + '...' if len(name) > 75 else name}")
    print(f"\n  >>> [{symbol}] {elig.replace('_', ' ')} <<<")
    print(f"      {s['met']} met / {s['not_met']} not met / {s['cannot_determine']} undetermined (of {s['total_criteria']})")
    print(f"{'-' * 78}")

    if result["disqualifying"]:
        print(f"\n  DISQUALIFYING ({len(result['disqualifying'])}):")
        for d in result["disqualifying"]:
            print(f"    x {d['criterion']}")
            print(f"      Reason: {d['reason']}  [{d['source']}]")

    if result["missing_data"]:
        print(f"\n  MISSING DATA ({len(result['missing_data'])}):")
        for i, m in enumerate(result["missing_data"], 1):
            print(f"    {i}. [{m['field']}] {m['data_needed']}")

    if result["criteria_met"]:
        print(f"\n  CRITERIA MET ({len(result['criteria_met'])}):")
        for c in result["criteria_met"]:
            reason_short = c["reason"][:80]
            print(f"    + {reason_short}")

    print(f"\n{'=' * 78}\n")


# ═══════════════════════════════════════════════════════════════════════════
# Embed Patient Profile (Voyage AI)
# ═══════════════════════════════════════════════════════════════════════════

def embed_patient(profile: dict) -> list:
    parts = [
        f"Patient: {profile.get('patient_name', 'Unknown')}",
        f"Age: {profile.get('age', '?')}, Sex: {profile.get('sex', '?')}",
        f"Diagnosis: {profile.get('cancer_type', profile.get('primary_diagnosis', 'Unknown'))}",
        f"Histology: {profile.get('histology', 'Unknown')}",
        f"Stage: {profile.get('stage', 'Unknown')}",
        f"ECOG: {profile.get('ECOG', '?')}",
        f"Biomarkers: EGFR={profile.get('EGFR_status')}, ALK={profile.get('ALK_status')}, "
        f"ROS1={profile.get('ROS1_status')}, HER2={profile.get('HER2_status')}, "
        f"PD-L1 TPS={profile.get('PD_L1_TPS')}",
    ]

    therapies = profile.get("prior_systemic_therapies") or []
    if therapies:
        parts.append("Prior therapies: " + ", ".join(t["drug_name"] for t in therapies))
    else:
        parts.append("Prior therapies: none")

    labs = []
    for key, label in [("ANC", "ANC"), ("platelets", "Plt"), ("hemoglobin", "Hgb"),
                        ("serum_creatinine", "Cr"), ("creatinine_clearance", "CrCl"),
                        ("AST", "AST"), ("ALT", "ALT"), ("total_bilirubin", "Bili")]:
        val = profile.get(key)
        if val is not None:
            labs.append(f"{label}={val}")
    if labs:
        parts.append("Labs: " + ", ".join(labs))

    notes = profile.get("notes", "")
    if notes:
        parts.append(f"Notes: {notes[:500]}")

    text = "\n".join(parts)
    result = vo.embed([text], model=VOYAGE_MODEL, input_type="query")
    return result.embeddings[0]


# ═══════════════════════════════════════════════════════════════════════════
# Stage 0 — Semantic Trial Matching (pgvector cosine similarity)
# ═══════════════════════════════════════════════════════════════════════════

def find_candidate_trials(profile: dict, top_k: int = 5,
                          required_trial_ids: list = None) -> list:
    from db import SessionLocal, Trial
    from pgvector.sqlalchemy import Vector

    patient_emb = embed_patient(profile)

    session = SessionLocal()
    try:
        rows = (
            session.query(
                Trial.id,
                Trial.name,
                Trial.phase,
                Trial.data,
                Trial.embedding.cosine_distance(patient_emb).label("distance"),
            )
            .filter(Trial.embedding.isnot(None))
            .order_by("distance")
            .limit(top_k)
            .all()
        )

        candidates = []
        seen_ids = set()
        for row in rows:
            similarity = round(1 - row.distance, 4)
            candidates.append({
                "trial_id": row.id,
                "trial_name": row.name,
                "phase": row.phase,
                "similarity": similarity,
                "data": row.data,
            })
            seen_ids.add(row.id)

        if required_trial_ids:
            for req_id in required_trial_ids:
                if req_id not in seen_ids:
                    req_row = session.get(Trial, req_id)
                    if req_row and req_row.embedding is not None:
                        from sqlalchemy import func, cast, Float, text as sa_text
                        dist_q = (
                            session.query(
                                Trial.embedding.cosine_distance(patient_emb).label("distance")
                            )
                            .filter(Trial.id == req_id)
                            .first()
                        )
                        sim = round(1 - dist_q.distance, 4) if dist_q else 0.0
                        candidates.append({
                            "trial_id": req_row.id,
                            "trial_name": req_row.name,
                            "phase": req_row.phase,
                            "similarity": sim,
                            "data": req_row.data,
                            "forced": True,
                        })
                    elif req_row:
                        candidates.append({
                            "trial_id": req_row.id,
                            "trial_name": req_row.name,
                            "phase": req_row.phase,
                            "similarity": 0.0,
                            "data": req_row.data,
                            "forced": True,
                        })

        return candidates
    finally:
        session.close()


# ═══════════════════════════════════════════════════════════════════════════
# Pipeline Orchestrator
# ═══════════════════════════════════════════════════════════════════════════

def run(patient_file: str, trials_file: str = "trials.json", trial_ids: list = None,
        persist: bool = True) -> list:
    from db import init_db, seed_trials, save_patient, save_result

    with open(trials_file, "r", encoding="utf-8") as f:
        trials = json.load(f)

    if trial_ids:
        trials = [t for t in trials if t["trial_id"] in trial_ids]

    if persist:
        print("\n[DB] Initializing database...")
        init_db()
        seed_trials(trials_file)

    print(f"\n[1/5] Ingesting: {patient_file}")
    text = ingest_document(patient_file)
    print(f"      {len(text)} chars extracted")

    print("[2/5] Extracting patient profile...")
    profile = extract_patient_profile(text)
    print(f"      {profile.get('patient_name', '?')}, {profile.get('age', '?')}yo, "
          f"{profile.get('cancer_type', '?')} Stage {profile.get('stage', '?')}, ECOG {profile.get('ECOG', '?')}")

    semantic_candidates = []
    if not trial_ids:
        print(f"\n[match] Semantic trial matching via Voyage AI + pgvector...")
        candidates = find_candidate_trials(profile, top_k=5)
        print(f"[match] Top {len(candidates)} candidate trials:")
        for c in candidates:
            forced = " [FORCED]" if c.get("forced") else ""
            print(f"        {c['trial_id']:20s} similarity={c['similarity']:.4f}{forced}")
        semantic_candidates = [
            {
                "trial_id": c["trial_id"],
                "trial_name": c["trial_name"],
                "phase": c["phase"],
                "similarity": c["similarity"],
                "forced": c.get("forced", False),
            }
            for c in candidates
        ]
        trials = [c["data"] for c in candidates]

    db_patient_id = None
    if persist:
        db_patient_id = save_patient(
            patient_id=profile.get("patient_id", "unknown"),
            patient_name=profile.get("patient_name"),
            note_text=text,
            profile=profile,
            source_file=os.path.basename(patient_file),
        )
        print(f"[DB] Saved patient (db id: {db_patient_id})")

    all_results = []
    for trial in trials:
        tid = trial["trial_id"]

        print(f"\n[3/5] Hard-rule filter: {tid}")
        hard = check_hard_rules(profile, trial)
        hm = sum(1 for r in hard if r["verdict"] == "met")
        hf = sum(1 for r in hard if r["verdict"] == "not_met")
        hu = sum(1 for r in hard if r["verdict"] == "cannot_determine")
        print(f"      {hm} pass / {hf} fail / {hu} undetermined")

        checked_keys = {(r["criterion"], r["field"]) for r in hard}

        print(f"[4/5] LLM reasoning: {tid}")
        llm = evaluate_with_llm(profile, trial, checked_keys)
        print(f"      {len(llm)} criteria evaluated by LLM")

        combined = hard + llm

        hard_rule_passed = not any(r["verdict"] == "not_met" for r in hard)

        pipeline_steps = {
            "semantic_search": semantic_candidates,
            "hard_rule_screening": {
                "trial_id": tid,
                "passed": hard_rule_passed,
                "total_rules": len(hard),
                "met": hm,
                "not_met": hf,
                "cannot_determine": hu,
                "details": hard,
            },
            "ai_reasoning": {
                "trial_id": tid,
                "total_evaluated": len(llm),
                "details": llm,
            },
        }

        print(f"[5/5] Building result: {tid}")
        result = build_result(profile, trial, combined, pipeline_steps=pipeline_steps)
        all_results.append(result)

        if persist and db_patient_id:
            rid = save_result(db_patient_id, tid, result)
            print(f"[DB] Saved result (db id: {rid}) — {result['eligibility']}")

    return all_results
