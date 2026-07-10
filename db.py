import json
import os
from datetime import datetime, timezone

from dotenv import load_dotenv
from sqlalchemy import create_engine, Column, String, Text, DateTime, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import declarative_base, sessionmaker, Session

load_dotenv()

from sqlalchemy.engine import URL

engine = create_engine(
    URL.create(
        drivername="postgresql",
        username=os.environ.get("DATABASE_USER", "postgres"),
        password=os.environ.get("DATABASE_PASSWORD", ""),
        host=os.environ.get("DATABASE_HOST", "localhost"),
        port=int(os.environ.get("DATABASE_PORT", "5432")),
        database=os.environ.get("DATABASE_NAME", "postgres"),
    ),
    pool_pre_ping=True,
)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()


# ── Models ──────────────────────────────────────────────────────────────────

class Trial(Base):
    __tablename__ = "trials"

    id = Column(String, primary_key=True)
    name = Column(Text, nullable=False)
    phase = Column(String, nullable=False)
    data = Column(JSONB, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class Patient(Base):
    __tablename__ = "patients"

    id = Column(Integer, primary_key=True, autoincrement=True)
    patient_id = Column(String, nullable=False)
    patient_name = Column(String)
    note_text = Column(Text)
    profile = Column(JSONB)
    source_file = Column(String)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class Result(Base):
    __tablename__ = "results"

    id = Column(Integer, primary_key=True, autoincrement=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False)
    trial_id = Column(String, ForeignKey("trials.id"), nullable=False)
    eligibility = Column(String, nullable=False)
    summary = Column(JSONB)
    disqualifying = Column(JSONB)
    missing_data = Column(JSONB)
    criteria_met = Column(JSONB)
    full_result = Column(JSONB)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


# ── Table Creation ──────────────────────────────────────────────────────────

def init_db():
    Base.metadata.create_all(engine)


# ── CRUD Functions ──────────────────────────────────────────────────────────

def save_trial(trial_data: dict, session: Session = None):
    own_session = session is None
    if own_session:
        session = SessionLocal()
    try:
        existing = session.get(Trial, trial_data["trial_id"])
        if existing:
            existing.name = trial_data["trial_name"]
            existing.phase = trial_data["phase"]
            existing.data = trial_data
        else:
            session.add(Trial(
                id=trial_data["trial_id"],
                name=trial_data["trial_name"],
                phase=trial_data["phase"],
                data=trial_data,
            ))
        if own_session:
            session.commit()
    except Exception:
        if own_session:
            session.rollback()
        raise
    finally:
        if own_session:
            session.close()


def save_patient(patient_id: str, patient_name: str, note_text: str,
                 profile: dict, source_file: str = None) -> int:
    session = SessionLocal()
    try:
        patient = Patient(
            patient_id=patient_id,
            patient_name=patient_name,
            note_text=note_text,
            profile=profile,
            source_file=source_file,
        )
        session.add(patient)
        session.commit()
        session.refresh(patient)
        return patient.id
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def save_result(db_patient_id: int, trial_id: str, result: dict) -> int:
    session = SessionLocal()
    try:
        row = Result(
            patient_id=db_patient_id,
            trial_id=trial_id,
            eligibility=result["eligibility"],
            summary=result["summary"],
            disqualifying=result["disqualifying"],
            missing_data=result["missing_data"],
            criteria_met=result["criteria_met"],
            full_result=result,
        )
        session.add(row)
        session.commit()
        session.refresh(row)
        return row.id
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def get_all_results() -> list:
    session = SessionLocal()
    try:
        rows = session.query(Result).order_by(Result.created_at.desc()).all()
        return [
            {
                "id": r.id,
                "patient_id": r.patient_id,
                "trial_id": r.trial_id,
                "eligibility": r.eligibility,
                "summary": r.summary,
                "created_at": r.created_at.isoformat(),
                "full_result": r.full_result,
            }
            for r in rows
        ]
    finally:
        session.close()


def get_result_by_id(result_id: int) -> dict | None:
    session = SessionLocal()
    try:
        r = session.get(Result, result_id)
        if not r:
            return None
        return {
            "id": r.id,
            "patient_id": r.patient_id,
            "trial_id": r.trial_id,
            "eligibility": r.eligibility,
            "summary": r.summary,
            "disqualifying": r.disqualifying,
            "missing_data": r.missing_data,
            "criteria_met": r.criteria_met,
            "full_result": r.full_result,
            "created_at": r.created_at.isoformat(),
        }
    finally:
        session.close()


# ── Seed Trials ─────────────────────────────────────────────────────────────

def seed_trials(trials_file: str = "trials.json"):
    session = SessionLocal()
    try:
        count = session.query(Trial).count()
        if count > 0:
            print(f"  Trials table already has {count} rows, skipping seed")
            return

        with open(trials_file, "r", encoding="utf-8") as f:
            trials = json.load(f)

        for t in trials:
            save_trial(t, session=session)

        session.commit()
        print(f"  Seeded {len(trials)} trials from {trials_file}")
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


# ── Standalone Init ─────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("Initializing database...")
    init_db()
    print("Tables created.")
    seed_trials()
    print("Done.")
