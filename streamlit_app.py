import json
import os
from datetime import datetime

import streamlit as st
from dotenv import load_dotenv

from agent import build_agent, search_jobs_for_resume

load_dotenv()

st.set_page_config(page_title="Job Search Agent", page_icon="🔎", layout="wide")


def get_api_key(name: str) -> str:
    """Prefer Streamlit secrets (for deployed apps), fall back to env vars (for local .env)."""
    try:
        if name in st.secrets:
            return st.secrets[name]
    except Exception:
        pass
    return os.environ.get(name, "")


GOOGLE_API_KEY = get_api_key("GOOGLE_API_KEY")
TAVILY_API_KEY = get_api_key("TAVILY_API_KEY")

if GOOGLE_API_KEY:
    os.environ["GOOGLE_API_KEY"] = GOOGLE_API_KEY
if TAVILY_API_KEY:
    os.environ["TAVILY_API_KEY"] = TAVILY_API_KEY


@st.cache_resource
def get_agent():
    return build_agent()


def score_color(score: int) -> str:
    if score >= 75:
        return "🟢"
    if score >= 50:
        return "🟡"
    return "🔴"


st.title("🔎 Job Search Agent")
st.caption(
    "An agent that searches the web for job postings, reads each one in full, "
    "and scores it against your resume - not just a keyword match."
)

if not GOOGLE_API_KEY or not TAVILY_API_KEY:
    st.warning(
        "Missing API keys. Set `GOOGLE_API_KEY` and `TAVILY_API_KEY` in a `.env` file "
        "locally, or in Streamlit secrets when deployed."
    )

with st.sidebar:
    st.header("Search settings")
    role = st.text_input("Target role", value="AI Engineer")
    location = st.text_input("Location", value="Remote")
    max_results = st.slider("Max postings to consider", min_value=1, max_value=10, value=5)
    st.divider()
    st.header("Your resume")
    resume_file = st.file_uploader("Upload resume (.txt or .md)", type=["txt", "md"])
    resume_pasted = st.text_area("...or paste resume text here", height=200)
    run_clicked = st.button("Search jobs", type="primary", use_container_width=True)

if run_clicked:
    resume_text = ""
    if resume_file is not None:
        resume_text = resume_file.read().decode("utf-8")
    elif resume_pasted.strip():
        resume_text = resume_pasted.strip()

    if not resume_text:
        st.error("Please upload or paste your resume text before searching.")
    elif not GOOGLE_API_KEY or not TAVILY_API_KEY:
        st.error("Cannot run: missing API keys. See the warning above.")
    else:
        with st.spinner("Searching postings, reading each one, and scoring against your resume..."):
            try:
                agent = get_agent()
                result = search_jobs_for_resume(agent, resume_text, role, location, max_results)
                st.session_state["result"] = result
            except Exception as exc:  # noqa: BLE001
                st.error(f"Something went wrong: {exc}")

if "result" in st.session_state:
    result = st.session_state["result"]

    st.subheader("Summary")
    st.write(result.summary)

    st.subheader("Matches")
    sorted_matches = sorted(result.matches, key=lambda m: -m.match_score)
    for match in sorted_matches:
        with st.container(border=True):
            col1, col2 = st.columns([4, 1])
            with col1:
                st.markdown(f"### {match.title} — {match.company}")
                st.markdown(f"[{match.url}]({match.url})")
                if match.location:
                    st.caption(match.location)
            with col2:
                st.markdown(f"## {score_color(match.match_score)} {match.match_score}/100")

            st.progress(match.match_score / 100)

            c1, c2 = st.columns(2)
            with c1:
                if match.matching_skills:
                    st.markdown("**✅ Matching**")
                    st.write(", ".join(match.matching_skills))
            with c2:
                if match.missing_skills:
                    st.markdown("**⚠️ Missing**")
                    st.write(", ".join(match.missing_skills))

            st.markdown(f"**Why:** {match.reasoning}")

    st.divider()
    json_bytes = json.dumps(result.model_dump(), indent=2).encode("utf-8")
    st.download_button(
        "Download full results (JSON)",
        data=json_bytes,
        file_name=f"job_matches_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
        mime="application/json",
    )
