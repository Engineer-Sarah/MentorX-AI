"""
Page 2 – Career Recommendation
"""

import streamlit as st

import sys
from pathlib import Path

src_dir = Path(__file__).resolve().parent.parent
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

from src.utils import GeminiService, DatabaseManager, inject_theme, score_color, score_label

st.set_page_config(
    page_title="Career Recommendation – MentorX AI",
    page_icon="🎯",
    layout="wide",
)

inject_theme()

# ── Header ───────────────────────────────────────────────────────────────────
st.html(
    """
    <div style="margin-bottom:1rem;">
        <div style="color:#B8B2A7;font-size:.78em;text-transform:uppercase;
                    letter-spacing:.1em;margin-bottom:.3rem;">Step 2 of 7</div>
        <h1>🎯 Career Recommendation</h1>
        <p style="color:#B8B2A7;font-size:.95em;">
            AI-powered career suggestions based on your assessment profile.</p>
    </div>
    """)

# ── Gate ─────────────────────────────────────────────────────────────────────
if "session_id" not in st.session_state:
    st.warning("Please start from the home page and enter your name first.")
    st.stop()

if "assessment_completed" not in st.session_state:
    st.warning("Please complete the Career Assessment first.")
    st.stop()

# ── Generate or display recommendations ─────────────────────────────────────
gemini = GeminiService()

# Regenerate if missing or empty (e.g. stale session state)
existing = st.session_state.get("career_recommendations", {})
needs_generation = (
    not existing or not existing.get("recommended_careers")
)

if needs_generation:
    with st.spinner("🤖  Analysing your profile and finding the best career paths…"):
        assessment = st.session_state.get("assessment_results", {})
        user_name = st.session_state.get("user_name", "User")

        recs = gemini.recommend_careers(assessment, user_name)

        if recs and recs.get("recommended_careers"):
            st.session_state["career_recommendations"] = recs

            db = DatabaseManager()
            db.save_recommendation(st.session_state["session_id"], recs)

            if "dashboard_data" not in st.session_state:
                st.session_state["dashboard_data"] = {}
            st.session_state["dashboard_data"]["recommendation"] = recs
        else:
            st.error(
                "Unable to generate your recommendation right now. "
                "Please try again in a moment."
            )
            st.stop()

recs = st.session_state["career_recommendations"]
recommended = recs.get("recommended_careers", [])

# ── Top Career Summary ───────────────────────────────────────────────────────
if recommended:
    top = recommended[0]
    top_score = top.get("match_score", 0)
    top_color = score_color(top_score)

    st.html(
        f"""
        <div style="background:linear-gradient(135deg,rgba(224,122,95,.12),rgba(212,163,115,.08));
                    border:1px solid rgba(224,122,95,.15);border-radius:14px;
                    padding:1.5rem 1.8rem;margin-bottom:1.5rem;">
            <div style="display:flex;justify-content:space-between;align-items:center;
                        flex-wrap:wrap;">
                <div>
                    <div style="color:#B8B2A7;font-size:.75em;text-transform:uppercase;
                                letter-spacing:.1em;">Your Top Career Match</div>
                    <h2 style="color:#F5F1E8;margin:.3rem 0 0;font-size:1.6em !important;">
                        {top.get('title', '—')}</h2>
                    <p style="color:#B8B2A7;font-size:.88em;margin-top:.3rem;">
                        {top.get('why_matches', '')[:120]}…</p>
                </div>
                <div style="text-align:center;padding:.8rem 1.5rem;background:#1E1E1E;
                            border-radius:12px;border:1px solid rgba(255,255,255,.05);
                            min-width:110px;">
                    <div style="color:#B8B2A7;font-size:.7em;text-transform:uppercase;
                                letter-spacing:.08em;">Match</div>
                    <div style="font-size:2.4em;font-weight:700;color:{top_color};
                                line-height:1;">{top_score}%</div>
                    <div style="color:#B8B2A7;font-size:.75em;margin-top:2px;">
                        {score_label(top_score)}</div>
                </div>
            </div>
        </div>""")

