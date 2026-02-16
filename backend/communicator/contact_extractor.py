"""Contact information extraction using regex + LLM double-check."""

from __future__ import annotations

import re
import logging
from typing import Any, Optional

from utils.llm_client import llm

logger = logging.getLogger(__name__)

# Chinese mobile phone number
PHONE_PATTERN = re.compile(r"1[3-9]\d{9}")
# WeChat ID: starts with a letter, 6-20 chars
WECHAT_PATTERN = re.compile(r"[a-zA-Z][\w\-]{5,19}")
# Email
EMAIL_PATTERN = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")


def _regex_extract(text: str) -> dict[str, Optional[str]]:
    """First pass: regex-based extraction."""
    phone_match = PHONE_PATTERN.search(text)
    email_match = EMAIL_PATTERN.search(text)

    # For WeChat, exclude common false positives
    wechat = None
    for m in WECHAT_PATTERN.finditer(text):
        candidate = m.group()
        # Skip if it looks like a common English word or URL fragment
        if len(candidate) >= 6 and candidate.lower() not in {
            "https", "script", "python", "resume", "please",
            "wechat", "weixin",
        }:
            wechat = candidate
            break

    return {
        "phone": phone_match.group() if phone_match else None,
        "wechat": wechat,
        "email": email_match.group() if email_match else None,
    }


def _llm_extract(text: str) -> dict[str, Optional[str]]:
    """Second pass: LLM-based extraction for ambiguous cases."""
    result = llm.chat_json(
        system_prompt=(
            "从以下文本中提取候选人的联系方式。"
            "以JSON格式回复: {\"wechat\": \"微信号或null\", "
            "\"phone\": \"手机号或null\", \"email\": \"邮箱或null\"}"
            "\n只返回JSON。"
        ),
        user_prompt=text,
        temperature=0.1,
    )
    return {
        "wechat": result.get("wechat"),
        "phone": result.get("phone"),
        "email": result.get("email"),
    }


def extract_contact_info(text: str) -> dict[str, Any]:
    """Extract contact information using regex + LLM double-check.

    Returns dict with keys: wechat, phone, email.
    """
    # First try regex
    regex_result = _regex_extract(text)

    if regex_result["phone"] or regex_result["wechat"] or regex_result["email"]:
        logger.info("Contact extracted via regex: %s", regex_result)
        return regex_result

    # Fall back to LLM
    llm_result = _llm_extract(text)
    if llm_result.get("phone") or llm_result.get("wechat") or llm_result.get("email"):
        logger.info("Contact extracted via LLM: %s", llm_result)
        return llm_result

    return {"wechat": None, "phone": None, "email": None}
