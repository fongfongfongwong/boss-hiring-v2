"""LLM-based structured information extraction from resume text."""

from __future__ import annotations

import logging

from resume_analysis.models import ExtractedResume
from resume_analysis.prompts import EXTRACT_SYSTEM, EXTRACT_USER
from utils.llm_client import llm

logger = logging.getLogger(__name__)


def extract_resume_info(resume_text: str) -> ExtractedResume:
    """Use LLM to extract structured data from raw resume text.

    Returns an ExtractedResume pydantic model.
    """
    if not resume_text.strip():
        logger.warning("Empty resume text – returning empty extraction")
        return ExtractedResume()

    # Truncate very long resumes to stay within token limits
    truncated = resume_text[:8000] if len(resume_text) > 8000 else resume_text

    user_prompt = EXTRACT_USER.format(resume_text=truncated)

    data = llm.chat_json(
        system_prompt=EXTRACT_SYSTEM,
        user_prompt=user_prompt,
        temperature=0.2,
        max_tokens=4096,
    )

    if "error" in data:
        logger.error("LLM extraction failed: %s", data)
        return ExtractedResume()

    try:
        extracted = ExtractedResume.model_validate(data)
    except Exception as exc:
        logger.error("Failed to validate extracted resume: %s", exc)
        return ExtractedResume()

    logger.info(
        "Extracted resume: %s – %d skills, %d work experiences",
        extracted.name,
        len(extracted.skills),
        len(extracted.work_experience),
    )
    return extracted
