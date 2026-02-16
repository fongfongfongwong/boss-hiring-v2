"""Database connection and session management."""

from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session, DeclarativeBase

DATA_DIR = Path(__file__).parent.parent / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)
DB_PATH = DATA_DIR / "boss_recruiter.db"

engine = create_engine(
    f"sqlite:///{DB_PATH}",
    echo=False,
    connect_args={"check_same_thread": False},
)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


class Base(DeclarativeBase):
    pass


def init_db() -> None:
    """Create all tables if they don't exist."""
    from database.models import (  # noqa: F401 – ensure models are registered
        Position,
        RecruitTask,
        Candidate,
        Resume,
        ChatMessage,
        ContactInfo,
        BossAccount,
        MarketCompany,
        MarketCompanySnapshot,
    )
    Base.metadata.create_all(bind=engine)


def get_db() -> Session:  # type: ignore[misc]
    """Dependency-injection helper for FastAPI routes."""
    db = SessionLocal()
    try:
        yield db  # type: ignore[misc]
    finally:
        db.close()
