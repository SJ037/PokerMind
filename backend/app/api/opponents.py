from __future__ import annotations

from fastapi import APIRouter, HTTPException

from backend.app.modeling.opponent import OpponentProfile
from backend.app.schemas.analysis import OpponentObservationRequest
from backend.app.storage.db import list_opponents, load_opponent, save_opponent

router = APIRouter()


def _deserialize(opponent_id: str, payload: dict[str, object]) -> OpponentProfile:
    profile = OpponentProfile.with_archetype(opponent_id, str(payload.get("archetype", "unknown")))
    profile.fold_vs_raise.alpha = float(payload["fold_vs_raise"]["alpha"])
    profile.fold_vs_raise.beta = float(payload["fold_vs_raise"]["beta"])
    profile.raise_frequency.alpha = float(payload["raise_frequency"]["alpha"])
    profile.raise_frequency.beta = float(payload["raise_frequency"]["beta"])
    profile.cbet_frequency.alpha = float(payload["cbet_frequency"]["alpha"])
    profile.cbet_frequency.beta = float(payload["cbet_frequency"]["beta"])
    return profile


@router.get("/opponents")
def get_opponents() -> list[dict[str, object]]:
    return list_opponents()


@router.get("/opponents/{opponent_id}")
def get_opponent(opponent_id: str) -> dict[str, object]:
    payload = load_opponent(opponent_id)
    if payload is None:
        raise HTTPException(status_code=404, detail="Opponent not found")
    return payload


@router.post("/opponents/observe")
def observe(req: OpponentObservationRequest) -> dict[str, object]:
    payload = load_opponent(req.opponent_id)
    if payload is None:
        profile = OpponentProfile.with_archetype(req.opponent_id, req.archetype)
    else:
        profile = _deserialize(req.opponent_id, payload)

    profile.observe(req.event, req.success)
    serialized = profile.to_dict()
    save_opponent(req.opponent_id, profile.archetype, serialized)
    return serialized
