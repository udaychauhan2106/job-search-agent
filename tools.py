import json
import os

from langchain.tools import tool
from tavily import TavilyClient

tavily = TavilyClient(api_key=os.environ.get("TAVILY_API_KEY"))


@tool
def search_jobs(query: str, max_results: int = 5) -> str:
    """
    Search the web for job postings matching a query.

    Args:
        query: A natural-language search query, e.g. "AI Engineer LangChain Bay Area remote".
        max_results: Maximum number of search results to return (default 5).

    Returns:
        JSON string of search results, each with a title, url, and content snippet.
        The snippet may be the only usable content if the page later blocks extraction.
    """
    print(f"[tool] search_jobs: {query!r} (max_results={max_results})")
    results = tavily.search(query=query, max_results=max_results, search_depth="advanced")
    trimmed = [
        {
            "title": r.get("title"),
            "url": r.get("url"),
            "snippet": (r.get("content") or "")[:1200],
        }
        for r in results.get("results", [])
    ]
    return json.dumps(trimmed)


@tool
def get_job_page_content(url: str) -> str:
    """
    Fetch and extract the main text content of a job posting page.

    Use this after search_jobs to read the full posting (responsibilities,
    requirements, etc.) before scoring it against the candidate's resume.

    If this returns "EXTRACTION_FAILED", the page could not be read (many
    job boards block scraping) - fall back to the snippet already returned
    by search_jobs for this posting instead of skipping it entirely.

    Args:
        url: The direct URL of the job posting to read.

    Returns:
        Extracted plain-text content of the page, truncated to a safe length,
        or "EXTRACTION_FAILED: <reason>" if the page could not be read.
    """
    print(f"[tool] get_job_page_content: {url}")
    try:
        extracted = tavily.extract(urls=[url])
        results = extracted.get("results", [])
        if not results:
            return "EXTRACTION_FAILED: no content returned for this URL."
        raw_content = (results[0].get("raw_content") or "").strip()
        if len(raw_content) < 100:
            return "EXTRACTION_FAILED: page returned little or no readable content (likely blocked)."
        return raw_content[:6000]
    except Exception as exc:  # noqa: BLE001
        return f"EXTRACTION_FAILED: {exc}"
