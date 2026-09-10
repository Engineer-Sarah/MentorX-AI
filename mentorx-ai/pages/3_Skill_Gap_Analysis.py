"""
Page 3 – Skill Gap Analysis
"""

import streamlit as st
import plotly.graph_objects as go

import sys
from pathlib import Path

src_dir = Path(__file__).resolve().parent.parent
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

from src.utils import (
    GeminiService, DatabaseManager, inject_theme, themed_fig,
    score_color, score_label, short_label,
)

st.set_page_config(
    page_title="Skill Gap Analysis – MentorX AI",
    page_icon="📊",
    layout="wide",
)

inject_theme()

# ── Header ───────────────────────────────────────────────────────────────────
st.html(
    """
    <div style="margin-bottom:1rem;">
        <div style="color:#B8B2A7;font-size:.78em;text-transform:uppercase;
                    letter-spacing:.1em;margin-bottom:.3rem;">Step 3 of 7</div>
        <h1>📊 Skill Gap Analysis</h1>
        <p style="color:#B8B2A7;font-size:.95em;">
            Compare your current skills against industry requirements for your
            target career.</p>
    </div>
    """)

# ── Gate ─────────────────────────────────────────────────────────────────────
if "session_id" not in st.session_state:
    st.warning("Please start from the home page and enter your name first.")
    st.stop()

if "career_recommendations" not in st.session_state:
    st.warning("Please complete the Career Recommendation step first.")
    st.stop()

# ── Target Career Selection ─────────────────────────────────────────────────
recs = st.session_state.get("career_recommendations", {})
recommended = recs.get("recommended_careers", [])

if not recommended:
    st.warning("No career recommendations available. Please redo the assessment.")
    st.stop()

career_titles = [c.get("title", "Unknown") for c in recommended]
selected_career = st.selectbox(
    "Select a target career to analyse",
    options=career_titles,
    label_visibility="collapsed",
)

# ── Generate or display analysis ─────────────────────────────────────────────
gemini = GeminiService()

cache_key = f"skill_analysis_{selected_career}"

if cache_key not in st.session_state:
    with st.spinner(f"🔍  Analysing skill gaps for {selected_career}…"):
        assessment = st.session_state.get("assessment_results", {})
        analysis = gemini.analyze_skill_gap(assessment, selected_career)

        if analysis:
            st.session_state[cache_key] = analysis

            db = DatabaseManager()
            db.save_skill_analysis(
                st.session_state["session_id"], selected_career, analysis
            )

            if "dashboard_data" not in st.session_state:
                st.session_state["dashboard_data"] = {}
            st.session_state["dashboard_data"]["skill_analysis"] = analysis
            st.session_state["dashboard_data"]["target_career"] = selected_career
        else:
            st.error("Unable to analyse skill gaps right now. Please try again.")
            st.stop()

analysis = st.session_state[cache_key]

# ── Overall Match ────────────────────────────────────────────────────────────
gap = analysis.get("gap_analysis", {})
match_pct = gap.get("overall_match_percentage", 0)
gap_pct = 100 - match_pct
match_color = score_color(match_pct)

st.html(
    f"""<div style="background:linear-gradient(135deg,rgba(224,122,95,0.10),rgba(212,163,115,0.06));
                border:1px solid rgba(224,122,95,0.12);border-radius:14px;
                padding:1.5rem 1.8rem;margin-bottom:1.5rem;text-align:center;">
        <div style="color:#B8B2A7;font-size:.75em;text-transform:uppercase;
                    letter-spacing:.1em;">Overall Skill Match</div>
        <div style="font-size:3em;font-weight:700;color:{match_color};
                    line-height:1.1;margin:.3rem 0;">{match_pct}%</div>
        <div style="background:#252525;border-radius:6px;height:8px;
                    overflow:hidden;max-width:300px;margin:.5rem auto 0;">
            <div style="background:{match_color};height:100%;width:{match_pct}%;
                        border-radius:6px;"></div>
        </div>
        <div style="color:#B8B2A7;font-size:.85em;margin-top:.5rem;">
            {score_label(match_pct)} match  ·  {gap_pct}% skills to develop</div>
    </div>""")

