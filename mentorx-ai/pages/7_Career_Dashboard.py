"""
Page 7 – Career Dashboard
"""

import streamlit as st
import plotly.graph_objects as go

import sys
from pathlib import Path

src_dir = Path(__file__).resolve().parent.parent
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

from src.utils import (
    DatabaseManager, inject_theme, themed_fig, calculate_readiness_score,
    get_progress, generate_text_report, score_color, score_label, short_label,
)

st.set_page_config(
    page_title="Career Dashboard – MentorX AI",
    page_icon="📈",
    layout="wide",
)

inject_theme()

# ── Header ───────────────────────────────────────────────────────────────────
st.html(
    """
    <div style="margin-bottom:1rem;">
        <div style="color:#B8B2A7;font-size:.78em;text-transform:uppercase;
                    letter-spacing:.1em;margin-bottom:.3rem;">Step 7 of 7</div>
        <h1>📈 Career Dashboard</h1>
        <p style="color:#B8B2A7;font-size:.95em;">
            Your complete career readiness overview — all your progress in one place.</p>
    </div>
    """)

# ── Gate ─────────────────────────────────────────────────────────────────────
if "session_id" not in st.session_state:
    st.warning("Please start from the home page and enter your name first.")
    st.stop()

# ── Load dashboard data ──────────────────────────────────────────────────────
dashboard = st.session_state.get("dashboard_data", {})
user_name = st.session_state.get("user_name", "User")

# Try loading from DB if session state is sparse
db = DatabaseManager()
db_data = db.get_session_data(st.session_state["session_id"])
if db_data:
    for key in ("assessment", "recommendation", "skill_analysis",
                "roadmap", "resume", "interview"):
        if key not in dashboard and key in db_data and db_data[key] is not None:
            dashboard[key] = db_data[key]
    if db_data.get("target_career"):
        dashboard["target_career"] = db_data["target_career"]

# ── Readiness Score ──────────────────────────────────────────────────────────
readiness = calculate_readiness_score(dashboard)
progress = get_progress(dashboard)
completed_steps = sum(1 for p in progress if p["completed"])
r_color = score_color(readiness)

# Main score gauge
fig = go.Figure(go.Indicator(
    mode="gauge+number",
    value=readiness,
    number={"font": {"color": r_color, "size": 55}, "suffix": "%"},
    title={"text": "Career Readiness", "font": {"color": "#B8B2A7", "size": 14}},
    gauge={
        "axis": {"range": [0, 100], "tickcolor": "#B8B2A7",
                 "tickfont": {"color": "#B8B2A7"}},
        "bar": {"color": r_color},
        "bgcolor": "#252525",
        "steps": [
            {"range": [0, 40], "color": "rgba(224,122,95,0.10)"},
            {"range": [40, 70], "color": "rgba(212,163,115,0.10)"},
            {"range": [70, 100], "color": "rgba(129,166,132,0.10)"},
        ],
        "threshold": {
            "line": {"color": "#F5F1E8", "width": 3},
            "thickness": 0.8, "value": readiness,
        },
    },
))
fig = themed_fig(fig)
fig.update_layout(height=260)

c1, c2 = st.columns([1, 1])
with c1:
    st.plotly_chart(fig, width="stretch")
with c2:
    # Progress steps
    steps_html = ""
    for p in progress:
        color = "#81A684" if p["completed"] else "#706B63"
        steps_html += (
            f"<div style='display:flex;align-items:center;gap:.5rem;"
            f"padding:.35rem 0;'>"
            f"<span style='font-size:.9em;'>{p['icon']}</span>"
            f"<span style='color:{color};font-size:.88em;'>"
            f"{p['step']}</span></div>"
        )

    st.html(
        f"""<div style="background:#1E1E1E;border:1px solid rgba(255,255,255,0.05);
                    border-radius:12px;padding:1.2rem 1.5rem;height:100%;">
            <div style="color:#F5F1E8;font-weight:700;font-size:.95em;
                        margin-bottom:.6rem;">Journey Progress</div>
            <div style="color:#B8B2A7;font-size:.82em;margin-bottom:.8rem;">
                {completed_steps} of 6 steps completed</div>
            <div style="background:#252525;border-radius:6px;height:6px;
                        overflow:hidden;margin-bottom:1rem;">
                <div style="background:linear-gradient(90deg,#E07A5F,#D4A373);
                            height:100%;width:{completed_steps/6*100}%;
                            border-radius:6px;"></div>
            </div>
            {steps_html}
        </div>""")

