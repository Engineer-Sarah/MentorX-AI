"""
Page 4 – Learning Roadmap
"""

import streamlit as st
import plotly.graph_objects as go
from datetime import datetime

import sys
from pathlib import Path

src_dir = Path(__file__).resolve().parent.parent
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

from src.utils import GeminiService, DatabaseManager, inject_theme, themed_fig

st.set_page_config(
    page_title="Learning Roadmap – MentorX AI",
    page_icon="🗺",
    layout="wide",
)

inject_theme()

# ── Header ───────────────────────────────────────────────────────────────────
st.html(
    """
    <div style="margin-bottom:1rem;">
        <div style="color:#B8B2A7;font-size:.78em;text-transform:uppercase;
                    letter-spacing:.1em;margin-bottom:.3rem;">Step 4 of 7</div>
        <h1>🗺  Learning Roadmap</h1>
        <p style="color:#B8B2A7;font-size:.95em;">
            Your personalised, step-by-step learning plan with timelines,
            milestones and free resources.</p>
    </div>
    """)

# ── Gate ─────────────────────────────────────────────────────────────────────
if "session_id" not in st.session_state:
    st.warning("Please start from the home page and enter your name first.")
    st.stop()

target_career = st.session_state.get("dashboard_data", {}).get("target_career", "")
if not target_career:
    recs = st.session_state.get("career_recommendations", {})
    recommended = recs.get("recommended_careers", [])
    if recommended:
        target_career = recommended[0].get("title", "")

if not target_career:
    st.warning("Please complete the Skill Gap Analysis step first.")
    st.stop()

# ── Generate or display roadmap ─────────────────────────────────────────────
gemini = GeminiService()

if "learning_roadmap" not in st.session_state:
    with st.spinner(f"🤖  Building your learning roadmap for {target_career}…"):
        skill_analysis = st.session_state.get(
            f"skill_analysis_{target_career}", {}
        )
        roadmap = gemini.generate_roadmap(
            target_career, skill_analysis
        )

        if roadmap:
            st.session_state["learning_roadmap"] = roadmap

            db = DatabaseManager()
            db.save_roadmap(st.session_state["session_id"], roadmap, target_career)

            if "dashboard_data" not in st.session_state:
                st.session_state["dashboard_data"] = {}
            st.session_state["dashboard_data"]["roadmap"] = roadmap
        else:
            st.error("Unable to generate your roadmap right now. Please try again.")
            st.stop()

roadmap = st.session_state["learning_roadmap"]
phases = roadmap.get("phases", [])

# ── Summary ──────────────────────────────────────────────────────────────────
total_weeks = roadmap.get("total_weeks", sum(p.get("duration_weeks", 4) for p in phases))
total_resources = sum(len(p.get("resources", [])) for p in phases)
total_milestones = sum(len(p.get("milestones", [])) for p in phases)

st.html(
    f"""<div style="background:linear-gradient(135deg,rgba(224,122,95,.1),rgba(129,166,132,.06));
                border:1px solid rgba(224,122,95,.1);border-radius:14px;
                padding:1.2rem 1.5rem;margin-bottom:1.5rem;
                display:flex;justify-content:space-around;flex-wrap:wrap;text-align:center;">
        <div style="padding:.5rem 1rem;">
            <div style="font-size:2em;font-weight:700;color:#E07A5F;">
                {total_weeks}</div>
            <div style="color:#B8B2A7;font-size:.82em;">Weeks Total</div>
        </div>
        <div style="padding:.5rem 1rem;">
            <div style="font-size:2em;font-weight:700;color:#D4A373;">
                {len(phases)}</div>
            <div style="color:#B8B2A7;font-size:.82em;">Phases</div>
        </div>
        <div style="padding:.5rem 1rem;">
            <div style="font-size:2em;font-weight:700;color:#81A684;">
                {total_milestones}</div>
            <div style="color:#B8B2A7;font-size:.82em;">Milestones</div>
        </div>
        <div style="padding:.5rem 1rem;">
            <div style="font-size:2em;font-weight:700;color:#F5F1E8;">
                {total_resources}</div>
            <div style="color:#B8B2A7;font-size:.82em;">Resources</div>
        </div>
    </div>""")

