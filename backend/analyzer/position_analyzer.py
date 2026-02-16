"""Module 1 – Position Analyzer.

Accepts a job title + optional description and uses LLM to produce:
  - Standardized JD
  - Search keyword matrix
  - Candidate filters
  - Scoring rubric (ScoreCard)
"""

from __future__ import annotations

import json
import logging

from analyzer.models import PositionAnalysis
from analyzer.prompts import POSITION_ANALYSIS_SYSTEM, POSITION_ANALYSIS_USER
from utils.llm_client import llm

logger = logging.getLogger(__name__)


def analyze_position(title: str, description: str = "") -> PositionAnalysis:
    """Analyze a position and return structured data.

    Parameters
    ----------
    title:
        The position name, e.g. "Quant Trader".
    description:
        Optional supplementary notes, e.g. "偏高频方向, base 上海".

    Returns
    -------
    PositionAnalysis
        Validated Pydantic model with JD, keywords, filters, scorecard.
    """
    logger.info("Analyzing position: %s", title)

    user_prompt = POSITION_ANALYSIS_USER.format(
        title=title,
        description=description or "无",
    )

    data = llm.chat_json(
        system_prompt=POSITION_ANALYSIS_SYSTEM,
        user_prompt=user_prompt,
        temperature=0.4,
        max_tokens=4096,
    )

    if "error" in data:
        logger.error("LLM analysis failed: %s", data)
        return PositionAnalysis()

    try:
        analysis = PositionAnalysis.model_validate(data)
    except Exception as exc:
        logger.error("Failed to parse analysis result: %s – raw: %s", exc, json.dumps(data, ensure_ascii=False)[:500])
        return PositionAnalysis()

    logger.info(
        "Position analysis complete: %d primary keywords, %d skill keywords",
        len(analysis.keywords.primary_keywords),
        len(analysis.keywords.skill_keywords),
    )
    return analysis