# ── Metric Cards Row ─────────────────────────────────────────────────────────
st.html("<div style='margin-top:1rem;'></div>")

mc1, mc2, mc3, mc4 = st.columns(4)

# Career Match
with mc1:
    sa = dashboard.get("skill_analysis") or {}
    gap = sa.get("gap_analysis") or {} if isinstance(sa, dict) else {}
    match_pct = gap.get("overall_match_percentage", "—") if isinstance(gap, dict) else "—"
    st.html(
        f"""<div style="background:#1E1E1E;border:1px solid rgba(255,255,255,0.05);
                    border-radius:12px;padding:1rem 1.2rem;text-align:center;">
            <div style="color:#B8B2A7;font-size:.72em;text-transform:uppercase;
                        letter-spacing:.08em;">Career Match</div>
            <div style="font-size:2em;font-weight:700;color:#E07A5F;
                        margin:.3rem 0;">{match_pct}{'%' if isinstance(match_pct, int) else ''}</div>
            <div style="color:#B8B2A7;font-size:.78em;">Skill Alignment</div>
        </div>""")

# Skills Progress
with mc2:
    skills = gap.get("skills_comparison", []) if isinstance(gap, dict) else []
    avg_skill = sum(s.get("current_level", 0) for s in skills) / len(skills) if skills else 0
    st.html(
        f"""<div style="background:#1E1E1E;border:1px solid rgba(255,255,255,0.05);
                    border-radius:12px;padding:1rem 1.2rem;text-align:center;">
            <div style="color:#B8B2A7;font-size:.72em;text-transform:uppercase;
                        letter-spacing:.08em;">Skills Level</div>
            <div style="font-size:2em;font-weight:700;color:#D4A373;
                        margin:.3rem 0;">{avg_skill:.1f}</div>
            <div style="color:#B8B2A7;font-size:.78em;">Avg out of 10</div>
        </div>""")

# Roadmap Progress
with mc3:
    roadmap = dashboard.get("roadmap") or {}
    if not isinstance(roadmap, dict):
        roadmap = {}
    phases = roadmap.get("phases", [])
    total_weeks = roadmap.get("total_weeks", sum(p.get("duration_weeks", 4) for p in phases))
    st.html(
        f"""<div style="background:#1E1E1E;border:1px solid rgba(255,255,255,0.05);
                    border-radius:12px;padding:1rem 1.2rem;text-align:center;">
            <div style="color:#B8B2A7;font-size:.72em;text-transform:uppercase;
                        letter-spacing:.08em;">Roadmap</div>
            <div style="font-size:2em;font-weight:700;color:#81A684;
                        margin:.3rem 0;">{total_weeks}</div>
            <div style="color:#B8B2A7;font-size:.78em;">Weeks Planned</div>
        </div>""")

# Interview Readiness
with mc4:
    interview = dashboard.get("interview") or {}
    if not isinstance(interview, dict):
        interview = {}
    fb = interview.get("feedback") or {}
    if not isinstance(fb, dict):
        fb = {}
    int_score = fb.get("overall_score", "—")
    st.html(
        f"""<div style="background:#1E1E1E;border:1px solid rgba(255,255,255,0.05);
                    border-radius:12px;padding:1rem 1.2rem;text-align:center;">
            <div style="color:#B8B2A7;font-size:.72em;text-transform:uppercase;
                        letter-spacing:.08em;">Interview</div>
            <div style="font-size:2em;font-weight:700;color:#E07A5F;
                        margin:.3rem 0;">{int_score}{'%' if isinstance(int_score, int) else ''}</div>
            <div style="color:#B8B2A7;font-size:.78em;">Readiness</div>
        </div>""")

# ── Interest Radar ───────────────────────────────────────────────────────────
assessment = dashboard.get("assessment", {})
scores = assessment.get("interest_scores", {})

