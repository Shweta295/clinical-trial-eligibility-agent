import json
import sys
import os
from pipeline import run, print_report


def main():
    if len(sys.argv) < 2:
        print("Usage: python main.py <patient_note> [--trial TRIAL_ID] [--trials-file FILE] [--json] [--no-db]")
        print("\nSupported formats: .txt, .pdf, .png, .jpg, .jpeg, .gif, .webp")
        print("\nExamples:")
        print("  python main.py patient_success.txt")
        print("  python main.py patient_success_scanned.png")
        print("  python main.py patient_success.txt --trial ONC-2024-0471")
        print("  python main.py patient_success.txt --json")
        print("  python main.py patient_success.txt --no-db")
        sys.exit(1)

    patient_file = sys.argv[1]
    if not os.path.exists(patient_file):
        print(f"Error: {patient_file} not found")
        sys.exit(1)

    trials_file = "trials.json"
    trial_ids = None
    output_json = False
    persist = True

    i = 2
    while i < len(sys.argv):
        if sys.argv[i] == "--trial" and i + 1 < len(sys.argv):
            trial_ids = [sys.argv[i + 1]]
            i += 2
        elif sys.argv[i] == "--trials-file" and i + 1 < len(sys.argv):
            trials_file = sys.argv[i + 1]
            i += 2
        elif sys.argv[i] == "--json":
            output_json = True
            i += 1
        elif sys.argv[i] == "--no-db":
            persist = False
            i += 1
        else:
            i += 1

    results = run(patient_file, trials_file, trial_ids, persist=persist)

    if output_json:
        print(json.dumps(results, indent=2, ensure_ascii=False))
    else:
        for result in results:
            print_report(result)


if __name__ == "__main__":
    main()
