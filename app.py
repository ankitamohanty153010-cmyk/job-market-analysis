from __future__ import annotations

import io
import re
from datetime import datetime
from pathlib import Path

import pandas as pd
import streamlit as st


st.set_page_config(
    page_title="Job Market Analysis & Recommendations",
    page_icon="💼",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    .block-container {padding-top: 2rem; padding-bottom: 3rem; max-width: 1300px;}
    .hero {
        padding: 2rem 2.2rem; border-radius: 18px; margin-bottom: 1.5rem;
        background: linear-gradient(115deg, #4669b2 0%, #263d69 58%, #192941 100%);
        border: 1px solid rgba(151, 178, 235, .22);
    }
    .hero h1 {margin: 0; color: #fff; font-size: 2.1rem;}
    .hero p {margin: .6rem 0 0; color: #e0e8fb; font-size: 1rem;}
    .small-note {color: #aab4c7; font-size: .88rem;}
    div[data-testid="stMetric"] {background: #202432; padding: 1rem; border-radius: 12px;}
    </style>
    """,
    unsafe_allow_html=True,
)

REQUIRED_COLUMNS = {"title", "is_hourly", "hourly_low", "hourly_high", "budget", "country"}


@st.cache_data(show_spinner=False)
def prepare_data(file_bytes: bytes) -> tuple[pd.DataFrame | None, str | None]:
    try:
        df = pd.read_csv(io.BytesIO(file_bytes), low_memory=False)
    except Exception as exc:
        return None, f"I couldn’t read that CSV: {exc}"

    missing = REQUIRED_COLUMNS - set(df.columns)
    if missing:
        return None, "The CSV is missing these required columns: " + ", ".join(sorted(missing))

    if "link" not in df.columns:
        df["link"] = ""
    if "published_date" not in df.columns:
        df["published_date"] = pd.NaT

    df["title"] = df["title"].fillna("").astype(str).str.strip()
    df = df.loc[df["title"].ne("")].copy()
    df["title_lower"] = df["title"].str.lower()
    df["is_hourly"] = df["is_hourly"].astype(str).str.strip().str.lower().isin(
        {"true", "1", "yes", "hourly"}
    )
    for col in ("hourly_low", "hourly_high", "budget"):
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df["hourly_midpoint"] = (df["hourly_low"] + df["hourly_high"]) / 2
    df["published_date"] = pd.to_datetime(df["published_date"], errors="coerce", utc=True)
    df["country"] = df["country"].fillna("Unknown").astype(str).str.strip().replace("", "Unknown")
    df["link"] = df["link"].fillna("").astype(str)
    return df, None


def money_range(row: pd.Series, hourly: bool) -> str:
    if hourly:
        low, high = row.get("hourly_low"), row.get("hourly_high")
        if pd.notna(low) and pd.notna(high):
            return f"{low:,.2f}–{high:,.2f} / hour"
        return "Hourly rate not listed"
    budget = row.get("budget")
    return f"Budget: {budget:,.0f}" if pd.notna(budget) else "Fixed-price budget not listed"


def render_recommendations(df: pd.DataFrame) -> None:
    st.subheader("🔎 Smart Job Recommendation Engine")
    st.caption("Find listings with matching words in their job titles. This first version uses title matching only.")

    left, right = st.columns([4, 1])
    with left:
        job_type = st.radio("Select job category", ["Hourly Jobs", "Fixed-Price Jobs"], horizontal=True)
        query = st.text_input("Enter a job title", placeholder="e.g., Full Stack Developer")
    with right:
        result_limit = st.slider("Top results", min_value=3, max_value=15, value=5)

    if st.button("Get Recommendations", type="primary", use_container_width=False):
        if not query.strip():
            st.warning("Enter a job title or a few skills to search.")
            return

        is_hourly = job_type == "Hourly Jobs"
        pool = df.loc[df["is_hourly"].eq(is_hourly)].copy()
        terms = [t for t in re.findall(r"[a-zA-Z0-9+#.]+", query.lower()) if len(t) > 1]
        if not terms:
            st.warning("Please enter at least one meaningful word.")
            return

        pool["match_score"] = sum(pool["title_lower"].str.contains(re.escape(term), na=False) for term in terms)
        results = pool.loc[pool["match_score"].gt(0)].copy()
        if results.empty:
            st.info("No title matches found. Try a broader search, such as ‘designer’ or ‘developer’.")
            return

        results = results.sort_values(
            ["match_score", "published_date"], ascending=[False, False], na_position="last"
        ).head(result_limit)
        st.success(f"Found {len(results)} matching listings.")
        for _, row in results.iterrows():
            with st.container(border=True):
                title_col, detail_col = st.columns([4, 2])
                with title_col:
                    st.markdown(f"#### {row['title']}")
                    st.caption(f"📍 {row['country']}  ·  {job_type[:-1] if job_type.endswith('s') else job_type}")
                with detail_col:
                    st.markdown(f"**{money_range(row, is_hourly)}**")
                    if pd.notna(row["published_date"]):
                        st.caption(f"Posted {row['published_date'].strftime('%d %b %Y')}")
                if row["link"].startswith(("http://", "https://")):
                    st.link_button("Open listing", row["link"])

        st.caption("Results are ranked by how many search words appear in the title, then by posting date. They are not personalized recommendations.")


def render_statistics(df: pd.DataFrame) -> None:
    st.subheader("📊 Quick Statistics")
    hourly = df.loc[df["is_hourly"]]
    fixed = df.loc[~df["is_hourly"]]
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Job postings", f"{len(df):,}")
    c2.metric("Hourly listings", f"{len(hourly):,}")
    c3.metric("Fixed-price listings", f"{len(fixed):,}")
    c4.metric("Countries / locations", f"{df['country'].nunique():,}")

    st.markdown("### Most active countries")
    country_counts = df["country"].value_counts().head(10)
    st.bar_chart(country_counts, horizontal=True)

    dated = df.dropna(subset=["published_date"]).copy()
    if not dated.empty:
        dated["month"] = dated["published_date"].dt.strftime("%Y-%m")
        st.markdown("### Postings by month")
        st.bar_chart(dated.groupby("month").size().rename("Postings"))

    st.markdown("### Most common job titles")
    st.dataframe(df["title"].value_counts().head(10).rename_axis("Title").reset_index(name="Postings"), hide_index=True, use_container_width=True)

    hourly_midpoints = hourly["hourly_midpoint"].dropna()
    if not hourly_midpoints.empty:
        st.markdown("### Hourly rate snapshot")
        st.caption("Rates are shown in the dataset’s units; the source does not specify a currency. The 999 upper-rate cap is excluded from this summary.")
        uncapped = hourly.loc[hourly["hourly_high"].lt(999), "hourly_midpoint"].dropna()
        a, b = st.columns(2)
        a.metric("Median hourly midpoint", f"{uncapped.median():,.2f}" if not uncapped.empty else "—")
        b.metric("Listings with usable rate bounds", f"{len(hourly_midpoints):,}")

    st.info("This dataset has no job descriptions, skill requirements, or explicit remote-work field. The app therefore focuses on title, location, date, and listed pay fields.")


with st.sidebar:
    st.markdown("## ℹ️ About This App")
    st.info("Explore job-market listings and find relevant posts using job-title keywords.")
    st.markdown("---")
    st.markdown("## 🧭 Menu & Info")
    page = st.radio("Navigation", ["Job Recommendation System", "Quick Statistics"], label_visibility="collapsed")
    st.markdown("---")
    st.markdown("### 👩‍💻 Developed by")
    st.markdown("**Ankita Vaghela**")
    st.caption("Job Market Analysis & Recommendation System")

st.markdown(
    """
    <div class="hero">
      <h1>💼 Job Recommendation &amp; Analytics Dashboard</h1>
      <p>Explore job-market patterns and discover listings that match your career interests.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

csv_name = "all_upwork_jobs_2024-02-07-2024-03-24.csv"
project_csv_candidates = [
    Path(__file__).with_name(csv_name),
    Path(__file__).parent.parent / csv_name,
]
project_csv = next((candidate for candidate in project_csv_candidates if candidate.exists()), project_csv_candidates[0])
uploaded = st.file_uploader(
    "Use another CSV (optional)",
    type=["csv"],
    help="By default, the app loads the project CSV beside app.py. Upload a different file only if needed.",
)

if uploaded is not None:
    csv_bytes = uploaded.getvalue()
elif project_csv.exists():
    csv_bytes = project_csv.read_bytes()
else:
    st.markdown("### Start by adding your data")
    st.write("Place the project CSV beside app.py or in the parent project folder, or upload it below to power recommendations and dashboard statistics.")
    st.caption("Expected fields include title, is_hourly, hourly_low, hourly_high, budget, and country. Posting date and listing link are used when available.")
    st.stop()

data, error = prepare_data(csv_bytes)
if error:
    st.error(error)
    st.stop()

st.caption(f"Loaded {len(data):,} listings · Updated {datetime.now().strftime('%d %b %Y')}")
if page == "Job Recommendation System":
    render_recommendations(data)
else:
    render_statistics(data)
