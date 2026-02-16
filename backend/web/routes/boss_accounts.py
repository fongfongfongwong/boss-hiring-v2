"""Boss Zhipin account management API routes.

Supports multiple accounts, each with its own Chrome profile.
Login is triggered via the Web UI — opens a real Chrome window for phone verification.
"""

from __future__ import annotations

import asyncio
import logging
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from database.db import SessionLocal
from database.models import BossAccount
from utils.config import get_config

router = APIRouter(prefix="/api/boss-accounts", tags=["boss-accounts"])
logger = logging.getLogger(__name__)

PROFILES_BASE = Path(__file__).parent.parent.parent / "data" / "boss_profiles"

# Track active login sessions: account_id -> { "pw", "ctx", "page", "task" }
_active_logins: Dict[int, dict] = {}


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ── Request / Response models ────────────────────────────────────────

class AccountCreate(BaseModel):
    name: Optional[str] = ""


class AccountOut(BaseModel):
    id: int
    name: str
    phone: str
    company: str
    is_logged_in: bool
    is_logging_in: bool
    last_login_at: Optional[str]
    created_at: Optional[str]


# ── Endpoints ────────────────────────────────────────────────────────

@router.get("")
def list_accounts(db: Session = Depends(get_db)) -> list[dict[str, Any]]:
    """List all Boss Zhipin accounts."""
    accounts = db.query(BossAccount).order_by(BossAccount.created_at.desc()).all()
    result = []
    for a in accounts:
        result.append({
            "id": a.id,
            "name": a.name or f"账号 {a.id}",
            "phone": a.phone or "",
            "company": a.company or "",
            "is_logged_in": a.is_logged_in,
            "is_logging_in": a.id in _active_logins,
            "last_login_at": a.last_login_at.isoformat() if a.last_login_at else None,
            "created_at": a.created_at.isoformat() if a.created_at else None,
        })
    return result


