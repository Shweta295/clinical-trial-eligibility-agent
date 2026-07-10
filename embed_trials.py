import json
import os
import time

import voyageai
from dotenv import load_dotenv

from config import VOYAGE_MODEL
from db import init_db, SessionLocal, Trial

load_dotenv()

vo = voyageai.Client(api_key=os.environ["VOYAGE_API_KEY"])

BATCH_SIZE = 3


def trial_to_text(trial: dict) -> str:
    parts = [
        f"Trial: {trial['trial_name']}",
        f"Phase: {trial['phase']}",
        "Inclusion Criteria:",
    ]
    for c in trial.get("inclusion_criteria", []):
        parts.append(f"  - {c['criterion_text']}")
    parts.append("Exclusion Criteria:")
    for c in trial.get("exclusion_criteria", []):
        parts.append(f"  - {c['criterion_text']}")
    return "\n".join(parts)


def embed_trials(trials_file: str = "trials.json"):
    init_db()

    with open(trials_file, "r", encoding="utf-8") as f:
        trials = json.load(f)

    texts = [trial_to_text(t) for t in trials]
    ids = [t["trial_id"] for t in trials]

    print(f"Embedding {len(texts)} trials with {VOYAGE_MODEL} (batch size {BATCH_SIZE})...")

    all_embeddings = []
    for i in range(0, len(texts), BATCH_SIZE):
        batch_texts = texts[i:i + BATCH_SIZE]
        batch_ids = ids[i:i + BATCH_SIZE]
        print(f"  Batch {i // BATCH_SIZE + 1}: {', '.join(batch_ids)}")
        result = vo.embed(batch_texts, model=VOYAGE_MODEL, input_type="document")
        all_embeddings.extend(result.embeddings)
        if i + BATCH_SIZE < len(texts):
            time.sleep(21)

    print(f"  Received {len(all_embeddings)} embeddings, dim={len(all_embeddings[0])}")

    session = SessionLocal()
    try:
        for trial_id, emb in zip(ids, all_embeddings):
            row = session.get(Trial, trial_id)
            if row:
                row.embedding = emb
            else:
                print(f"  WARNING: trial {trial_id} not in DB, skipping")
        session.commit()
        print(f"  Stored embeddings for {len(all_embeddings)} trials")
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()

    session = SessionLocal()
    try:
        count = session.query(Trial).filter(Trial.embedding.isnot(None)).count()
        print(f"\nVerification: {count}/{len(trials)} trials have embeddings in DB")
    finally:
        session.close()


if __name__ == "__main__":
    embed_trials()
