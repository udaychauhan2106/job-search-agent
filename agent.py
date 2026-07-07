"""
Core agent logic for the Job Search Agent.

This module builds and runs the LangChain agent. It has no CLI or UI code -
streamlit_app.py imports build_agent() and search_jobs_for_resume() directly.
"""

from langchain.agents import create_agent
from langchain_core.messages import HumanMessage
from langchain_google_genai import ChatGoogleGenerativeAI

from schemas import JobSearchResult
from tools import get_job_page_content, search_jobs

SYSTEM_INSTRUCTIONS = """You are a job search assistant helping a candidate find roles that fit their resume.

You have two tools:
1. search_jobs - search the web for job postings matching a role and location.
2. get_job_page_content - read the full text of a specific job posting URL.

Your process:
1. Call search_jobs to find candidate postings for the requested role and location.
2. For each promising result, call get_job_page_content to read the actual posting.
3. IMPORTANT - handling extraction failures: many job boards (LinkedIn, Indeed,
   etc.) block automated page reading. If get_job_page_content returns a string
   starting with "EXTRACTION_FAILED", do NOT drop that posting from your results.
   Instead, fall back to reasoning from the snippet you already have for that
   posting from search_jobs, and lower your confidence accordingly - mention in
   the reasoning field that the assessment is based on limited information
   (e.g. "Based on listing snippet only; full posting could not be read.").
4. Never return an empty match list just because some or all postings could not
   be fully read. Always return your best-effort ranked assessment using
   whatever information you do have (title, company, snippet, and/or full text).
5. Compare each posting's requirements against the candidate's resume below.
6. Return a JobSearchResult: a ranked list of JobMatch entries (highest match_score
   first), each with matching_skills, missing_skills, and a short reasoning string,
   plus an overall summary. If most postings could only be assessed from snippets,
   say so plainly in the summary.

Be honest in scoring - do not inflate match_score. A missing core requirement
(e.g. required years of experience, a required language/framework) should
meaningfully lower the score.
"""


def build_agent():
    llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash")
    tools = [search_jobs, get_job_page_content]
    return create_agent(model=llm, tools=tools, response_format=JobSearchResult)


def search_jobs_for_resume(
    agent, resume_text: str, role: str, location: str, max_results: int
) -> JobSearchResult:
    """Run the agent once and return its structured JobSearchResult."""
    user_prompt = (
        f"{SYSTEM_INSTRUCTIONS}\n\n"
        f"Role: {role}\n"
        f"Location: {location}\n"
        f"Max results to consider: {max_results}\n\n"
        f"Candidate resume:\n{resume_text}\n\n"
        f"Find and score job postings for this role and location against this resume."
    )

    result = agent.invoke({"messages": [HumanMessage(content=user_prompt)]})
    structured = result.get("structured_response")

    if structured is None:
        raise RuntimeError(
            "Agent did not return structured output. Raw result: " + str(result)
        )

    return structured
