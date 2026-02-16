"""Module 2 – RPA Browser Engine.

Manages the lifecycle of a real Chrome browser instance connected via CDP.
Key design: we launch Chrome with a persistent user-data-dir so that all
cookies, login sessions, and browser fingerprints are genuine – making it
indistinguishable from a human user to Boss Zhipin's anti-bot system.
"""

from __future__ import annotations

import asyncio
import logging
import platform
import shutil
import subprocess
from pathlib import Path
from typing import Optional

from playwright.async_api import (
    Browser,
    BrowserContext,
    Page,
    Playwright,
    async_playwright,
)

from utils.config import get_config

logger = logging.getLogger(__name__)


def _detect_chrome_path() -> str:
    """Auto-detect the Chrome / Chromium executable on the current OS."""
    system = platform.system()
    candidates: list[str] = []

    if system == "Darwin":
        candidates = [
            "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
            "/Applications/Chromium.app/Contents/MacOS/Chromium",
        ]
    elif system == "Linux":
        candidates = [
            "google-chrome",
            "google-chrome-stable",
            "chromium-browser",
            "chromium",
        ]
    elif system == "Windows":
        candidates = [
            r"C:\Program Files\Google\Chrome\Application\chrome.exe",
            r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        ]

    for path in candidates:
        if Path(path).exists() or shutil.which(path):
            return path

    raise FileNotFoundError(
        "Chrome not found. Please set browser.chrome_path in config.yaml"
    )


class BrowserEngine:
    """Manages a real Chrome instance and Playwright CDP connection."""

    def __init__(self) -> None:
        cfg = get_config().get("browser", {})
        self._chrome_path: str = cfg.get("chrome_path") or ""
        self._profile_path: str = cfg.get(
            "profile_path", "./data/chrome_profile"
        )
        self._debug_port: int = cfg.get("debug_port", 9222)

        self._process: Optional[subprocess.Popen] = None  # type: ignore[type-arg]
        self._playwright: Optional[Playwright] = None
        self._browser: Optional[Browser] = None
        self._context: Optional[BrowserContext] = None

    async def launch(self) -> Page:
        """Launch Chrome with a persistent profile (preserves login session).

        Returns the first available page.
        """
        chrome = self._chrome_path if self._chrome_path else None
        if not chrome:
            try:
                chrome = _detect_chrome_path()
            except FileNotFoundError:
                chrome = None  # Let Playwright use its bundled Chromium

        profile = str(Path(self._profile_path).resolve())
        Path(profile).mkdir(parents=True, exist_ok=True)

        logger.info("Launching Chrome with persistent context (profile=%s)", profile)

        self._playwright = await async_playwright().start()
        self._context = await self._playwright.chromium.launch_persistent_context(
            user_data_dir=profile,
            headless=False,
            executable_path=chrome,
            args=["--no-first-run", "--no-default-browser-check"],
            viewport={"width": 1280, "height": 800},
        )

        pages = self._context.pages
        if pages:
            page = pages[0]
        else:
            page = await self._context.new_page()

        logger.info("Browser launched with persistent context – ready")
        return page

    async def new_page(self) -> Page:
        """Open a new tab in the existing context."""
        if not self._context:
            raise RuntimeError("Browser not launched – call launch() first")
        return await self._context.new_page()

    async def close(self) -> None:
        """Gracefully shut down the browser and Playwright."""
        if self._browser:
            try:
                await self._browser.close()
            except Exception:
                pass
        if self._playwright:
            await self._playwright.stop()
        if self._process:
            self._process.terminate()
            self._process.wait(timeout=5)
        logger.info("Browser engine shut down")

    @property
    def context(self) -> Optional[BrowserContext]:
        return self._context
