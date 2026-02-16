"""Recruitment task management API routes."""

from __future__ import annotations

import json
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from database.db import get_db
from database.models import RecruitTask, Position
from pipeline.events import PipelineEvent
from pipeline.orchestrator import RecruitPipeline
from pipeline.task_manager import task_manager, TaskControl
from web.routes.websocket import ws_manager

router = APIRouter(prefix="/api/tasks", tags=["tasks"])


class TaskCreateRequest(BaseModel):
    position_id: int
    config: dict[str, Any] = {}


@router.post("")
async def create_task(
    req: TaskCreateRequest,
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """Create and start a new recruitment task."""
    position = db.get(Position, req.position_id)
    if not position:
        raise HTTPException(404, "Position not found")

    task = RecruitTask(
        position_id=req.position_id,
        status="pending",
        config_json=json.dumps(req.config, ensure_ascii=False),
        progress_json="{}",
    )
    db.add(task)
    db.commit()
    db.refresh(task)

    # Define the event callback to push to WebSocket
    async def emit_event(event: PipelineEvent) -> None:
        await ws_manager.broadcast(task.id, event.to_dict())

    # Create the control first, then the pipeline, then schedule
    ctrl = TaskControl(task.id)
    pipeline = RecruitPipeline(
        task_id=task.id,
        control=ctrl,
        emit=emit_event,
    )

    # Register and start the pipeline coroutine
    import asyncio
    task_manager.register_task(task.id, ctrl, asyncio.create_task(pipeline.run()))

    return {
        "task_id": task.id,
        "status": task.status,
        "position": position.title,
    }


@router.get("")
def list_tasks(db: Session = Depends(get_db)) -> list[dict[str, Any]]:
    """List all tasks."""
    tasks = db.query(RecruitTask).order_by(RecruitTask.created_at.desc()).all()
    return [
        {
            "id": t.id,
            "position_id": t.position_id,
            "position_title": t.position.title if t.position else "",
            "status": t.status,
            "progress": json.loads(t.progress_json) if t.progress_json else {},
            "started_at": t.started_at.isoformat() if t.started_at else None,
            "completed_at": t.completed_at.isoformat() if t.completed_at else None,
            "created_at": t.created_at.isoformat() if t.created_at else None,
        }
        for t in tasks
    ]


@router.get("/{task_id}")
def get_task(task_id: int, db: Session = Depends(get_db)) -> dict[str, Any]:
    """Get a task with full details."""
    t = db.get(RecruitTask, task_id)
    if not t:
        raise HTTPException(404, "Task not found")
    return {
        "id": t.id,
        "position_id": t.position_id,
        "position_title": t.position.title if t.position else "",
        "status": t.status,
        "config": json.loads(t.config_json) if t.config_json else {},
        "progress": json.loads(t.progress_json) if t.progress_json else {},
        "error_message": t.error_message,
        "started_at": t.started_at.isoformat() if t.started_at else None,
        "completed_at": t.completed_at.isoformat() if t.completed_at else None,
        "created_at": t.created_at.isoformat() if t.created_at else None,
        "candidate_count": len(t.candidates),
    }


@router.post("/{task_id}/pause")
def pause_task(task_id: int, db: Session = Depends(get_db)) -> dict[str, str]:
    """Pause a running task."""
    t = db.get(RecruitTask, task_id)
    if not t:
        raise HTTPException(404, "Task not found")
    if t.status != "running":
        raise HTTPException(400, "Task is not running")

    task_manager.pause_task(task_id)
    t.status = "paused"
    db.commit()
    return {"status": "paused"}


@router.post("/{task_id}/resume")
def resume_task(task_id: int, db: Session = Depends(get_db)) -> dict[str, str]:
    """Resume a paused task."""
    t = db.get(RecruitTask, task_id)
    if not t:
        raise HTTPException(404, "Task not found")
    if t.status != "paused":
        raise HTTPException(400, "Task is not paused")

    task_manager.resume_task(task_id)
    t.status = "running"
    db.commit()
    return {"status": "running"}


@router.post("/{task_id}/stop")
def stop_task(task_id: int, db: Session = Depends(get_db)) -> dict[str, str]:
    """Stop a running or paused task."""
    t = db.get(RecruitTask, task_id)
    if not t:
        raise HTTPException(404, "Task not found")

    task_manager.stop_task(task_id)
    t.status = "completed"
    t.completed_at = datetime.utcnow()
    db.commit()
    return {"status": "stopped"}
