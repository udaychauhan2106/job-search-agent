from typing import List, Optional
from pydantic import BaseModel, Field


class JobMatch(BaseModel):
    """A single job posting scored against the candidate's resume."""

    title: str = Field(description="Job title as listed in the posting")
    company: str = Field(description="Hiring company name")
    url: str = Field(description="Direct URL to the job posting")
    location: Optional[str] = Field(default=None, description="Job location, e.g. 'Remote', 'Bay Area, CA'")
    match_score: int = Field(ge=0, le=100, description="How well the candidate's resume matches this posting, 0-100")
    matching_skills: List[str] = Field(default_factory=list, description="Skills/requirements from the posting the candidate already has")
    missing_skills: List[str] = Field(default_factory=list, description="Skills/requirements from the posting the candidate does not clearly have")
    reasoning: str = Field(description="1-3 sentence explanation of the match score")


class JobSearchResult(BaseModel):
    """Final structured output returned by the agent."""

    matches: List[JobMatch] = Field(default_factory=list, description="Job postings found, sorted by match_score descending")
    summary: str = Field(description="A short overall summary of the search and how the candidate stacks up")
