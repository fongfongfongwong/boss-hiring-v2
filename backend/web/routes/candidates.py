"""Candidate management API routes."""

from __future__ import annotations

import json
from io import BytesIO
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse, StreamingResponse
from sqlalchemy.orm import Session

from database.db import get_db
from database.models import Candidate, ChatMessage, ContactInfo, Resume

router = APIRouter(prefix="/api/candidates", tags=["candidates"])


@router.get("")
def list_candidates(
    task_id: Optional[int] = Query(None),
    position_id: Optional[int] = Query(None),
    status: Optional[str] = Query(None),
    min_score: Optional[float] = Query(None),
    sort_by: str = Query("created_at"),
    order: str = Query("desc"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """List candidates with filtering, sorting, and pagination."""
    q = db.query(Candidate)

    if task_id:
        q = q.filter(Candidate.task_id == task_id)
    if position_id:
        q = q.filter(Candidate.position_id == position_id)
    if status:
        q = q.filter(Candidate.status == status)
    if min_score is not None:
        q = q.filter(Candidate.pre_match_score >= min_score)

    # Sorting
    sort_col = getattr(Candidate, sort_by, Candidate.created_at)
    if order == "desc":
        q = q.order_by(sort_col.desc())
    else:
        q = q.order_by(sort_col.asc())

    total = q.count()
    candidates = q.offset((page - 1) * page_size).limit(page_size).all()

    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "items": [_candidate_summary(c) for c in candidates],
    }


@router.get("/export")
def export_candidates(
    task_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
):
    """Export candidates to an Excel file."""
    try:
        import openpyxl
    except ImportError:
        raise HTTPException(500, "openpyxl not installed")

    q = db.query(Candidate)
    if task_id:
        q = q.filter(Candidate.task_id == task_id)
    candidates = q.order_by(Candidate.created_at.desc()).all()

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Candidates"

    headers = ["ID", "姓名", "状态", "初筛分数", "简历评分", "微信", "手机", "创建时间"]
    ws.append(headers)

    for c in candidates:
        resume_score = c.resume.weighted_total if c.resume else ""
        wechat = c.contact.wechat if c.contact else ""
        phone = c.contact.phone if c.contact else ""
        ws.append([
            c.id,
            c.name,
            c.status,
            c.pre_match_score,
            resume_score,
            wechat,
            phone,
            c.created_at.isoformat() if c.created_at else "",
        ])

    buf = BytesIO()
    wb.save(buf)
    buf.seek(0)

    return StreamingResponse(
        buf,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=candidates.xlsx"},
    )


@router.get("/{candidate_id}")
def get_candidate(candidate_id: int, db: Session = Depends(get_db)) -> dict[str, Any]:
    """Get detailed information about a single candidate."""
    c = db.get(Candidate, candidate_id)
    if not c:
        raise HTTPException(404, "Candidate not found")

    result = _candidate_summary(c)

    # Add full details
    result["boss_profile"] = json.loads(c.boss_profile_json) if c.boss_profile_json else {}

    # Resume & score
    if c.resume:
        result["resume"] = {
            "file_path": c.resume.file_path,
            "file_type": c.resume.file_type,
            "extracted": json.loads(c.resume.extracted_json) if c.resume.extracted_json else {},
            "score": json.loads(c.resume.score_json) if c.resume.score_json else {},
            "weighted_total": c.resume.weighted_total,
            "is_qualified": c.resume.is_qualified,
            "analysis_report": c.resume.analysis_report,
        }

    # Contact info
    if c.contact:
        result["contact"] = {
            "wechat": c.contact.wechat,
            "phone": c.contact.phone,
            "email": c.contact.email,
            "obtained_at": c.contact.obtained_at.isoformat() if c.contact.obtained_at else None,
        }

    return result


@router.get("/{candidate_id}/messages")
def get_messages(candidate_id: int, db: Session = Depends(get_db)) -> list[dict[str, Any]]:
    """Get all chat messages for a candidate."""
    messages = (
        db.query(ChatMessage)
        .filter(ChatMessage.candidate_id == candidate_id)
        .order_by(ChatMessage.created_at.asc())
        .all()
    )
    return [
        {
            "id": m.id,
            "direction": m.direction,
            "content": m.content,
            "message_type": m.message_type,
            "created_at": m.created_at.isoformat() if m.created_at else None,
        }
        for m in messages
    ]


@router.get("/{candidate_id}/resume")
def download_resume(candidate_id: int, db: Session = Depends(get_db)):
    """Download the resume file for a candidate."""
    resume = db.query(Resume).filter(Resume.candidate_id == candidate_id).first()
    if not resume or not resume.file_path:
        raise HTTPException(404, "Resume file not found")

    from pathlib import Path
    path = Path(resume.file_path)
    if not path.exists():
        raise HTTPException(404, "Resume file not found on disk")

    return FileResponse(
        path=str(path),
        filename=path.name,
        media_type="application/octet-stream",
    )


def _candidate_summary(c: Candidate) -> dict[str, Any]:
    """Build a summary dict for a candidate."""
    return {
        "id": c.id,
        "task_id": c.task_id,
        "position_id": c.position_id,
        "name": c.name,
        "status": c.status,
        "pre_match_score": c.pre_match_score,
        "resume_score": c.resume.weighted_total if c.resume else None,
        "is_qualified": c.resume.is_qualified if c.resume else None,
        "has_contact": c.contact is not None,
        "created_at": c.created_at.isoformat() if c.created_at else None,
    }