# ── Gantt Chart ──────────────────────────────────────────────────────────────
if phases:
    st.html(
        """<div style="background:#1E1E1E;border:1px solid rgba(255,255,255,.05);
                    border-radius:14px;padding:1.2rem 1.5rem;margin-bottom:1rem;">
            <div style="color:#F5F1E8;font-size:1.05em;font-weight:700;">
                📅 Timeline Overview</div>
            <div style="color:#B8B2A7;font-size:.85em;">
                Visual breakdown of each learning phase</div>
        </div>""")

    phase_names = [p.get("name", f"Phase {i+1}") for i, p in enumerate(phases)]
    durations = [p.get("duration_weeks", 4) for p in phases]
    starts = []
    cum = 0
    for d in durations:
        starts.append(cum)
        cum += d

    colors = ["#E07A5F", "#D4A373", "#81A684", "#C9856E", "#B8956A"]

    fig = go.Figure()
    for i, (name, dur, start) in enumerate(zip(phase_names, durations, starts)):
        color = colors[i % len(colors)]
        fig.add_trace(go.Bar(
            x=[dur], y=[name], orientation="h",
            base=[start],
            marker_color=color,
            marker_line_width=0,
            text=[f"{dur} weeks"],
            textposition="inside",
            textfont_color="#fff",
        ))
    fig = themed_fig(fig)
    fig.update_layout(
        title=dict(
            text="Learning Roadmap Timeline",
            font=dict(size=18, color="#F5F1E8"),
            x=0.5,
        ),
        xaxis_title="Weeks",
        yaxis=dict(autorange="reversed", tickfont=dict(size=12, color="#F5F1E8")),
        xaxis=dict(tickfont=dict(size=11, color="#B8B2A7")),
        barmode="overlay",
        showlegend=False,
        height=360,
        margin=dict(t=60, b=50, l=30, r=30),
    )
    st.plotly_chart(fig, width="stretch")

# ── Phase Details ────────────────────────────────────────────────────────────
st.html(
    """<div style="margin:1.2rem 0 .6rem;">
        <h3 style="color:#F5F1E8;">Phase Details</h3>
    </div>""")

for idx, phase in enumerate(phases):
    name = phase.get("name", f"Phase {idx + 1}")
    weeks = phase.get("duration_weeks", "?")
    topics = phase.get("topics", [])
    milestones = phase.get("milestones", [])
    resources = phase.get("resources", [])
    color = colors[idx % len(colors)]

    with st.expander(f"Phase {idx+1}: {name}  ({weeks} weeks)", expanded=(idx == 0)):
        # Topics
        if topics:
            st.markdown("**Topics Covered**")
            for t in topics:
                st.markdown(f"• {t}")

        # Milestones
        if milestones:
            st.markdown("**Milestones**")
            for m in milestones:
                st.markdown(f"✅ {m}")

        # Resources
        if resources:
            st.markdown("**Resources**")
            for r in resources:
                if isinstance(r, dict):
                    title = r.get("title", r.get("name", "Resource"))
                    url = r.get("url", "")
                    if url:
                        st.markdown(f"🔗 [{title}]({url})")
                    else:
                        st.markdown(f"📚 {title}")
                else:
                    st.markdown(f"📚 {r}")

# ── Next Step ────────────────────────────────────────────────────────────────
st.divider()
c1, c2, c3 = st.columns([1, 2, 1])
with c2:
    if st.button("📄  Go to Resume Analyzer", type="primary",
                 width="stretch"):
        st.switch_page("pages/5_Resume_Analyzer.py")
