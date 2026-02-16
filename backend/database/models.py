"""SQLAlchemy ORM models – 6 core tables."""

from datetime import datetime
from typing import Optional

from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    Boolean,
    Text,
    DateTime,
    ForeignKey,
)
from sqlalchemy.orm import relationship

from database.db import Base


class Position(Base):
    """A job position created via the Web UI task wizard."""

    __tablename__ = "positions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(200), nullable=False, index=True)
    description = Column(Text, default="")
    jd_json = Column(Text, default="{}")
    keywords_json = Column(Text, default="{}")
    scorecard_json = Column(Text, default="{}")
    created_at = Column(DateTime, default=datetime.utcnow)

    tasks = relationship("RecruitTask", back_populates="position")
    candidates = relationship("Candidate", back_populates="position")


class RecruitTask(Base):
    """A recruitment automation task launched from the Web UI."""

    __tablename__ = "recruit_tasks"

    id = Column(Integer, primary_key=True, autoincrement=True)
    position_id = Column(Integer, ForeignKey("positions.id"), nullable=False)
    status = Column(
        String(20), default="pending", index=True
    )  # pending / running / paused / completed / failed
    config_json = Column(Text, default="{}")
    progress_json = Column(Text, default="{}")
    error_message = Column(Text, nullable=True)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    position = relationship("Position", back_populates="tasks")
    candidates = relationship("Candidate", back_populates="task")


class Candidate(Base):
    """A candidate discovered on Boss Zhipin."""

    __tablename__ = "candidates"

    id = Column(Integer, primary_key=True, autoincrement=True)
    task_id = Column(Integer, ForeignKey("recruit_tasks.id"), nullable=False)
    position_id = Column(Integer, ForeignKey("positions.id"), nullable=False)
    boss_id = Column(String(100), default="", index=True)
    name = Column(String(100), default="")
    boss_profile_json = Column(Text, default="{}")
    status = Column(
        String(30), default="found", index=True
    )  # found / greeted / chatting / resume_received / scored / qualified / contact_obtained / rejected / archived
    pre_match_score = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow)

    task = relationship("RecruitTask", back_populates="candidates")
    position = relationship("Position", back_populates="candidates")
    resume = relationship("Resume", back_populates="candidate", uselist=False)
    messages = relationship(
        "ChatMessage", back_populates="candidate", order_by="ChatMessage.created_at"
    )
    contact = relationship("ContactInfo", back_populates="candidate", uselist=False)


class Resume(Base):
    """Parsed resume with AI scoring."""

    __tablename__ = "resumes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    candidate_id = Column(
        Integer, ForeignKey("candidates.id"), nullable=False, unique=True
    )
    file_path = Column(String(500), default="")
    file_type = Column(String(20), default="pdf")
    raw_text = Column(Text, default="")
    extracted_json = Column(Text, default="{}")
    score_json = Column(Text, default="{}")
    weighted_total = Column(Float, default=0.0)
    is_qualified = Column(Boolean, default=False)
    analysis_report = Column(Text, default="")
    scored_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    candidate = relationship("Candidate", back_populates="resume")


class ChatMessage(Base):
    """A single chat message exchanged with a candidate."""

    __tablename__ = "chat_messages"

    id = Column(Integer, primary_key=True, autoincrement=True)
    candidate_id = Column(Integer, ForeignKey("candidates.id"), nullable=False)
    direction = Column(String(10), nullable=False)  # sent / received
    content = Column(Text, default="")
    message_type = Column(
        String(30), default="general"
    )  # greeting / followup / resume_request / contact_request / general
    created_at = Column(DateTime, default=datetime.utcnow)

    candidate = relationship("Candidate", back_populates="messages")


class ContactInfo(Base):
    """Contact information obtained from a qualified candidate."""

    __tablename__ = "contact_info"

    id = Column(Integer, primary_key=True, autoincrement=True)
    candidate_id = Column(
        Integer, ForeignKey("candidates.id"), nullable=False, unique=True
    )
    wechat = Column(String(100), nullable=True)
    phone = Column(String(20), nullable=True)
    email = Column(String(200), nullable=True)
    obtained_at = Column(DateTime, default=datetime.utcnow)

    candidate = relationship("Candidate", back_populates="contact")


class BossAccount(Base):
    """A Boss Zhipin recruiter account with its own browser profile."""

    __tablename__ = "boss_accounts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), default="")
    phone = Column(String(20), default="")
    company = Column(String(200), default="")
    profile_dir = Column(String(500), nullable=False, unique=True)
    is_logged_in = Column(Boolean, default=False)
    last_login_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class MarketCompany(Base):
    """A quant/trading company tracked in the market research board."""

    __tablename__ = "market_companies"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(200), nullable=False, index=True)
    name_en = Column(String(200), default="")
    region = Column(String(20), default="CN")  # CN / US / Global
    category = Column(String(50), default="")  # quant / trading / hedge_fund / prop_trading / market_maker
    website = Column(String(500), default="")
    headquarters = Column(String(200), default="")
    description = Column(Text, default="")
    open_positions_json = Column(Text, default="[]")
    talent_profile = Column(Text, default="")
    supplementary_info = Column(Text, default="")
    boss_resume_count = Column(Integer, default=0)
    last_researched_at = Column(DateTime, nullable=True)
    last_boss_updated_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    snapshots = relationship(
        "MarketCompanySnapshot", back_populates="company",
        order_by="MarketCompanySnapshot.snapshot_date.desc()",
    )


class MarketCompanySnapshot(Base):
    """Daily snapshot of a company's recruitment data for trend tracking."""

    __tablename__ = "market_company_snapshots"

    id = Column(Integer, primary_key=True, autoincrement=True)
    company_id = Column(Integer, ForeignKey("market_companies.id"), nullable=False)
    snapshot_date = Column(String(10), nullable=False)  # YYYY-MM-DD
    boss_resume_count = Column(Integer, default=0)
    open_position_count = Column(Integer, default=0)
    notes = Column(Text, default="")
    created_at = Column(DateTime, default=datetime.utcnow)

    company = relationship("MarketCompany", back_populates="snapshots")
