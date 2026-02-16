"""AI-powered multi-dimensional resume scoring engine."""

from __future__ import annotations

import json
import logging

from resume_analysis.models import ExtractedResume, ResumeScore
from resume_analysis.prompts import SCORE_SYSTEM, SCORE_USER
from utils.config import get_scoring_weights, get_qualified_threshold
from utils.llm_client import llm

logger = logging.getLogger(__name__)


def score_resume(
    extracted: ExtractedResume,
    jd_summary: str,
    scorecard: str,
) -> ResumeScore:
    """Score an extracted resume against a position.

    Parameters
    ----------
    extracted:
        Structured resume data from the extractor.
    jd_summary:
        Text summary of the job description.
    scorecard:
        Scoring rubric text from the position analysis.
    """
    user_prompt = SCORE_USER.format(
        jd_summary=jd_summary,
        scorecard=scorecard,
        extracted_resume=extracted.model_dump_json(indent=2),
    )

    data = llm.chat_json(
        system_prompt=SCORE_SYSTEM,
        user_prompt=user_prompt,
        temperature=0.3,
        max_tokens=2048,
    )

    if "error" in data:
        logger.error("LLM scoring failed: %s", data)
        return ResumeScore()

    try:
        score = ResumeScore.model_validate(data)
    except Exception as exc:
        logger.error("Failed to validate score: %s", exc)
        return ResumeScore()

    # Compute weighted total
    weights = get_scoring_weights()
    score.weighted_total = round(
        score.skill_match * weights.get("skill_match", 0.3)
        + score.experience_relevance * weights.get("experience_relevance", 0.25)
        + score.education_fit * weights.get("education_fit", 0.15)
        + score.project_quality * weights.get("project_quality", 0.2)
        + score.overall_recommendation * weights.get("overall_recommendation", 0.1),
        1,
    )

    threshold = get_qualified_threshold()
    score.is_qualified = score.weighted_total >= threshold

    logger.info(
        "Resume scored: %.1f (qualified=%s) – %s",
        score.weighted_total,
        score.is_qualified,
        extracted.name,
    )
    return score


def generate_report(extracted: ExtractedResume, score: ResumeScore) -> str:
    """Generate a Markdown analysis report for a scored resume."""
    lines = [
        f"# 简历评分报告 – {extracted.name}",
        "",
        f"**综合评分: {score.weighted_total:.1f} / 100** {'✅ 达标' if score.is_qualified else '❌ 未达标'}",
        "",
        "## 评分明细",
        "",
        f"| 维度 | 分数 |",
        f"|------|------|",
        f"| 技能匹配 | {score.skill_match} |",
        f"| 经验相关性 | {score.experience_relevance} |",
        f"| 学历契合度 | {score.education_fit} |",
        f"| 项目质量 | {score.project_quality} |",
        f"| 综合推荐度 | {score.overall_recommendation} |",
        "",
        "## 亮点",
        "",
    ]
    for s in score.strengths:
        lines.append(f"- {s}")

    lines.extend(["", "## 不足", ""])
    for w in score.weaknesses:
        lines.append(f"- {w}")

    lines.extend(["", "## 评分理由", "", score.reasoning, ""])

    if extracted.skills:
        lines.extend(["## 技能清单", ""])
        lines.append(", ".join(extracted.skills))
        lines.append("")

    return "\n".join(lines)
