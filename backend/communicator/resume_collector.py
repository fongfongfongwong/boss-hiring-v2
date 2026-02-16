"""Resume download / collection logic.

Downloads resume attachments from Boss Zhipin chat and saves them locally.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional

import httpx
from playwright.async_api import Page

from rpa.page_actions import check_for_resume_attachment

logger = logging.getLogger(__name__)

RESUME_DIR = Path(__file__).parent.parent / "data" / "resumes"


async def collect_resume(
    page: Page,
    candidate_name: str,
    position_title: str,
) -> Optional[str]:
    """Check for and download a resume attachment from the current chat.

    Returns the local file path if successful, None otherwise.
    """
    url = await check_for_resume_attachment(page)
    if not url:
        logger.info("No resume attachment found for %s", candidate_name)
        return None

    # Ensure directory exists
    safe_position = position_title.replace(" ", "_").replace("/", "_")
    save_dir = RESUME_DIR / safe_position
    save_dir.mkdir(parents=True, exist_ok=True)

    # Determine filename
    safe_name = candidate_name.replace(" ", "_").replace("/", "_")
    ext = ".pdf"
    if ".doc" in url.lower():
        ext = ".docx"
    filename = f"{safe_name}{ext}"
    filepath = save_dir / filename

    try:
        # Try downloading via the browser context cookies
        cookies = await page.context.cookies()
        cookie_header = "; ".join(f"{c['name']}={c['value']}" for c in cookies)

        async with httpx.AsyncClient() as client:
            resp = await client.get(
                url if url.startswith("http") else f"https://www.zhipin.com{url}",
                headers={
                    "Cookie": cookie_header,
                    "Referer": "https://www.zhipin.com/",
                    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                },
                follow_redirects=True,
                timeout=30.0,
            )
            resp.raise_for_status()

        filepath.write_bytes(resp.content)
        logger.info("Resume downloaded: %s (%d bytes)", filepath, len(resp.content))
        return str(filepath)

    except Exception as e:
        logger.error("Failed to download resume for %s: %s", candidate_name, e)
        return None
