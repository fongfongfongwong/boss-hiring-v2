"""Dashboard statistics API routes."""

from __future__ import annotations

import json
from typing import Any

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from database.db import get_db
from database.models import Candidate, RecruitTask, Position

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("/stats")
def get_stats(db: Session = Depends(get_db)) -> dict[str, Any]:
    """Global dashboard statistics."""
    total_positions = db.query(Position).count()
    total_tasks = db.query(RecruitTask).count()
    active_tasks = db.query(RecruitTask).filter(RecruitTask.status == "running").count()
    total_candidates = db.query(Candidate).count()
    greeted = db.query(Candidate).filter(Candidate.status != "found").count()
    resume_received = db.query(Candidate).filter(
        Candidate.status.in_(["resume_received", "scored", "qualified", "contact_obtained"])
    ).count()
    qualified = db.query(Candidate).filter(
        Candidate.status.in_(["qualified", "contact_obtained"])
    ).count()
    contact_obtained = db.query(Candidate).filter(
        Candidate.status == "contact_obtained"
    ).count()

    return {
        "total_positions": total_positions,
        "total_tasks": total_tasks,
        "active_tasks": active_tasks,
        "total_candidates": total_candidates,
        "greeted": greeted,
        "resume_received": resume_received,
        "qualified": qualified,
        "contact_obtained": contact_obtained,
    }


@router.get("/funnel/{task_id}")
def get_funnel(task_id: int, db: Session = Depends(get_db)) -> dict[str, Any]:
    """Recruitment funnel data for a specific task."""
    task = db.get(RecruitTask, task_id)
    if not task:
        return {"error": "Task not found"}

    candidates = db.query(Candidate).filter(Candidate.task_id == task_id).all()

    status_counts: dict[str, int] = {}
    for c in candidates:
        status_counts[c.status] = status_counts.get(c.status, 0) + 1

    # Build ordered funnel
    funnel = [
        {"stage": "搜索发现", "count": len(candidates)},
        {"stage": "初筛通过", "count": len([c for c in candidates if c.pre_match_score >= 50])},
        {"stage": "已打招呼", "count": sum(1 for c in candidates if c.status not in ("found", "rejected"))},
        {"stage": "已回复", "count": sum(1 for c in candidates if c.status in ("chatting", "resume_received", "scored", "qualified", "contact_obtained"))},
        {"stage": "收到简历", "count": sum(1 for c in candidates if c.status in ("resume_received", "scored", "qualified", "contact_obtained"))},
        {"stage": "评分达标", "count": sum(1 for c in candidates if c.status in ("qualified", "contact_obtained"))},
        {"stage": "获取联系方式", "count": sum(1 for c in candidates if c.status == "contact_obtained")},
    ]

    return {
        "task_id": task_id,
        "position_title": task.position.title if task.position else "",
        "status": task.status,
        "funnel": funnel,
        "status_counts": status_counts,
    }
