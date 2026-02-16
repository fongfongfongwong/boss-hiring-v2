"""Market research API routes – quant/trading company intelligence board."""

from __future__ import annotations

import asyncio
import json
import logging
from datetime import datetime
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from pydantic import BaseModel
from sqlalchemy.orm import Session

from database.db import SessionLocal
from database.models import MarketCompany, MarketCompanySnapshot

router = APIRouter(prefix="/api/market", tags=["market-research"])
logger = logging.getLogger(__name__)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ── Request / Response models ────────────────────────────────────────

class CompanyCreate(BaseModel):
    name: str
    name_en: Optional[str] = ""
    region: Optional[str] = "CN"
    category: Optional[str] = "quant"
    website: Optional[str] = ""
    headquarters: Optional[str] = ""
    description: Optional[str] = ""


# ── Status tracking for background tasks ─────────────────────────────

_task_status: dict[str, Any] = {}


# ── Endpoints ────────────────────────────────────────────────────────

@router.get("/companies")
def list_companies(
    region: Optional[str] = None,
    category: Optional[str] = None,
    db: Session = Depends(get_db),
) -> list[dict[str, Any]]:
    """List all tracked companies with optional filtering."""
    query = db.query(MarketCompany)
    if region:
        query = query.filter(MarketCompany.region == region)
    if category:
        query = query.filter(MarketCompany.category == category)

    companies = query.order_by(MarketCompany.region, MarketCompany.name).all()
    result = []
    for c in companies:
        positions = json.loads(c.open_positions_json) if c.open_positions_json else []
        result.append({
            "id": c.id,
            "name": c.name,
            "name_en": c.name_en or "",
            "region": c.region,
            "category": c.category,
            "website": c.website or "",
            "headquarters": c.headquarters or "",
            "description": c.description or "",
            "open_positions": positions,
            "open_position_count": len(positions),
            "talent_profile": c.talent_profile or "",
            "supplementary_info": c.supplementary_info or "",
            "boss_resume_count": c.boss_resume_count,
            "last_researched_at": c.last_researched_at.isoformat() if c.last_researched_at else None,
            "last_boss_updated_at": c.last_boss_updated_at.isoformat() if c.last_boss_updated_at else None,
            "created_at": c.created_at.isoformat() if c.created_at else None,
        })
    return result


