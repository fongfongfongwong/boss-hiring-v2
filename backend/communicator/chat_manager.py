"""Multi-turn chat management.

Handles follow-up conversations, reply analysis, and resume requests.
"""

from __future__ import annotations

import logging
from typing import Any

from communicator.prompts import (
    FOLLOWUP_SYSTEM,
    FOLLOWUP_USER,
    REPLY_ANALYSIS_SYSTEM,
    REPLY_ANALYSIS_USER,
)
from utils.llm_client import llm

logger = logging.getLogger(__name__)


def analyze_reply(
    message: str,
    chat_history: str,
) -> dict[str, Any]:
    """Analyze a candidate's reply to determine intent.

    Returns dict with keys: intent, has_resume_attachment, has_contact_info,
    extracted_contact, summary.
    """
    user_prompt = REPLY_ANALYSIS_USER.format(
        message=message,
        chat_history=chat_history,
    )

    result = llm.chat_json(
        system_prompt=REPLY_ANALYSIS_SYSTEM,
        user_prompt=user_prompt,
        temperature=0.2,
    )

    logger.info("Reply analysis – intent: %s", result.get("intent", "unknown"))
    return result


def generate_followup(
    jd_summary: str,
    chat_history: str,
    latest_message: str,
) -> str:
    """Generate a follow-up message in response to a candidate's reply."""
    user_prompt = FOLLOWUP_USER.format(
        jd_summary=jd_summary,
        chat_history=chat_history,
        latest_message=latest_message,
    )

    reply = llm.chat(
        system_prompt=FOLLOWUP_SYSTEM,
        user_prompt=user_prompt,
        temperature=0.7,
        max_tokens=300,
    )

    logger.info("Generated follow-up (%d chars)", len(reply))
    return reply