# ── Radar Chart ──────────────────────────────────────────────────────────────
skills = gap.get("skills_comparison", [])
if skills:
    st.html(
        """<div style="background:#1E1E1E;border:1px solid rgba(255,255,255,0.05);
                    border-radius:14px;padding:1.2rem 1.5rem;margin-bottom:1rem;">
            <div style="color:#F5F1E8;font-size:1.05em;font-weight:700;">
                📈 Skill Comparison</div>
            <div style="color:#B8B2A7;font-size:.85em;">
                Your current skills vs. required levels</div>
        </div>""")

    # Keep the chart readable: use the 8 biggest gaps first, then sort by name
    sorted_skills = sorted(
        [s for s in skills if s.get("skill")],
        key=lambda s: s.get("required_level", 0) - s.get("current_level", 0),
        reverse=True,
    )[:8]
    sorted_skills = sorted(sorted_skills, key=lambda s: s.get("skill", ""))

    skill_names = [short_label(s.get("skill", "Skill")) for s in sorted_skills]
    current = [s.get("current_level", 0) for s in sorted_skills]
    required = [s.get("required_level", 0) for s in sorted_skills]

    if skill_names:
        fig = go.Figure()
        fig.add_trace(go.Scatterpolar(
            r=current + [current[0]],
            theta=skill_names + [skill_names[0]],
            fill="toself",
            name="Your Level",
            line=dict(color="#D4A373", width=3),
            fillcolor="rgba(212,163,115,0.18)",
            marker=dict(size=6, color="#D4A373"),
            hovertemplate="<b>%{theta}</b><br>Your level: %{r}/10<extra></extra>",
        ))
        fig.add_trace(go.Scatterpolar(
            r=required + [required[0]],
            theta=skill_names + [skill_names[0]],
            fill="toself",
            name="Required",
            line=dict(color="#E07A5F", width=3),
            fillcolor="rgba(224,122,95,0.12)",
            marker=dict(size=6, color="#E07A5F"),
            hovertemplate="<b>%{theta}</b><br>Required: %{r}/10<extra></extra>",
        ))
        fig = themed_fig(fig)
        fig.update_layout(
            title=dict(
                text="Skill Gap Radar",
                font=dict(size=18, color="#F5F1E8"),
                x=0.5,
            ),
            height=520,
            margin=dict(t=70, b=70, l=70, r=70),
            polar=dict(
                bgcolor="#1E1E1E",
                radialaxis=dict(
                    visible=True,
                    range=[0, 10],
                    gridcolor="rgba(255,255,255,0.08)",
                    tickcolor="rgba(255,255,255,0.10)",
                    tickfont=dict(size=11, color="#B8B2A7"),
                ),
                angularaxis=dict(
                    gridcolor="rgba(255,255,255,0.08)",
                    tickfont=dict(size=12, color="#F5F1E8"),
                    rotation=45,
                    direction="clockwise",
                ),
            ),
            showlegend=True,
            legend=dict(
                bgcolor="rgba(0,0,0,0)",
                font=dict(size=12, color="#B8B2A7"),
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="center",
                x=0.5,
            ),
        )
        st.plotly_chart(fig, width="stretch")

# ── Detailed Skills ──────────────────────────────────────────────────────────
if skills:
    st.html(
        """<div style="margin:1.2rem 0 .6rem;">
            <h3 style="color:#F5F1E8;">Detailed Skill Breakdown</h3>
        </div>""")

    for s in skills:
        skill_name = s.get("skill", "")
        if not skill_name:
            continue
        cur = s.get("current_level", 0)
        req = s.get("required_level", 0)
        diff = req - cur
        if diff > 0:
            status_color = "#E07A5F"
            status = f"+{diff} to develop"
        elif diff == 0:
            status_color = "#81A684"
            status = "✓ Matched"
        else:
            status_color = "#81A684"
            status = "✓ Exceeds"

        st.html(
            f"""<div style="background:#1E1E1E;border:1px solid rgba(255,255,255,0.04);
                        border-radius:10px;padding:.8rem 1.2rem;margin-bottom:.5rem;">
                <div style="display:flex;justify-content:space-between;align-items:center;
                            flex-wrap:wrap;">
                    <span style="color:#F5F1E8;font-weight:600;font-size:.92em;">
                        {skill_name}</span>
                    <span style="color:{status_color};font-size:.82em;font-weight:500;">
                        {status}</span>
                </div>
                <div style="display:flex;gap:.8rem;align-items:center;margin-top:.4rem;">
                    <span style="color:#B8B2A7;font-size:.78em;min-width:60px;">
                        You: {cur}/10</span>
                    <div style="flex:1;background:#252525;border-radius:4px;height:6px;
                                overflow:hidden;position:relative;">
                        <div style="background:#D4A373;height:100%;
                                    width:{cur/10*100}%;border-radius:4px;
                                    position:absolute;"></div>
                        <div style="background:rgba(224,122,95,0.30);height:100%;
                                    width:{req/10*100}%;border-radius:4px;"></div>
                    </div>
                    <span style="color:#B8B2A7;font-size:.78em;min-width:75px;">
                        Req: {req}/10</span>
                </div>
            </div>""")

# ── Next Step ────────────────────────────────────────────────────────────────
st.divider()
c1, c2, c3 = st.columns([1, 2, 1])
with c2:
    if st.button("🗺  Go to Learning Roadmap", type="primary",
                 width="stretch"):
        st.switch_page("pages/4_Learning_Roadmap.py")
