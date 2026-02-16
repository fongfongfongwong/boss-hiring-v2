"""Boss Zhipin-specific page actions.

Encapsulates navigation and element interactions on Boss Zhipin's
recruiter-side pages (搜索牛人, 消息列表, etc.).
"""

from __future__ import annotations

import asyncio
import logging
import random
from typing import Any, Optional

from playwright.async_api import Page

from rpa.human_simulator import (
    human_click,
    human_type,
    random_delay,
    random_scroll,
)

logger = logging.getLogger(__name__)

BOSS_BASE_URL = "https://www.zhipin.com"
BOSS_SEARCH_URL = f"{BOSS_BASE_URL}/web/boss/recommend"
BOSS_CHAT_URL = f"{BOSS_BASE_URL}/web/boss/chat"


async def navigate_to_search(page: Page) -> None:
    """Navigate to the recruiter's candidate search page."""
    logger.info("Navigating to candidate search page")
    await page.goto(BOSS_SEARCH_URL, wait_until="networkidle", timeout=30_000)
    await random_delay(1.5, 3.0)


async def search_candidates(page: Page, keyword: str) -> None:
    """Enter a keyword in the search box and submit."""
    logger.info("Searching for candidates with keyword: %s", keyword)

    search_input = (
        'input[placeholder*="搜索"],'
        'input[class*="search"],'
        ".search-input input"
    )
    try:
        await human_click(page, search_input)
        # Clear existing text
        await page.keyboard.press("Meta+a")
        await asyncio.sleep(0.1)
        await page.keyboard.press("Backspace")
        await human_type(page, search_input, keyword)
        await asyncio.sleep(0.3)
        await page.keyboard.press("Enter")
        await random_delay(2.0, 4.0)
    except Exception as e:
        logger.error("Failed to search: %s", e)
        raise


async def get_candidate_cards(page: Page) -> list[dict[str, Any]]:
    """Extract visible candidate cards from the search results page.

    Returns a list of dicts with keys: name, title, company, boss_id, element_selector.
    """
    await random_delay(1.0, 2.0)

    cards = await page.query_selector_all(
        ".card-inner, .recommend-card, .candidate-card, [class*='geek-card']"
    )

    results: list[dict[str, Any]] = []
    for i, card in enumerate(cards):
        try:
            name_el = await card.query_selector(
                ".name, [class*='name'], .geek-name"
            )
            title_el = await card.query_selector(
                ".title, [class*='title'], .geek-title"
            )
            company_el = await card.query_selector(
                ".company, [class*='company']"
            )

            name = (await name_el.inner_text()).strip() if name_el else ""
            title = (await title_el.inner_text()).strip() if title_el else ""
            company = (await company_el.inner_text()).strip() if company_el else ""

            results.append(
                {
                    "name": name,
                    "title": title,
                    "company": company,
                    "card_index": i,
                }
            )
        except Exception as e:
            logger.debug("Error parsing card %d: %s", i, e)
            continue

    logger.info("Found %d candidate cards", len(results))
    return results


async def click_candidate_card(page: Page, card_index: int) -> None:
    """Click on a candidate card to view their profile."""
    cards = await page.query_selector_all(
        ".card-inner, .recommend-card, .candidate-card, [class*='geek-card']"
    )
    if card_index < len(cards):
        await cards[card_index].click()
        await random_delay(1.5, 3.0)


async def get_candidate_profile(page: Page) -> dict[str, Any]:
    """Extract profile details from the candidate detail view."""
    await random_delay(1.0, 2.0)

    profile: dict[str, Any] = {}

    selectors = {
        "name": ".name, .geek-name, [class*='name']",
        "title": ".expect-title, .geek-expect, [class*='expect']",
        "experience": ".work-exp, [class*='experience']",
        "education": ".edu, [class*='education']",
        "skills": ".skill-list, [class*='skill']",
        "description": ".describe, [class*='describe'], .geek-desc",
    }

    for key, selector in selectors.items():
        try:
            el = await page.query_selector(selector)
            if el:
                profile[key] = (await el.inner_text()).strip()
        except Exception:
            pass

    return profile


