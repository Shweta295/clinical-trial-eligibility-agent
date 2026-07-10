from pipeline import extract_patient_profile, find_candidate_trials
from utils import ingest_document

PATIENTS = [
    ("patient_success.txt",    "ONC-2024-0471", "NSCLC eligible"),
    ("patient_rejection.txt",  "ONC-2024-0471", "NSCLC rejected (pembrolizumab)"),
    ("patient_missing.txt",    "ONC-2024-0471", "NSCLC missing data"),
    ("patient_borderline.txt", "ONC-2024-0471", "NSCLC borderline"),
]

for file, expected_trial, desc in PATIENTS:
    print(f"\n{'='*70}")
    print(f"  {file} — {desc}")
    print(f"  Expected trial: {expected_trial}")
    print(f"{'='*70}")

    text = ingest_document(file)
    profile = extract_patient_profile(text)
    print(f"  Patient: {profile.get('patient_name')}, {profile.get('age')}yo")
    print(f"  Dx: {profile.get('cancer_type')}, Stage {profile.get('stage')}")

    candidates = find_candidate_trials(profile, top_k=5)

    print(f"\n  Rank  Trial ID              Similarity  Match?")
    print(f"  ----  --------------------  ----------  ------")
    found = False
    for i, c in enumerate(candidates, 1):
        is_match = c["trial_id"] == expected_trial
        if is_match:
            found = True
        marker = " <-- EXPECTED" if is_match else ""
        forced = " [FORCED]" if c.get("forced") else ""
        print(f"  #{i:<3}  {c['trial_id']:20s}  {c['similarity']:.4f}      {'YES' if is_match else '   '}{marker}{forced}")

    status = "PASS" if found else "FAIL"
    print(f"\n  >> {status}: {expected_trial} {'FOUND' if found else 'NOT FOUND'} in top 5")

print(f"\n{'='*70}")
print("  ALL TESTS COMPLETE")
print(f"{'='*70}")
