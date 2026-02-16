"""Human behavior simulation – makes RPA actions look natural.

Techniques used:
  - Bezier-curve mouse movement (not straight lines)
  - Random delays between actions
  - Per-character typing with variable speed
  - Natural scrolling patterns
"""

from __future__ import annotations

import asyncio
import math
import random
from typing import Sequence

from playwright.async_api import Page


async def bezier_mouse_move(
    page: Page,
    start_x: float,
    start_y: float,
    end_x: float,
    end_y: float,
    steps: int = 20,
) -> None:
    """Move the mouse along a cubic Bezier curve from start to end."""
    # Two random control points for a natural arc
    ctrl1_x = start_x + (end_x - start_x) * random.uniform(0.2, 0.4) + random.uniform(-50, 50)
    ctrl1_y = start_y + (end_y - start_y) * random.uniform(0.1, 0.3) + random.uniform(-30, 30)
    ctrl2_x = start_x + (end_x - start_x) * random.uniform(0.6, 0.8) + random.uniform(-50, 50)
    ctrl2_y = start_y + (end_y - start_y) * random.uniform(0.7, 0.9) + random.uniform(-30, 30)

    for i in range(steps + 1):
        t = i / steps
        inv = 1 - t
        x = (
            inv**3 * start_x
            + 3 * inv**2 * t * ctrl1_x
            + 3 * inv * t**2 * ctrl2_x
            + t**3 * end_x
        )
        y = (
            inv**3 * start_y
            + 3 * inv**2 * t * ctrl1_y
            + 3 * inv * t**2 * ctrl2_y
            + t**3 * end_y
        )
        await page.mouse.move(x, y)
        await asyncio.sleep(random.uniform(0.005, 0.02))


async def human_click(page: Page, selector: str) -> None:
    """Click an element with natural mouse movement and timing."""
    element = await page.wait_for_selector(selector, timeout=10_000)
    if not element:
        raise ValueError(f"Element not found: {selector}")

    box = await element.bounding_box()
    if not box:
        # Fallback to simple click
        await element.click()
        return

    # Random point within the element (not dead center)
    target_x = box["x"] + box["width"] * random.uniform(0.25, 0.75)
    target_y = box["y"] + box["height"] * random.uniform(0.25, 0.75)

    # Get current mouse position (approximate from viewport center)
    vp = page.viewport_size or {"width": 1280, "height": 720}
    current_x = random.uniform(vp["width"] * 0.3, vp["width"] * 0.7)
    current_y = random.uniform(vp["height"] * 0.3, vp["height"] * 0.7)

    await bezier_mouse_move(page, current_x, current_y, target_x, target_y)
    await asyncio.sleep(random.uniform(0.05, 0.2))
    await page.mouse.click(target_x, target_y)
    await asyncio.sleep(random.uniform(0.1, 0.3))


async def human_type(page: Page, selector: str, text: str) -> None:
    """Type text character by character with human-like delays."""
    await human_click(page, selector)
    await asyncio.sleep(random.uniform(0.2, 0.5))

    for char in text:
        await page.keyboard.type(char, delay=random.randint(50, 180))
        # Occasional longer pause (simulates thinking)
        if random.random() < 0.05:
            await asyncio.sleep(random.uniform(0.3, 0.8))


async def random_scroll(page: Page, direction: str = "down", distance: int = 0) -> None:
    """Scroll the page naturally."""
    if distance == 0:
        distance = random.randint(200, 600)

    delta = distance if direction == "down" else -distance

    # Scroll in small increments
    remaining = abs(delta)
    sign = 1 if delta > 0 else -1
    while remaining > 0:
        chunk = min(remaining, random.randint(40, 120))
        await page.mouse.wheel(0, chunk * sign)
        remaining -= chunk
        await asyncio.sleep(random.uniform(0.02, 0.08))

    await asyncio.sleep(random.uniform(0.3, 1.0))


async def random_delay(min_sec: float = 2.0, max_sec: float = 8.0) -> None:
    """Wait for a random duration between actions."""
    await asyncio.sleep(random.uniform(min_sec, max_sec))


async def human_wait(seconds: float = 1.0) -> None:
    """Wait with slight jitter."""
    await asyncio.sleep(seconds * random.uniform(0.8, 1.2))
