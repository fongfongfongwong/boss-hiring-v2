"""Market research service – uses LLM (with web search) to research quant/trading companies.

Supports:
1. Seed research – generate a comprehensive list of CN/US quant & trading companies
2. Single company deep-dive – open positions, talent profiles, supplementary info
3. Boss Zhipin resume count snapshot (placeholder for future RPA integration)
"""

from __future__ import annotations

import json
import logging
from datetime import datetime
from typing import Any, List, Optional

from database.db import SessionLocal
from database.models import MarketCompany, MarketCompanySnapshot
from utils.llm_client import llm

logger = logging.getLogger(__name__)


# ── LLM Prompts ──────────────────────────────────────────────────────

SEED_SYSTEM = """你是一名资深量化金融行业分析师。请根据用户要求，列出中国和美国主要的量化交易(Quant Trading)、
自营交易(Proprietary Trading)、量化对冲基金(Quant Hedge Fund)和做市(Market Making)公司。

请以纯 JSON 数组格式回复，每个元素包含：
- name: 公司中文名称（没有则用英文）
- name_en: 公司英文名称
- region: "CN" 或 "US"
- category: "quant" / "prop_trading" / "hedge_fund" / "market_maker" 之一
- website: 公司官网 URL（尽量准确）
- headquarters: 总部所在城市
- description: 一句话简介（50字以内）

要求：
1. 中国公司至少列出 20 家知名量化/交易公司
2. 美国公司至少列出 20 家知名量化/交易公司
3. 涵盖不同细分领域（高频交易、统计套利、CTA、期权做市等）
4. 只回复 JSON 数组，不要包含任何其他文字"""

RESEARCH_SYSTEM = """你是一名量化金融行业猎头分析师。请根据用户提供的公司信息，进行深度调研并返回 JSON。

返回格式：
{
  "open_positions": [
    {"title": "岗位名称", "level": "Junior/Mid/Senior/VP/Director", "location": "城市", "source": "来源说明"}
  ],
  "talent_profile": "这家公司通常招聘什么样的人才？学历要求、技能偏好、经验要求等，用2-3段中文概述",
  "supplementary_info": "公司最近的重要新闻、业务动态、规模变化、融资信息等，用2-3段中文概述",
  "estimated_headcount": "估计员工规模（如：200-500人）",
  "tech_stack": ["主要使用的技术栈"],
  "hiring_trend": "up / stable / down"
}

要求：
1. 信息尽量基于你的知识库中的真实数据
2. 岗位信息尽量具体真实
3. 人才画像要详细实用
4. 所有文字用中文回复
5. 只返回 JSON，不要其他文字"""

MARKET_SUMMARY_SYSTEM = """你是一名量化金融行业分析师。请根据以下公司数据，生成一份简洁的市场概览报告。

报告要求：
1. 中国量化市场概况（招聘趋势、热门岗位、人才需求）
2. 美国量化市场概况（招聘趋势、热门岗位、人才需求）
3. 关键洞察（3-5条）
4. 用中文回复，Markdown 格式"""


# ── Service Functions ────────────────────────────────────────────────

def seed_companies() -> List[dict]:
    """Use LLM to generate a seed list of quant/trading companies."""
    logger.info("Seeding market companies via LLM...")

    result = llm.chat_json(
        SEED_SYSTEM,
        "请列出中国和美国主要的量化交易和量化金融公司。",
        temperature=0.4,
        max_tokens=8000,
    )

    if isinstance(result, dict) and "error" in result:
        logger.error("Failed to seed companies: %s", result.get("raw", "")[:300])
        return []

    # Handle if the LLM wraps the array in an object
    companies = result if isinstance(result, list) else result.get("companies", [])

    db = SessionLocal()
    saved = []
    try:
        for c in companies:
            if not isinstance(c, dict) or not c.get("name"):
                continue

            # Skip duplicates
            existing = db.query(MarketCompany).filter(
                MarketCompany.name == c["name"]
            ).first()
            if existing:
                continue

            company = MarketCompany(
                name=c.get("name", ""),
                name_en=c.get("name_en", ""),
                region=c.get("region", "CN"),
                category=c.get("category", "quant"),
                website=c.get("website", ""),
                headquarters=c.get("headquarters", ""),
                description=c.get("description", ""),
            )
            db.add(company)
            saved.append(c)

        db.commit()
        logger.info("Seeded %d new companies", len(saved))
    finally:
        db.close()

    return saved


def research_company(company_id: int) -> dict:
    """Deep-research a single company using LLM."""
    db = SessionLocal()
    try:
        company = db.query(MarketCompany).filter(MarketCompany.id == company_id).first()
        if not company:
            return {"error": "Company not found"}

        prompt = f"""请调研以下公司：
公司名称: {company.name}
英文名称: {company.name_en}
地区: {company.region}
类型: {company.category}
官网: {company.website}
总部: {company.headquarters}
简介: {company.description}

请返回该公司的招聘岗位、人才画像和最新动态信息。"""

        result = llm.chat_json(
            RESEARCH_SYSTEM,
            prompt,
            temperature=0.4,
            max_tokens=4000,
        )

        if isinstance(result, dict) and "error" not in result:
            positions = result.get("open_positions", [])
            company.open_positions_json = json.dumps(positions, ensure_ascii=False)
            company.talent_profile = result.get("talent_profile", "")
            company.supplementary_info = result.get("supplementary_info", "")
            company.last_researched_at = datetime.utcnow()

            # Create snapshot
            today = datetime.utcnow().strftime("%Y-%m-%d")
            snapshot = MarketCompanySnapshot(
                company_id=company.id,
                snapshot_date=today,
                open_position_count=len(positions),
                boss_resume_count=company.boss_resume_count,
            )
            db.add(snapshot)
            db.commit()

            logger.info("Researched company %s: %d positions found", company.name, len(positions))
            return result

        return {"error": "LLM research failed", "raw": str(result)}
    finally:
        db.close()


def research_all_companies() -> dict:
    """Research all tracked companies (batch operation)."""
    db = SessionLocal()
    try:
        companies = db.query(MarketCompany).all()
        total = len(companies)
    finally:
        db.close()

    success = 0
    failed = 0
    for c in companies:
        try:
            result = research_company(c.id)
            if "error" not in result:
                success += 1
            else:
                failed += 1
        except Exception as e:
            logger.error("Failed to research %s: %s", c.name, e)
            failed += 1

    return {"total": total, "success": success, "failed": failed}


def generate_market_summary() -> str:
    """Generate an overall market summary report using LLM."""
    db = SessionLocal()
    try:
        companies = db.query(MarketCompany).all()
        if not companies:
            return "暂无公司数据，请先执行市场调研。"

        company_data = []
        for c in companies:
            positions = json.loads(c.open_positions_json) if c.open_positions_json else []
            company_data.append({
                "name": c.name,
                "region": c.region,
                "category": c.category,
                "open_positions": len(positions),
                "talent_profile": (c.talent_profile or "")[:200],
                "boss_resume_count": c.boss_resume_count,
            })
    finally:
        db.close()

    prompt = f"""以下是我们追踪的量化/交易公司数据：

{json.dumps(company_data, ensure_ascii=False, indent=2)}

请生成市场概览报告。"""

    return llm.chat(
        MARKET_SUMMARY_SYSTEM,
        prompt,
        temperature=0.5,
        max_tokens=4000,
    )
