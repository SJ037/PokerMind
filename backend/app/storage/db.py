from __future__ import annotations

import json
from pathlib import Path

from sqlalchemy import Column, String, Text, create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

DB_PATH = Path(__file__).resolve().parents[3] / "pokermind.db"
engine = create_engine(f"sqlite:///{DB_PATH}", future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


class Base(DeclarativeBase):
    pass


class OpponentRecord(Base):
    __tablename__ = "opponents"

    opponent_id = Column(String, primary_key=True)
    archetype = Column(String, nullable=False)
    profile_json = Column(Text, nullable=False)


def init_db() -> None:
    Base.metadata.create_all(engine)


def save_opponent(opponent_id: str, archetype: str, payload: dict[str, object]) -> None:
    init_db()
    with Session(engine) as session:
        existing = session.get(OpponentRecord, opponent_id)
        if existing is None:
            record = OpponentRecord(
                opponent_id=opponent_id,
                archetype=archetype,
                profile_json=json.dumps(payload),
            )
            session.add(record)
        else:
            existing.archetype = archetype
            existing.profile_json = json.dumps(payload)
        session.commit()


def load_opponent(opponent_id: str) -> dict[str, object] | None:
    init_db()
    with Session(engine) as session:
        record = session.get(OpponentRecord, opponent_id)
        if record is None:
            return None
        return json.loads(record.profile_json)


def list_opponents() -> list[dict[str, object]]:
    init_db()
    with Session(engine) as session:
        rows = session.query(OpponentRecord).all()
        return [
            {
                "opponent_id": row.opponent_id,
                "archetype": row.archetype,
                "profile": json.loads(row.profile_json),
            }
            for row in rows
        ]
