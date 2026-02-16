"""Pydantic models for resume analysis results."""

from __future__ import annotations

from pydantic import BaseModel, Field


class ExtractedResume(BaseModel):
    """Structured data extracted from a resume by LLM."""

    name: str = ""
    phone: str = ""
    email: str = ""
    education: list[dict] = Field(default_factory=list)
    work_experience: list[dict] = Field(default_factory=list)
    projects: list[dict] = Field(default_factory=list)
    skills: list[str] = Field(default_factory=list)
    certifications: list[str] = Field(default_factory=list)
    languages: list[str] = Field(default_factory=list)
    summary: str = ""


class ResumeScore(BaseModel):
    """Multi-dimensional AI scoring result."""

    skill_match: int = 0
    experience_relevance: int = 0
    education_fit: int = 0
    project_quality: int = 0
    overall_recommendation: int = 0
    weighted_total: float = 0.0
    is_qualified: bool = False
    strengths: list[str] = Field(default_factory=list)
    weaknesses: list[str] = Field(default_factory=list)
    reasoning: str = ""
