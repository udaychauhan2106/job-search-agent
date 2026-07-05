# Job Search Agent

An autonomous LangChain agent, with a Streamlit UI, that searches the web for
job postings, reads the full content of each posting, and scores it against
a candidate's resume - returning a ranked, structured list of matches with
reasoning.

## Problem

Job boards return dozens of postings for any given search, but skimming
titles and snippets does not tell you how well a posting actually matches
your skills. This agent automates that judgment: it searches, reads each
posting in full, and produces an honest match score with specific reasoning
- not just a keyword count.

## How it works

The agent plans and executes a multi-step tool-calling loop rather than a
single hardcoded prompt chain:

1. **search_jobs** - searches the web (via Tavily) for postings matching a
   role and location.
2. **get_job_page_content** - for each promising result, fetches and
   extracts the actual page content, since a search snippet alone is not
   enough to judge fit.
3. **Structured scoring** - the agent compares each posting's real
   requirements against the candidate's resume and returns a
   `JobSearchResult` (a Pydantic schema) containing, per posting: a
   `match_score` (0-100), the skills that matched, the skills that are
   missing, and a short reasoning string - plus an overall summary.

```
User (resume, role, location) via Streamlit UI
        |
        v
   LangChain agent (Gemini 2.5 Flash)
        |
        |--> search_jobs(query) ---------> list of candidate postings
        |
        |--> get_job_page_content(url) --> full text per posting
        |
        v
 Structured output: JobSearchResult
   (ranked JobMatch list + summary) --> rendered in Streamlit
```

## Tech stack

- **LangChain** (`create_agent`) for tool-calling agent orchestration
- **Google Gemini 2.5 Flash** as the LLM
- **Tavily** for web search and page content extraction
- **Pydantic** for structured, validated output schemas
- **Streamlit** for the UI

## Project structure

```
schemas.py        Pydantic output schemas (JobMatch, JobSearchResult)
tools.py           Custom LangChain tools (search_jobs, get_job_page_content)
agent.py           Agent construction and invocation logic (no UI code)
streamlit_app.py   Streamlit UI - the only entry point
```


## Limitations

- Match scoring is only as good as the LLM's judgment - it is a useful
  first pass, not a guarantee of fit.
- Some job boards block scraping/extraction, so a subset of postings may
  return partial content.
- Currently single-turn per run (no conversation memory across searches).

## Possible extensions

- Add a `filter_by_salary` or `filter_by_seniority` tool.
- Cache extracted page content to avoid re-fetching on repeated searches.
- Let users save/compare results across multiple searches in one session.
