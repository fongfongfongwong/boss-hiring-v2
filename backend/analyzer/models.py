"""Pydantic models for the Position Analyzer output."""

from __future__ import annotations

from pydantic import BaseModel, Field


class JobDescription(BaseModel):
    """AI-generated Job Description."""

    title: str = ""
    responsibilities: list[str] = Field(default_factory=list)
    requirements: list[str] = Field(default_factory=list)
    preferred: list[str] = Field(default_factory=list)
    skills: list[str] = Field(default_factory=list)
    summary: str = ""


class KeywordMatrix(BaseModel):
    """Search keyword matrix for Boss Zhipin candidate search."""

    primary_keywords: list[str] = Field(default_factory=list)
    skill_keywords: list[str] = Field(default_factory=list)
    domain_keywords: list[str] = Field(default_factory=list)
    education_keywords: list[str] = Field(default_factory=list)


class Filters(BaseModel):
    """Hard filters for candidate screening."""

    min_experience_years: int = 0
    min_education: str = "本科"
    preferred_education: str = "硕士"
    must_have_skills: list[str] = Field(default_factory=list)
    nice_to_have_skills: list[str] = Field(default_factory=list)


class ScoreCard(BaseModel):
    """Scoring rubric for evaluating candidates against the position."""

    skill_match_criteria: str = ""
    experience_criteria: str = ""
    education_criteria: str = ""
    project_criteria: str = ""
    overall_criteria: str = ""


class PositionAnalysis(BaseModel):
    """Complete output from the Position Analyzer."""

    jd: JobDescription = Field(default_factory=JobDescription)
    keywords: KeywordMatrix = Field(default_factory=KeywordMatrix)
    filters: Filters = Field(default_factory=Filters)
    scorecard: ScoreCard = Field(default_factory=ScoreCard)
