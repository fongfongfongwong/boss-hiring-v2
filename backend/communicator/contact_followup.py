"""Module 5 – Contact follow-up.

For candidates who pass the resume scoring threshold, automatically
initiate follow-up conversations to obtain their WeChat or phone number.
"""

from __future__ import annotations

import logging
from typing import Any

from communicator.contact_extractor import extract_contact_info
from communicator.prompts import CONTACT_REQUEST_SYSTEM, CONTACT_REQUEST_USER
from utils.config import get_communication_config
from utils.llm_client import llm

logger = logging.getLogger(__name__)


def generate_contact_request(
    jd_summary: str,
    candidate_profile: str,
    chat_history: str,
    attempt: int = 1,
) -> str:
    """Generate a message requesting the candidate's contact info.

    Parameters
    ----------
    attempt:
        The Nth attempt at requesting contact info (1, 2, or 3).
    """
    cfg = get_communication_config()

    user_prompt = CONTACT_REQUEST_USER.format(
        jd_summary=jd_summary,
        candidate_profile=candidate_profile,
        chat_history=chat_history,
        recruiter_wechat=cfg.get("recruiter_wechat", ""),
        recruiter_email=cfg.get("recruiter_email", ""),
        attempt=attempt,
    )

    message = llm.chat(
        system_prompt=CONTACT_REQUEST_SYSTEM,
        user_prompt=user_prompt,
        temperature=0.7,
        max_tokens=200,
    )

    logger.info("Generated contact request (attempt %d): %d chars", attempt, len(message))
    return message


def process_contact_reply(message: str) -> dict[str, Any]:
    """Analyze a candidate's reply to a contact request.

    Returns extracted contact info and whether we got what we needed.
    """
    contact = extract_contact_info(message)

    has_contact = bool(contact.get("wechat") or contact.get("phone") or contact.get("email"))

    return {
        "has_contact": has_contact,
        **contact,
    }
