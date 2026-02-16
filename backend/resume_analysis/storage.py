"""Resume storage – local file management and database persistence."""

from __future__ import annotations

import json
import logging
from datetime import datetime
from pathlib import Path

from sqlalchemy.orm import Session

from database.models import Resume as ResumeModel

logger = logging.getLogger(__name__)


def save_resume_to_db(
    db: Session,
    candidate_id: int,
    file_path: str,
    file_type: str,
    raw_text: str,
    extracted_json: dict,
    score_json: dict,
    weighted_total: float,
    is_qualified: bool,
    analysis_report: str,
) -> ResumeModel:
    """Persist a resume analysis result to the database."""
    resume = ResumeModel(
        candidate_id=candidate_id,
        file_path=file_path,
        file_type=file_type,
        raw_text=raw_text,
        extracted_json=json.dumps(extracted_json, ensure_ascii=False),
        score_json=json.dumps(score_json, ensure_ascii=False),
        weighted_total=weighted_total,
        is_qualified=is_qualified,
        analysis_report=analysis_report,
        scored_at=datetime.utcnow(),
    )
    db.add(resume)
    db.commit()
    db.refresh(resume)
    logger.info("Resume saved to DB: candidate_id=%d, score=%.1f", candidate_id, weighted_total)
    return resume