async def send_greeting(page: Page, message: str) -> bool:
    """Send a greeting message to the candidate.

    Returns True if the message was sent successfully.
    """
    logger.info("Sending greeting message...")

    try:
        # Look for the "打招呼" / "立即沟通" button
        greet_btn = (
            'button:has-text("立即沟通"),'
            'button:has-text("打招呼"),'
            'a:has-text("立即沟通"),'
            '[class*="btn-greet"]'
        )
        await human_click(page, greet_btn)
        await random_delay(1.0, 2.0)

        # Type the greeting in the chat input
        chat_input = (
            'textarea, [contenteditable="true"], .chat-input textarea'
        )
        # Clear default text if any
        input_el = await page.wait_for_selector(chat_input, timeout=5_000)
        if input_el:
            await input_el.click()
            await page.keyboard.press("Meta+a")
            await asyncio.sleep(0.1)

        await human_type(page, chat_input, message)
        await asyncio.sleep(0.3)

        # Click send button
        send_btn = (
            'button:has-text("发送"),'
            '[class*="btn-send"],'
            '.send-btn'
        )
        await human_click(page, send_btn)
        await random_delay(0.5, 1.5)

        logger.info("Greeting sent successfully")
        return True

    except Exception as e:
        logger.error("Failed to send greeting: %s", e)
        return False


async def navigate_to_chat(page: Page) -> None:
    """Navigate to the recruiter's chat/message list."""
    logger.info("Navigating to chat page")
    await page.goto(BOSS_CHAT_URL, wait_until="networkidle", timeout=30_000)
    await random_delay(1.5, 3.0)


async def get_unread_messages(page: Page) -> list[dict[str, Any]]:
    """Get a list of conversations with unread messages."""
    await random_delay(1.0, 2.0)

    conversations: list[dict[str, Any]] = []
    items = await page.query_selector_all(
        ".chat-item, .conversation-item, [class*='msg-item']"
    )

    for item in items:
        try:
            badge = await item.query_selector(".badge, .unread, [class*='unread']")
            if not badge:
                continue

            name_el = await item.query_selector(".name, [class*='name']")
            preview_el = await item.query_selector(".last-msg, [class*='preview']")

            name = (await name_el.inner_text()).strip() if name_el else ""
            preview = (await preview_el.inner_text()).strip() if preview_el else ""

            conversations.append({"name": name, "preview": preview, "element": item})
        except Exception:
            continue

    logger.info("Found %d conversations with unread messages", len(conversations))
    return conversations


async def send_chat_message(page: Page, message: str) -> bool:
    """Send a message in the currently open chat window."""
    try:
        chat_input = 'textarea, [contenteditable="true"], .chat-input textarea'
        await human_type(page, chat_input, message)
        await asyncio.sleep(0.3)

        send_btn = (
            'button:has-text("发送"), [class*="btn-send"], .send-btn'
        )
        await human_click(page, send_btn)
        await random_delay(0.5, 1.5)
        return True
    except Exception as e:
        logger.error("Failed to send chat message: %s", e)
        return False


async def check_for_resume_attachment(page: Page) -> Optional[str]:
    """Check if the candidate has sent a resume attachment in chat.

    Returns the download URL if found, None otherwise.
    """
    attachments = await page.query_selector_all(
        ".file-msg, [class*='attachment'], [class*='resume-file']"
    )
    for att in attachments:
        text = (await att.inner_text()).strip().lower()
        if any(kw in text for kw in ["简历", "resume", ".pdf", ".doc", ".docx"]):
            link = await att.query_selector("a")
            if link:
                href = await link.get_attribute("href")
                return href
    return None


async def scroll_to_load_more(page: Page) -> None:
    """Scroll down to trigger lazy-loading of more candidate cards."""
    await random_scroll(page, direction="down", distance=random.randint(400, 800))
    await random_delay(1.5, 3.0)
