import anthropic
import json
import sys
from dotenv import load_dotenv

load_dotenv()

client = anthropic.Anthropic()

CRITERION_SCHEMA = {
    "type": "object",
    "properties": {
        "criterion_text": {"type": "string"},
        "field_required": {"type": "string"},
        "type": {"type": "string", "enum": ["hard_rule", "judgment_call"]}
    },
    "required": ["criterion_text", "field_required", "type"],
    "additionalProperties": False
}

TRIAL_SCHEMA = {
    "type": "object",
    "properties": {
        "trial_id": {"type": "string"},
        "trial_name": {"type": "string"},
        "phase": {"type": "string"},
        "inclusion_criteria": {"type": "array", "items": CRITERION_SCHEMA},
        "exclusion_criteria": {"type": "array", "items": CRITERION_SCHEMA}
    },
    "required": ["trial_id", "trial_name", "phase", "inclusion_criteria", "exclusion_criteria"],
    "additionalProperties": False
}

SYSTEM_PROMPT = """You are an expert clinical trial protocol parser. Your job is to read raw, unstructured clinical trial protocol documents and extract structured eligibility criteria.

For each criterion you extract:
- criterion_text: A clear, concise statement of the criterion. Normalize messy language into a clean sentence.
- field_required: The patient data field needed to evaluate this criterion (e.g., "age", "diagnosis", "ECOG_performance_status", "lab_ANC", "lab_platelets", "EGFR_mutation_status", "prior_therapy_history", "LVEF", "HER2_status", etc.)
- type: Classify as either:
  - "hard_rule": Objectively checkable from structured patient data (lab values, age, diagnosis codes, specific mutation status, measurable thresholds)
  - "judgment_call": Requires clinical reasoning, investigator judgment, or subjective assessment (e.g., "adequate organ function" without specific thresholds, "clinically significant cardiac disease", case-by-case PS 2 approval, tumor board decisions)

Important guidelines:
- Extract EVERY distinct eligibility criterion, even if buried in paragraphs or cross-references.
- Split compound criteria into individual items when they test different patient attributes.
- If a criterion has a specific numeric threshold, it's a hard_rule.
- If a criterion requires "discussion with medical monitor" or "investigator judgment", it's a judgment_call.
- Ignore duplicate criteria (e.g., if autoimmune disease is mentioned twice, include it once).
- Ignore administrative criteria (informed consent, IRB approval) — focus on medical/clinical criteria.
- For criteria with conditional logic (e.g., "X unless Y"), capture the full conditional as one criterion."""


def parse_trial_protocol(raw_text: str) -> dict:
    response = client.messages.create(
        model="claude-sonnet-5",
        max_tokens=16000,
        thinking={"type": "adaptive"},
        system=SYSTEM_PROMPT,
        messages=[{
            "role": "user",
            "content": f"Parse the following clinical trial protocol into structured JSON.\n\n{raw_text}"
        }],
        output_config={
            "format": {
                "type": "json_schema",
                "schema": TRIAL_SCHEMA
            }
        }
    )

    text = next(b.text for b in response.content if b.type == "text")
    return json.loads(text)


if __name__ == "__main__":
    files = ["trial_A_raw.txt", "trial_B_raw.txt"]
    trials = []

    for filepath in files:
        print(f"Parsing {filepath}...")
        with open(filepath, "r", encoding="utf-8") as f:
            raw_text = f.read()
        result = parse_trial_protocol(raw_text)
        trials.append(result)
        print(f"  -> {result['trial_id']}: {len(result['inclusion_criteria'])} inclusion, {len(result['exclusion_criteria'])} exclusion criteria")

    with open("trials.json", "w", encoding="utf-8") as f:
        json.dump(trials, f, indent=2, ensure_ascii=False)

    print(f"\nSaved {len(trials)} trials to trials.json")