if scores:
    st.html(
        """<div style="background:#1E1E1E;border:1px solid rgba(255,255,255,0.05);
                    border-radius:14px;padding:1.2rem 1.5rem;margin:1.2rem 0 .5rem;">
            <div style="color:#F5F1E8;font-size:1.05em;font-weight:700;">
                🧭 Interest Profile</div>
            <div style="color:#B8B2A7;font-size:.85em;">
                Your assessment dimensions</div>
        </div>""")

    dims = list(scores.keys())
    vals = list(scores.values())

    dims = [short_label(d.replace("_", " ").title()) for d in dims]

    fig2 = go.Figure(go.Scatterpolar(
        r=vals + [vals[0]],
        theta=dims + [dims[0]],
        fill="toself",
        line=dict(color="#E07A5F", width=3),
        fillcolor="rgba(224,122,95,0.15)",
        marker=dict(size=6, color="#E07A5F"),
        hovertemplate="<b>%{theta}</b><br>Score: %{r}/5<extra></extra>",
    ))
    fig2 = themed_fig(fig2)
    fig2.update_layout(
        title=dict(
            text="Interest Profile",
            font=dict(size=18, color="#F5F1E8"),
            x=0.5,
        ),
        height=450,
        margin=dict(t=70, b=60, l=60, r=60),
        polar=dict(
            bgcolor="#1E1E1E",
            radialaxis=dict(visible=True, range=[0, 5],
                            gridcolor="rgba(255,255,255,0.08)",
                            tickfont=dict(size=11, color="#B8B2A7")),
            angularaxis=dict(gridcolor="rgba(255,255,255,0.08)",
                             tickfont=dict(size=12, color="#F5F1E8"),
                             rotation=45),
        ),
        showlegend=False,
    )
    st.plotly_chart(fig2, width="stretch")