@router.post("/login")
async def start_login(
    req: AccountCreate,
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """Create a new account (or reuse) and launch Chrome for login.

    Opens a real Chrome window on the server machine.
    The user logs in via phone number on Boss Zhipin.
    The session is auto-detected and saved.
    """
    # Create a new account record
    profile_name = f"account_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
    profile_path = str(PROFILES_BASE / profile_name)
    Path(profile_path).mkdir(parents=True, exist_ok=True)

    account = BossAccount(
        name=req.name or "",
        profile_dir=profile_path,
        is_logged_in=False,
    )
    db.add(account)
    db.commit()
    db.refresh(account)

    # Launch browser in background
    account_id = account.id
    asyncio.create_task(_run_login(account_id, profile_path))

    return {
        "account_id": account_id,
        "status": "launching",
        "message": "正在打开 Chrome 浏览器，请在弹出的窗口中用手机号登录 Boss 直聘...",
    }


@router.post("/{account_id}/relogin")
async def relogin(
    account_id: int,
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """Re-login an existing account (reuse its Chrome profile)."""
    account = db.query(BossAccount).filter(BossAccount.id == account_id).first()
    if not account:
        raise HTTPException(status_code=404, detail="账号不存在")

    if account_id in _active_logins:
        return {"account_id": account_id, "status": "already_logging_in", "message": "该账号正在登录中..."}

    asyncio.create_task(_run_login(account_id, account.profile_dir))
    return {
        "account_id": account_id,
        "status": "launching",
        "message": "正在打开 Chrome 浏览器，请在弹出的窗口中重新登录...",
    }


@router.get("/{account_id}/status")
def get_login_status(
    account_id: int,
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """Check the login status of an account."""
    account = db.query(BossAccount).filter(BossAccount.id == account_id).first()
    if not account:
        raise HTTPException(status_code=404, detail="账号不存在")

    is_logging_in = account_id in _active_logins
    login_info = _active_logins.get(account_id, {})

    return {
        "account_id": account_id,
        "is_logged_in": account.is_logged_in,
        "is_logging_in": is_logging_in,
        "name": account.name or f"账号 {account.id}",
        "phone": account.phone or "",
        "company": account.company or "",
        "step": login_info.get("step", ""),
    }


@router.delete("/{account_id}")
def delete_account(
    account_id: int,
    db: Session = Depends(get_db),
) -> dict[str, str]:
    """Delete an account and its Chrome profile data."""
    account = db.query(BossAccount).filter(BossAccount.id == account_id).first()
    if not account:
        raise HTTPException(status_code=404, detail="账号不存在")

    # Cancel active login if any
    if account_id in _active_logins:
        _cancel_login(account_id)

    # Remove Chrome profile directory
    profile = Path(account.profile_dir)
    if profile.exists():
        shutil.rmtree(profile, ignore_errors=True)

    db.delete(account)
    db.commit()

    return {"status": "deleted"}


# ── Browser login logic ──────────────────────────────────────────────

async def _run_login(account_id: int, profile_path: str) -> None:
    """Launch Chrome, navigate to Boss Zhipin, and monitor for login success."""
    from playwright.async_api import async_playwright

    cfg = get_config().get("browser", {})
    chrome_path = cfg.get("chrome_path", "")

    pw = None
    ctx = None
    try:
        _active_logins[account_id] = {"step": "launching"}

        pw = await async_playwright().start()
        ctx = await pw.chromium.launch_persistent_context(
            user_data_dir=profile_path,
            headless=False,
            executable_path=chrome_path if chrome_path else None,
            args=["--no-first-run", "--no-default-browser-check"],
            viewport={"width": 1280, "height": 800},
        )

        page = ctx.pages[0] if ctx.pages else await ctx.new_page()
        _active_logins[account_id] = {"step": "navigating", "pw": pw, "ctx": ctx}

        await page.goto("https://www.zhipin.com/web/boss/recommend", wait_until="domcontentloaded")
        _active_logins[account_id]["step"] = "waiting_for_login"

        logger.info("Account %d: Chrome opened, waiting for login...", account_id)

        # Poll for login success (max 5 minutes)
        logged_in = False
        account_name = ""
        account_company = ""

        for _ in range(300):
            await asyncio.sleep(1)

            # Check if browser/page was closed by user
            try:
                url = page.url
            except Exception:
                logger.info("Account %d: Browser closed by user", account_id)
                break

            # Detect login success: look for recruiter-specific elements
            try:
                # On Boss Zhipin recruiter backend, after login the URL contains /boss/
                # and there should be user info visible
                if "/login" not in url and "/web/boss" in url:
                    # Try to extract account name from the page
                    try:
                        name_el = await page.query_selector(".nav-figure .nav-name, .user-name, .boss-name")
                        if name_el:
                            account_name = (await name_el.inner_text()).strip()
                    except Exception:
                        pass

                    try:
                        company_el = await page.query_selector(".nav-figure .nav-company, .company-name")
                        if company_el:
                            account_company = (await company_el.inner_text()).strip()
                    except Exception:
                        pass

                    # Check if we see actual recruiter page content
                    has_content = await page.query_selector(".recommend-main, .job-list, .boss-chat, .resume-list")
                    if has_content:
                        logged_in = True
                        _active_logins[account_id]["step"] = "login_success"
                        logger.info("Account %d: Login detected! name=%s", account_id, account_name)
                        # Give a moment for the page to fully load
                        await asyncio.sleep(2)
                        break
            except Exception as e:
                logger.debug("Account %d: check error: %s", account_id, e)
                continue

        # Save the result
        _save_login_result(account_id, logged_in, account_name, account_company)

        # Close browser
        try:
            await ctx.close()
        except Exception:
            pass
        try:
            await pw.stop()
        except Exception:
            pass

    except Exception as e:
        logger.error("Account %d: Login error: %s", account_id, e)
        _save_login_result(account_id, False, "", "")
        if ctx:
            try:
                await ctx.close()
            except Exception:
                pass
        if pw:
            try:
                await pw.stop()
            except Exception:
                pass
    finally:
        _active_logins.pop(account_id, None)


def _save_login_result(
    account_id: int,
    logged_in: bool,
    name: str,
    company: str,
) -> None:
    """Persist the login result to the database."""
    db = SessionLocal()
    try:
        account = db.query(BossAccount).filter(BossAccount.id == account_id).first()
        if account:
            account.is_logged_in = logged_in
            if name:
                account.name = name
            if company:
                account.company = company
            if logged_in:
                account.last_login_at = datetime.utcnow()
            if not account.name:
                account.name = f"账号 {account.id}"
            db.commit()
            logger.info(
                "Account %d saved: logged_in=%s, name=%s, company=%s",
                account_id, logged_in, name, company,
            )
    finally:
        db.close()


def _cancel_login(account_id: int) -> None:
    """Cancel an active login session."""
    session = _active_logins.pop(account_id, None)
    if session:
        ctx = session.get("ctx")
        pw = session.get("pw")
        try:
            if ctx:
                asyncio.create_task(ctx.close())
            if pw:
                asyncio.create_task(pw.stop())
        except Exception:
            pass
