"""Position analysis and management API routes."""

from __future__ import annotations

import json
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from analyzer.position_analyzer import analyze_position
from database.db import get_db
from database.models import Position

router = APIRouter(prefix="/api/positions", tags=["positions"])


class PositionAnalyzeRequest(BaseModel):
    title: str
    description: str = ""


class PositionUpdateRequest(BaseModel):
    jd_json: Optional[str] = None
    keywords_json: Optional[str] = None
    scorecard_json: Optional[str] = None


@router.post("/analyze")
def api_analyze_position(
    req: PositionAnalyzeRequest,
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """AI-analyze a position and return JD + keywords + scorecard.

    Also persists the position to the database.
    """
    analysis = analyze_position(req.title, req.description)

    position = Position(
        title=req.title,
        description=req.description,
        jd_json=json.dumps(analysis.jd.model_dump(), ensure_ascii=False),
        keywords_json=json.dumps(
            {**analysis.keywords.model_dump(), "filters": analysis.filters.model_dump()},
            ensure_ascii=False,
        ),
        scorecard_json=json.dumps(analysis.scorecard.model_dump(), ensure_ascii=False),
    )
    db.add(position)
    db.commit()
    db.refresh(position)

    return {
        "position_id": position.id,
        "title": position.title,
        "jd": analysis.jd.model_dump(),
        "keywords": analysis.keywords.model_dump(),
        "filters": analysis.filters.model_dump(),
        "scorecard": analysis.scorecard.model_dump(),
    }


@router.get("")
def list_positions(db: Session = Depends(get_db)) -> list[dict[str, Any]]:
    """List all positions."""
    positions = db.query(Position).order_by(Position.created_at.desc()).all()
    return [
        {
            "id": p.id,
            "title": p.title,
            "description": p.description,
            "created_at": p.created_at.isoformat() if p.created_at else None,
            "candidate_count": len(p.candidates),
        }
        for p in positions
    ]


@router.get("/{position_id}")
def get_position(position_id: int, db: Session = Depends(get_db)) -> dict[str, Any]:
    """Get a single position with full details."""
    p = db.get(Position, position_id)
    if not p:
        raise HTTPException(404, "Position not found")
    return {
        "id": p.id,
        "title": p.title,
        "description": p.description,
        "jd": json.loads(p.jd_json) if p.jd_json else {},
        "keywords": json.loads(p.keywords_json) if p.keywords_json else {},
        "scorecard": json.loads(p.scorecard_json) if p.scorecard_json else {},
        "created_at": p.created_at.isoformat() if p.created_at else None,
    }


@router.put("/{position_id}")
def update_position(
    position_id: int,
    req: PositionUpdateRequest,
    db: Session = Depends(get_db),
) -> dict[str, str]:
    """Update a position's JD, keywords, or scorecard."""
    p = db.get(Position, position_id)
    if not p:
        raise HTTPException(404, "Position not found")

    if req.jd_json is not None:
        p.jd_json = req.jd_json
    if req.keywords_json is not None:
        p.keywords_json = req.keywords_json
    if req.scorecard_json is not None:
        p.scorecard_json = req.scorecard_json

    db.commit()
    return {"status": "updated"}
