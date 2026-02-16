"""Auto-greeting generator.

Uses LLM to craft personalized greeting messages for candidates.
"""

from __future__ import annotations

import logging

from communicator.prompts import GREETING_SYSTEM, GREETING_USER
from utils.llm_client import llm

logger = logging.getLogger(__name__)


def generate_greeting(jd_summary: str, candidate_profile: str) -> str:
    """Generate a personalized greeting message for a candidate."""
    user_prompt = GREETING_USER.format(
        jd_summary=jd_summary,
        candidate_profile=candidate_profile,
    )

    greeting = llm.chat(
        system_prompt=GREETING_SYSTEM,
        user_prompt=user_prompt,
        temperature=0.7,
        max_tokens=300,
    )

    logger.info("Generated greeting (%d chars)", len(greeting))
    return greeting
