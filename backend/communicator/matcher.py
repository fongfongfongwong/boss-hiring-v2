"""LLM-based pre-screening matcher.

Evaluates a candidate's Boss Zhipin profile summary against the position
requirements and returns a match score + recommendation.
"""

from __future__ import annotations

import json
import logging
from typing import Any

from communicator.prompts import PRE_MATCH_SYSTEM, PRE_MATCH_USER
from utils.llm_client import llm

logger = logging.getLogger(__name__)


def pre_match_candidate(
    jd_summary: str,
    candidate_profile: str,
) -> dict[str, Any]:
    """Score a candidate against the position using LLM.

    Returns dict with keys: score, match_reasons, concern_reasons, recommendation.
    """
    user_prompt = PRE_MATCH_USER.format(
        jd_summary=jd_summary,
        candidate_profile=candidate_profile,
    )

    result = llm.chat_json(
        system_prompt=PRE_MATCH_SYSTEM,
        user_prompt=user_prompt,
        temperature=0.3,
    )

    score = result.get("score", 0)
    logger.info(
        "Pre-match score: %d – %s",
        score,
        result.get("recommendation", "unknown"),
    )
    return result