# ── Skills Bar Chart ─────────────────────────────────────────────────────────
if skills:
    st.html(
        """<div style="background:#1E1E1E;border:1px solid rgba(255,255,255,0.05);
                    border-radius:14px;padding:1.2rem 1.5rem;margin:1.2rem 0 .5rem;">
            <div style="color:#F5F1E8;font-size:1.05em;font-weight:700;">
                📊 Skills Comparison</div>
            <div style="color:#B8B2A7;font-size:.85em;">
                Current vs. required skill levels</div>
        </div>""")

    sorted_skills = sorted(
        [s for s in skills if s.get("skill")],
        key=lambda s: s.get("required_level", 0) - s.get("current_level", 0),
        reverse=True,
    )[:10]
    skill_names = [short_label(s.get("skill", "Skill")) for s in sorted_skills]
    current = [s.get("current_level", 0) for s in sorted_skills]
    required = [s.get("required_level", 0) for s in sorted_skills]

    fig3 = go.Figure()
    fig3.add_trace(go.Bar(
        x=skill_names, y=current, name="Your Level",
        marker_color="#D4A373",
        hovertemplate="<b>%{x}</b><br>Your level: %{y}/10<extra></extra>",
    ))
    fig3.add_trace(go.Bar(
        x=skill_names, y=required, name="Required",
        marker_color="#E07A5F", opacity=0.6,
        hovertemplate="<b>%{x}</b><br>Required: %{y}/10<extra></extra>",
    ))
    fig3 = themed_fig(fig3)
    fig3.update_layout(
        title=dict(
            text="Skills Comparison",
            font=dict(size=18, color="#F5F1E8"),
            x=0.5,
        ),
        barmode="group",
        showlegend=True,
        height=440,
        margin=dict(t=70, b=110, l=50, r=30),
        xaxis=dict(
            tickangle=-30,
            tickfont=dict(size=11, color="#F5F1E8"),
        ),
        yaxis=dict(
            title=dict(text="Level (0-10)", font=dict(color="#B8B2A7")),
            tickfont=dict(color="#B8B2A7"),
            range=[0, max(max(current or [0]), max(required or [0])) * 1.15 or 10],
        ),
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
    st.plotly_chart(fig3, width="stretch")

# ── Resume Score ─────────────────────────────────────────────────────────────
resume = dashboard.get("resume", {})
if resume:
    fb = resume.get("feedback", {})
    overall = fb.get("overall_score", 0)
    st.html(
        f"""<div style="background:#1E1E1E;border:1px solid rgba(255,255,255,0.05);
                    border-radius:12px;padding:1.2rem 1.5rem;margin:1.2rem 0;">
            <div style="display:flex;justify-content:space-between;align-items:center;
                        flex-wrap:wrap;">
                <div>
                    <div style="color:#F5F1E8;font-weight:700;font-size:1em;">
                        📄 Resume Score</div>
                    <div style="color:#B8B2A7;font-size:.85em;margin-top:.2rem;">
                        {score_label(overall)} — review the Resume Analyzer for details</div>
                </div>
                <div style="font-size:2em;font-weight:700;color:{score_color(overall)};">
                    {overall}%</div>
            </div>
        </div>""")

# ── Recommended Career & Next Action ────────────────────────────────────────
rec = dashboard.get("recommendation", {})
rec_careers = rec.get("recommended_careers", []) if rec else []

if rec_careers or not all(p["completed"] for p in progress):
    rc1, rc2 = st.columns([1, 1])

    with rc1:
        if rec_careers:
            top = rec_careers[0]
            st.html(
                f"""<div style="background:#1E1E1E;border:1px solid rgba(224,122,95,.12);
                            border-radius:12px;padding:1.2rem 1.5rem;">
                    <div style="color:#B8B2A7;font-size:.72em;text-transform:uppercase;
                                letter-spacing:.08em;margin-bottom:.3rem;">Recommended Career</div>
                    <div style="color:#F5F1E8;font-size:1.2em;font-weight:700;
                                margin-bottom:.3rem;">{top.get('title', '—')}</div>
                    <div style="color:#D4A373;font-size:.88em;">
                        {top.get('match_score', 0)}% match  ·  {top.get('salary_range_pkr', '')}</div>
                </div>""")

    with rc2:
        # Determine next incomplete step
        next_step = None
        step_pages = {
            "Career Assessment": "pages/1_Career_Assessment.py",
            "Career Recommendation": "pages/2_Career_Recommendation.py",
            "Skill Gap Analysis": "pages/3_Skill_Gap_Analysis.py",
            "Learning Roadmap": "pages/4_Learning_Roadmap.py",
            "Resume Analyzer": "pages/5_Resume_Analyzer.py",
            "AI Mock Interview": "pages/6_AI_Mock_Interview.py",
        }
        for p in progress:
            if not p["completed"]:
                next_step = p["step"]
                break

        if next_step:
            st.html(
                f"""<div style="background:#1E1E1E;border:1px solid rgba(129,166,132,.12);
                            border-radius:12px;padding:1.2rem 1.5rem;">
                    <div style="color:#B8B2A7;font-size:.72em;text-transform:uppercase;
                                letter-spacing:.08em;margin-bottom:.3rem;">Next Recommended Action</div>
                    <div style="color:#81A684;font-size:1.05em;font-weight:600;
                                margin-bottom:.3rem;">Complete your {next_step}</div>
                    <div style="color:#B8B2A7;font-size:.85em;">
                        Continue your journey to unlock full career insights</div>
                </div>""")
        else:
            st.html(
                """<div style="background:#1E1E1E;border:1px solid rgba(129,166,132,.12);
                            border-radius:12px;padding:1.2rem 1.5rem;">
                    <div style="color:#81A684;font-size:1.05em;font-weight:600;">
                        🎉 All steps complete!</div>
                    <div style="color:#B8B2A7;font-size:.85em;margin-top:.3rem;">
                        Review your insights and download your career report below</div>
                </div>""")

# ── Export Report ────────────────────────────────────────────────────────────
st.divider()
report = generate_text_report(dashboard)

c1, c2, c3 = st.columns([1, 2, 1])
with c2:
    st.download_button(
        label="📥  Download Career Report",
        data=report,
        file_name=f"mentorx_report_{st.session_state.get('user_name', 'user').replace(' ', '_')}.txt",
        mime="text/plain",
        type="primary",
        width="stretch",
    )

# ── Footer ───────────────────────────────────────────────────────────────────
st.html(
    """<div style="background:#1E1E1E;border:1px solid rgba(255,255,255,0.05);
                border-radius:12px;padding:1.2rem;text-align:center;margin-top:1rem;">
        <p style="color:#B8B2A7;font-size:.88em;margin:0;">
            🚀 Keep working on your career journey — consistency is the key to success!</p>
        <p style="color:#706B63;font-size:.8em;margin:.5rem 0 0;">
            MentorX AI — Pakistan's Personal Career Coach</p>
    </div>""")
