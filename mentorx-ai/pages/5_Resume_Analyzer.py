"""
Page 5 – Resume Analyzer
"""

import streamlit as st
import plotly.graph_objects as go

import sys
from pathlib import Path

src_dir = Path(__file__).resolve().parent.parent
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

from src.utils import GeminiService, ResumeParser, DatabaseManager, inject_theme, themed_fig, score_color, score_label

st.set_page_config(
    page_title="Resume Analyzer – MentorX AI",
    page_icon="📄",
    layout="wide",
)

inject_theme()

# ── Header ───────────────────────────────────────────────────────────────────
st.html(
    """
    <div style="margin-bottom:1rem;">
        <div style="color:#B8B2A7;font-size:.78em;text-transform:uppercase;
                    letter-spacing:.1em;margin-bottom:.3rem;">Step 5 of 7</div>
        <h1>📄 Resume Analyzer</h1>
        <p style="color:#B8B2A7;font-size:.95em;">
            Upload your resume for an AI-powered ATS compatibility review with
            actionable improvement tips.</p>
    </div>
    """)

# ── Gate ─────────────────────────────────────────────────────────────────────
if "session_id" not in st.session_state:
    st.warning("Please start from the home page and enter your name first.")
    st.stop()

# ── Instructions ─────────────────────────────────────────────────────────────
st.html(
    """
    <div style="background:#1E1E1E;border:1px solid rgba(255,255,255,0.05);
                border-radius:12px;padding:1.2rem 1.5rem;margin-bottom:1.2rem;">
        <div style="display:flex;align-items:center;gap:.5rem;margin-bottom:.5rem;">
            <span style="font-size:1.3em;">📎</span>
            <span style="color:#F5F1E8;font-weight:600;font-size:1em;">
                Upload your resume</span>
        </div>
        <p style="color:#B8B2A7;font-size:.88em;line-height:1.6;margin:0;">
            Supported formats: PDF, DOCX or TXT. Max 5 MB. Your file is processed
            securely and never stored permanently.</p>
    </div>
    """)

# ── File Upload ──────────────────────────────────────────────────────────────
uploaded = st.file_uploader(
    "Choose file", type=["pdf", "docx", "txt"], label_visibility="collapsed"
)

c1, c2, c3 = st.columns([1, 2, 1])
with c2:
    analyze_btn = st.button("🔍  Analyse Resume", type="primary",
                            width="stretch", disabled=uploaded is None)

if analyze_btn and uploaded:
    parser = ResumeParser()
    parsed = parser.parse(uploaded)

    if parsed.get("error"):
        st.error(parsed["error"])
        st.stop()

    gemini = GeminiService()
    target = st.session_state.get("dashboard_data", {}).get("target_career", "")

    with st.spinner("🤖  Analysing your resume with AI…"):
        result = gemini.analyze_resume(parsed, target_career=target)

    if result:
        st.session_state["resume_analysis"] = result
        db = DatabaseManager()
        db.save_resume_analysis(st.session_state["session_id"], result)
        if "dashboard_data" not in st.session_state:
            st.session_state["dashboard_data"] = {}
        st.session_state["dashboard_data"]["resume"] = result
    else:
        st.error("Unable to analyse your resume right now. Please try again.")
        st.stop()

