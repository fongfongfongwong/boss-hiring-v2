"""Main entry point – CLI commands for the recruitment system."""

from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path

import typer
import uvicorn
from rich.console import Console
from rich.table import Table

# Ensure the backend directory is in sys.path
sys.path.insert(0, str(Path(__file__).parent))

app = typer.Typer(
    name="boss-recruiter",
    help="Boss 直聘自动化招聘系统",
)
console = Console()


@app.command()
def serve(
    host: str = typer.Option("0.0.0.0", help="Bind host"),
    port: int = typer.Option(8000, help="Bind port"),
    dev: bool = typer.Option(False, help="Development mode with auto-reload"),
) -> None:
    """Start the web server (API + frontend)."""
    from utils.logger import setup_logging
    setup_logging()

    console.print(f"[bold green]Starting server on http://{host}:{port}[/bold green]")
    console.print("Open in browser to access the recruitment dashboard.")

    uvicorn.run(
        "web.app:create_app",
        factory=True,
        host=host,
        port=port,
        reload=dev,
        log_level="info",
    )


@app.command()
def setup() -> None:
    """Launch browser for initial Boss Zhipin login."""
    from utils.logger import setup_logging
    setup_logging()

    console.print("[bold]Launching Chrome for Boss Zhipin login...[/bold]")
    console.print("Please log in to your Boss Zhipin recruiter account.")
    console.print("After logging in, come back to this terminal.\n")

    async def _setup():
        from playwright.async_api import async_playwright
        from utils.config import get_config

        cfg = get_config().get("browser", {})
        chrome_path = cfg.get("chrome_path", "")

        pw = await async_playwright().start()
        ctx = await pw.chromium.launch_persistent_context(
            user_data_dir="./data/chrome_profile_pw",
            headless=False,
            executable_path=chrome_path if chrome_path else None,
            args=["--no-first-run", "--no-default-browser-check"],
            viewport={"width": 1280, "height": 800},
        )
        page = ctx.pages[0] if ctx.pages else await ctx.new_page()
        await page.goto("https://www.zhipin.com/web/boss/recommend")

        console.print(f"[green]Chrome opened: {page.url}[/green]")
        console.print("[bold yellow]Please log in in the Chrome window.[/bold yellow]")
        console.print("[bold yellow]The browser will stay open for 5 minutes.[/bold yellow]")
        console.print("[bold yellow]Login session is auto-saved when you close the browser or time is up.[/bold yellow]\n")

        # Wait for the page/browser to be closed by user, or timeout after 5 min
        try:
            for _ in range(300):
                await asyncio.sleep(1)
        except (KeyboardInterrupt, asyncio.CancelledError):
            pass

        console.print("\nSaving session...")
        await ctx.close()
        await pw.stop()

    asyncio.run(_setup())
    console.print("[bold green]Session saved! You can now start recruiting.[/bold green]")


@app.command()
def analyze(
    title: str = typer.Argument(..., help="Position title, e.g. 'Quant Trader'"),
    description: str = typer.Option("", help="Additional description"),
) -> None:
    """Analyze a position and generate JD + keywords."""
    from utils.logger import setup_logging
    setup_logging()

    from analyzer.position_analyzer import analyze_position

    console.print(f"[bold]Analyzing position: {title}[/bold]")

    analysis = analyze_position(title, description)

    console.print("\n[bold green]== Job Description ==[/bold green]")
    console.print(f"Title: {analysis.jd.title}")
    console.print(f"Summary: {analysis.jd.summary}")
    console.print(f"\nResponsibilities:")
    for r in analysis.jd.responsibilities:
        console.print(f"  - {r}")
    console.print(f"\nRequirements:")
    for r in analysis.jd.requirements:
        console.print(f"  - {r}")

    console.print("\n[bold green]== Keywords ==[/bold green]")
    console.print(f"Primary: {', '.join(analysis.keywords.primary_keywords)}")
    console.print(f"Skills: {', '.join(analysis.keywords.skill_keywords)}")
    console.print(f"Domain: {', '.join(analysis.keywords.domain_keywords)}")

    console.print("\n[bold green]== Filters ==[/bold green]")
    console.print(f"Min Experience: {analysis.filters.min_experience_years} years")
    console.print(f"Must-have Skills: {', '.join(analysis.filters.must_have_skills)}")


@app.command()
def status() -> None:
    """Show recruitment status overview."""
    from utils.logger import setup_logging
    setup_logging()

    from database.db import init_db, SessionLocal
    from database.models import Candidate, RecruitTask

    init_db()
    db = SessionLocal()

    tasks = db.query(RecruitTask).order_by(RecruitTask.created_at.desc()).limit(10).all()

    if not tasks:
        console.print("[yellow]No recruitment tasks found. Create one via the Web UI.[/yellow]")
        return

    table = Table(title="Recent Recruitment Tasks")
    table.add_column("ID", style="cyan")
    table.add_column("Position", style="green")
    table.add_column("Status", style="bold")
    table.add_column("Candidates", justify="right")
    table.add_column("Created", style="dim")

    for t in tasks:
        candidate_count = db.query(Candidate).filter(Candidate.task_id == t.id).count()
        table.add_row(
            str(t.id),
            t.position.title if t.position else "?",
            t.status,
            str(candidate_count),
            t.created_at.strftime("%Y-%m-%d %H:%M") if t.created_at else "",
        )

    console.print(table)
    db.close()


if __name__ == "__main__":
    app()