@router.get("/companies/{company_id}")
def get_company(
    company_id: int,
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """Get detailed info for a single company."""
    c = db.query(MarketCompany).filter(MarketCompany.id == company_id).first()
    if not c:
        raise HTTPException(status_code=404, detail="公司不存在")

    positions = json.loads(c.open_positions_json) if c.open_positions_json else []

    # Get recent snapshots for trend data
    snapshots = (
        db.query(MarketCompanySnapshot)
        .filter(MarketCompanySnapshot.company_id == company_id)
        .order_by(MarketCompanySnapshot.snapshot_date.desc())
        .limit(30)
        .all()
    )

    return {
        "id": c.id,
        "name": c.name,
        "name_en": c.name_en or "",
        "region": c.region,
        "category": c.category,
        "website": c.website or "",
        "headquarters": c.headquarters or "",
        "description": c.description or "",
        "open_positions": positions,
        "talent_profile": c.talent_profile or "",
        "supplementary_info": c.supplementary_info or "",
        "boss_resume_count": c.boss_resume_count,
        "last_researched_at": c.last_researched_at.isoformat() if c.last_researched_at else None,
        "snapshots": [
            {
                "date": s.snapshot_date,
                "boss_resume_count": s.boss_resume_count,
                "open_position_count": s.open_position_count,
            }
            for s in snapshots
        ],
    }


@router.post("/companies")
def add_company(
    req: CompanyCreate,
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """Manually add a company to track."""
    existing = db.query(MarketCompany).filter(MarketCompany.name == req.name).first()
    if existing:
        raise HTTPException(status_code=409, detail="该公司已存在")

    company = MarketCompany(
        name=req.name,
        name_en=req.name_en or "",
        region=req.region or "CN",
        category=req.category or "quant",
        website=req.website or "",
        headquarters=req.headquarters or "",
        description=req.description or "",
    )
    db.add(company)
    db.commit()
    db.refresh(company)

    return {"id": company.id, "name": company.name, "status": "added"}


@router.delete("/companies/{company_id}")
def delete_company(
    company_id: int,
    db: Session = Depends(get_db),
) -> dict[str, str]:
    """Remove a company from tracking."""
    c = db.query(MarketCompany).filter(MarketCompany.id == company_id).first()
    if not c:
        raise HTTPException(status_code=404, detail="公司不存在")

    db.query(MarketCompanySnapshot).filter(
        MarketCompanySnapshot.company_id == company_id
    ).delete()
    db.delete(c)
    db.commit()
    return {"status": "deleted"}


@router.post("/seed")
def seed_companies(background_tasks: BackgroundTasks) -> dict[str, str]:
    """Trigger LLM to generate a seed list of quant/trading companies."""
    _task_status["seed"] = {"status": "running", "started_at": datetime.utcnow().isoformat()}
    background_tasks.add_task(_run_seed)
    return {"status": "started", "message": "正在通过 AI 生成量化/交易公司列表，请稍候..."}


@router.post("/companies/{company_id}/research")
def research_single(
    company_id: int,
    background_tasks: BackgroundTasks,
) -> dict[str, str]:
    """Trigger deep research for a single company."""
    _task_status[f"research_{company_id}"] = {"status": "running"}
    background_tasks.add_task(_run_research_single, company_id)
    return {"status": "started", "message": "正在调研该公司..."}


@router.post("/research-all")
def research_all(background_tasks: BackgroundTasks) -> dict[str, str]:
    """Trigger research for all tracked companies."""
    _task_status["research_all"] = {"status": "running", "started_at": datetime.utcnow().isoformat()}
    background_tasks.add_task(_run_research_all)
    return {"status": "started", "message": "正在批量调研所有公司，这可能需要几分钟..."}


@router.get("/task-status")
def get_task_status() -> dict[str, Any]:
    """Check the status of background research tasks."""
    return _task_status


@router.get("/summary")
def get_summary(db: Session = Depends(get_db)) -> dict[str, Any]:
    """Get market overview statistics."""
    total = db.query(MarketCompany).count()
    cn_count = db.query(MarketCompany).filter(MarketCompany.region == "CN").count()
    us_count = db.query(MarketCompany).filter(MarketCompany.region == "US").count()

    # Count by category
    categories = {}
    for c in db.query(MarketCompany).all():
        cat = c.category or "other"
        categories[cat] = categories.get(cat, 0) + 1

    # Companies with research data
    researched = db.query(MarketCompany).filter(
        MarketCompany.last_researched_at.isnot(None)
    ).count()

    # Total open positions
    total_positions = 0
    for c in db.query(MarketCompany).all():
        try:
            positions = json.loads(c.open_positions_json) if c.open_positions_json else []
            total_positions += len(positions)
        except Exception:
            pass

    return {
        "total_companies": total,
        "cn_companies": cn_count,
        "us_companies": us_count,
        "categories": categories,
        "researched_count": researched,
        "total_open_positions": total_positions,
    }


@router.post("/generate-report")
def generate_report() -> dict[str, str]:
    """Generate a comprehensive market summary report via LLM."""
    from market_research.researcher import generate_market_summary
    report = generate_market_summary()
    return {"report": report}


# ── Background task runners ──────────────────────────────────────────

def _run_seed() -> None:
    try:
        from market_research.researcher import seed_companies
        result = seed_companies()
        _task_status["seed"] = {
            "status": "completed",
            "count": len(result),
            "completed_at": datetime.utcnow().isoformat(),
        }
    except Exception as e:
        logger.error("Seed failed: %s", e)
        _task_status["seed"] = {"status": "failed", "error": str(e)}


def _run_research_single(company_id: int) -> None:
    try:
        from market_research.researcher import research_company
        result = research_company(company_id)
        status = "completed" if "error" not in result else "failed"
        _task_status[f"research_{company_id}"] = {"status": status}
    except Exception as e:
        logger.error("Research %d failed: %s", company_id, e)
        _task_status[f"research_{company_id}"] = {"status": "failed", "error": str(e)}


def _run_research_all() -> None:
    try:
        from market_research.researcher import research_all_companies
        result = research_all_companies()
        _task_status["research_all"] = {
            "status": "completed",
            **result,
            "completed_at": datetime.utcnow().isoformat(),
        }
    except Exception as e:
        logger.error("Research all failed: %s", e)
        _task_status["research_all"] = {"status": "failed", "error": str(e)}