# ── Display Results ──────────────────────────────────────────────────────────
if "resume_analysis" in st.session_state:
    result = st.session_state["resume_analysis"]
    fb = result.get("feedback", {})
    overall = fb.get("overall_score", 0)
    color = score_color(overall)

    # ATS Score Gauge
    st.html(
        f"""<div style="text-align:center;margin:1rem 0 .5rem;">
            <h2>Resume Analysis Results</h2>
        </div>""")

    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=overall,
        number={"font": {"color": color, "size": 60}, "suffix": "%"},
        title={"text": "Resume Score", "font": {"color": "#B8B2A7", "size": 14}},
        gauge={
            "axis": {"range": [0, 100], "tickcolor": "#B8B2A7",
                     "tickfont": {"color": "#B8B2A7"}},
            "bar": {"color": color},
            "bgcolor": "#252525",
            "steps": [
                {"range": [0, 40], "color": "rgba(224,122,95,0.10)"},
                {"range": [40, 70], "color": "rgba(212,163,115,0.10)"},
                {"range": [70, 100], "color": "rgba(129,166,132,0.10)"},
            ],
            "threshold": {
                "line": {"color": "#F5F1E8", "width": 3},
                "thickness": 0.8, "value": overall,
            },
        },
    ))
    fig = themed_fig(fig)
    fig.update_layout(height=280)
    st.plotly_chart(fig, width="stretch")

    # Metric cards
    c1, c2, c3 = st.columns(3)
    scores = fb.get("scores", {})

    with c1:
        content_s = scores.get("content", 0)
        st.html(
            f"""<div style="background:#1E1E1E;border:1px solid rgba(255,255,255,0.05);
                        border-radius:12px;padding:1rem 1.2rem;text-align:center;">
                <div style="color:#B8B2A7;font-size:.75em;text-transform:uppercase;
                            letter-spacing:.08em;">Content</div>
                <div style="font-size:2em;font-weight:700;color:{score_color(content_s)};
                            margin:.3rem 0;">{content_s}%</div>
                <div style="color:#B8B2A7;font-size:.8em;">{score_label(content_s)}</div>
            </div>""")
    with c2:
        format_s = scores.get("formatting", 0)
        st.html(
            f"""<div style="background:#1E1E1E;border:1px solid rgba(255,255,255,0.05);
                        border-radius:12px;padding:1rem 1.2rem;text-align:center;">
                <div style="color:#B8B2A7;font-size:.75em;text-transform:uppercase;
                            letter-spacing:.08em;">Formatting</div>
                <div style="font-size:2em;font-weight:700;color:{score_color(format_s)};
                            margin:.3rem 0;">{format_s}%</div>
                <div style="color:#B8B2A7;font-size:.8em;">{score_label(format_s)}</div>
            </div>""")
    with c3:
        ats_s = scores.get("ats_compatibility", 0)
        st.html(
            f"""<div style="background:#1E1E1E;border:1px solid rgba(255,255,255,0.05);
                        border-radius:12px;padding:1rem 1.2rem;text-align:center;">
                <div style="color:#B8B2A7;font-size:.75em;text-transform:uppercase;
                            letter-spacing:.08em;">ATS Compatible</div>
                <div style="font-size:2em;font-weight:700;color:{score_color(ats_s)};
                            margin:.3rem 0;">{ats_s}%</div>
                <div style="color:#B8B2A7;font-size:.8em;">{score_label(ats_s)}</div>
            </div>""")

    # Suggestions
    suggestions = fb.get("suggestions", [])
    if suggestions:
        st.html(
            """<div style="margin:1.2rem 0 .5rem;">
                <h3 style="color:#F5F1E8;">💡 Suggestions for Improvement</h3>
            </div>""")
        for i, s in enumerate(suggestions, 1):
            st.html(
                f"""<div style="background:#1E1E1E;border:1px solid rgba(255,255,255,0.04);
                            border-radius:10px;padding:.8rem 1.2rem;margin-bottom:.5rem;">
                    <span style="color:#E07A5F;font-weight:600;margin-right:.4rem;">
                        {i}.</span>
                    <span style="color:#D4CFC4;font-size:.92em;">{s}</span>
                </div>""")

    # Keywords
    missing = fb.get("missing_keywords", [])
    found = fb.get("found_keywords", [])
    if found or missing:
        st.html(
            """<div style="margin:1.2rem 0 .5rem;">
                <h3 style="color:#F5F1E8;">🔑 Keyword Analysis</h3>
            </div>""")
        if found:
            tags = " ".join(
                f"<span style='background:rgba(129,166,132,0.12);color:#81A684;"
                f"padding:.2rem .6rem;border-radius:6px;font-size:.82em;"
                f"margin:.2rem .3rem;display:inline-block;'>{k}</span>"
                for k in found
            )
            st.html(f"<div style='margin-bottom:.5rem;'>{tags}</div>")
        if missing:
            tags = " ".join(
                f"<span style='background:rgba(224,122,95,0.10);color:#E07A5F;"
                f"padding:.2rem .6rem;border-radius:6px;font-size:.82em;"
                f"margin:.2rem .3rem;display:inline-block;'>{k}</span>"
                for k in missing
            )
            st.html(tags)

    # Strengths
    strengths = fb.get("strengths", [])
    if strengths:
        st.html(
            """<div style="margin:1.2rem 0 .5rem;">
                <h3 style="color:#F5F1E8;">💪 Resume Strengths</h3>
            </div>""")
        for s in strengths:
            st.html(
                f"""<div style="background:#1E1E1E;border:1px solid rgba(129,166,132,.12);
                            border-radius:10px;padding:.7rem 1.2rem;margin-bottom:.4rem;">
                    <span style="color:#81A684;font-weight:600;margin-right:.4rem;">✓</span>
                    <span style="color:#D4CFC4;font-size:.92em;">{s}</span>
                </div>""")

# ── Next Step ────────────────────────────────────────────────────────────────
st.divider()
c1, c2, c3 = st.columns([1, 2, 1])
with c2:
    if st.button("🎤  Go to AI Mock Interview", type="primary",
                 width="stretch"):
        st.switch_page("pages/6_AI_Mock_Interview.py")