# ── All Recommendations ──────────────────────────────────────────────────────
st.html(
    """<div style="margin-bottom:1rem;">
        <h2>Top Career Matches</h2>
    </div>""")

for rank, career in enumerate(recommended, 1):
    title = career.get("title", "Unknown")
    match_score = career.get("match_score", 0)
    why = career.get("why_matches", "No details available.")
    strengths = career.get("your_strengths", [])
    gaps = career.get("skill_gaps", [])
    salary = career.get("salary_range_pkr", "")
    color = score_color(match_score)

    # Build strengths HTML
    strengths_html = ""
    if strengths:
        items = "".join(
            f"<span style='background:rgba(129,166,132,.12);color:#81A684;"
            f"padding:.2rem .6rem;border-radius:6px;font-size:.8em;"
            f"margin-right:.4rem;margin-bottom:.3rem;display:inline-block;'>"
            f"{s}</span>" for s in strengths
        )
        strengths_html = f"<div style='margin-top:.6rem;'><div style='color:#B8B2A7;font-size:.78em;text-transform:uppercase;letter-spacing:.06em;margin-bottom:.4rem;'>Your Strengths</div><div style='display:flex;flex-wrap:wrap;'>{items}</div></div>"

    # Build gaps HTML
    gaps_html = ""
    if gaps:
        items = "".join(
            f"<span style='background:rgba(224,122,95,.1);color:#E07A5F;"
            f"padding:.2rem .6rem;border-radius:6px;font-size:.8em;"
            f"margin-right:.4rem;margin-bottom:.3rem;display:inline-block;'>"
            f"{g}</span>" for g in gaps
        )
        gaps_html = f"<div style='margin-top:.6rem;'><div style='color:#B8B2A7;font-size:.78em;text-transform:uppercase;letter-spacing:.06em;margin-bottom:.4rem;'>Skill Gaps</div><div style='display:flex;flex-wrap:wrap;'>{items}</div></div>"

    st.html(
        f"""<div style="background:#1E1E1E;border:1px solid rgba(255,255,255,.05);
                    border-radius:14px;padding:1.3rem 1.5rem;margin-bottom:1rem;">
            <div style="display:flex;justify-content:space-between;align-items:flex-start;
                        flex-wrap:wrap;">
                <div style="flex:1;min-width:200px;">
                    <div style="display:flex;align-items:center;gap:.5rem;margin-bottom:.3rem;">
                        <span style="background:{color};color:#151515;width:26px;height:26px;
                                     border-radius:50%;display:flex;align-items:center;
                                     justify-content:center;font-weight:700;font-size:.8em;">
                            {rank}</span>
                        <span style="color:#F5F1E8;font-size:1.15em;font-weight:700;">
                            {title}</span>
                    </div>
                    <p style="color:#B8B2A7;font-size:.88em;line-height:1.6;margin:.5rem 0;">
                        {why}</p>
                </div>
                <div style="text-align:center;min-width:90px;padding-left:1rem;">
                    <div style="color:#B8B2A7;font-size:.7em;text-transform:uppercase;
                                letter-spacing:.06em;">Match</div>
                    <div style="font-size:1.8em;font-weight:700;color:{color};
                                line-height:1.1;">{match_score}%</div>
                </div>
            </div>
            <div style="background:#252525;border-radius:6px;height:6px;
                        overflow:hidden;margin:.8rem 0 .6rem;">
                <div style="background:{color};height:100%;width:{match_score}%;
                            border-radius:6px;"></div>
            </div>
            {strengths_html}
            {gaps_html}
            {f'<div style="color:#B8B2A7;font-size:.8em;margin-top:.8rem;">💰 {salary}</div>' if salary else ''}
        </div>""")

# ── Next Step ────────────────────────────────────────────────────────────────
st.divider()
c1, c2, c3 = st.columns([1, 2, 1])
with c2:
    if st.button("📊  Go to Skill Gap Analysis", type="primary",
                 width="stretch"):
        st.switch_page("pages/3_Skill_Gap_Analysis.py")
