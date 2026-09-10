"""
MentorX AI – Home Page
"""
import sys
from pathlib import Path

import streamlit as st

# Ensure the src/ package is on sys.path
src_dir = Path(__file__).resolve().parent
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

from src.utils import DatabaseManager, GeminiService, inject_theme

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="MentorX AI – Pakistan's Career Coach",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded",
)

inject_theme()

# ── Sidebar ──────────────────────────────────────────────────────────────────
with st.sidebar:
    # Branding
    try:
        st.image("assets/logo.png", width=120)
    except Exception:
        st.html(
            "<div style='font-size:2.2em;margin-bottom:.2rem;'>🎯</div>")
    st.html(
        "<h2 style='margin-top:0.3rem; margin-bottom:0; background:none !important; "
        "-webkit-text-fill-color: #E07A5F !important; font-size:1.45em !important;'>"
        "MentorX AI</h2>")
    st.html(
        "<p style='color:#81A684; font-size:.85em; margin-top:0.2rem;'>"
        "Pakistan's Personal Career Coach</p>")
    st.divider()

    # Navigation
    st.html("<h3 style='font-size:.95em !important; color:#B8B2A7 !important; "
                "text-transform:uppercase; letter-spacing:.08em;'>Navigate</h3>")
    st.html(
        """
        <a href="/" target="_self" style="color:#F5F1E8; text-decoration:none; display:block;
           padding:.45rem .6rem; border-radius:8px; margin-bottom:.15rem;
           transition:background .15s;">🏠 Home</a>
        """)
    nav_items = [
        ("📝", "1_Career_Assessment", "Career Assessment"),
        ("🎯", "2_Career_Recommendation", "Career Recommendation"),
        ("📊", "3_Skill_Gap_Analysis", "Skill Gap Analysis"),
        ("🗺", "4_Learning_Roadmap", "Learning Roadmap"),
        ("📄", "5_Resume_Analyzer", "Resume Analyzer"),
        ("🎤", "6_AI_Mock_Interview", "AI Mock Interview"),
        ("📈", "7_Career_Dashboard", "Career Dashboard"),
    ]
    for icon, page, label in nav_items:
        st.html(
            f'<a href="/{page}" target="_self" style="color:#D4CFC4; text-decoration:none; '
            f'display:block; padding:.45rem .6rem; border-radius:8px; margin-bottom:.15rem; '
            f'font-size:.92em; transition:background .15s;">{icon}  {label}</a>')

    st.divider()

    # User info card
    if st.session_state.get("user_name"):
        st.html(
            f"""<div style="background:#181818;border-radius:10px;padding:.8rem 1rem;
            border:1px solid rgba(255,255,255,.05);margin-bottom:1rem">
                <div style="color:#B8B2A7;font-size:.72em;text-transform:uppercase;
                    letter-spacing:.08em;">Logged In As</div>
                <div style="color:#F5F1E8;font-size:1.05em;font-weight:600;margin-top:3px;">
                    {st.session_state['user_name']}</div>
                <div style="color:#D4A373;font-size:.8em;margin-top:2px;">
                    Session: {st.session_state['session_id'][:8]}</div>
            </div>""")

    # How to use
    with st.expander("💡  How to Use"):
        st.markdown(
            """
            **Step 1** – Enter your name below  
            **Step 2** – Complete the Career Assessment  
            **Step 3** – Get personalized recommendations  
            **Step 4** – Analyse skill gaps & get a roadmap  
            **Step 5** – Upload your resume for AI review  
            **Step 6** – Practise with a mock interview  
            **Step 7** – View your full dashboard  
            """
        )

    # API status
    try:
        gemini = GeminiService()
        if gemini.is_available:
            st.html(
                "<p style='color:#81A684;font-size:.82em;'>● Gemini API Connected</p>")
        else:
            st.html(
                "<p style='color:#E07A5F;font-size:.82em;'>⚠ Gemini API Offline</p>")
    except Exception:
        st.html(
            "<p style='color:#D4A373;font-size:.82em;'>⚠ Check API configuration</p>")

# ── Hero Section ─────────────────────────────────────────────────────────────
st.html(
    """
    <div style="padding:2rem 2.2rem;border-radius:16px;
                background:#1E1E1E;border:1px solid rgba(255,255,255,.05);
                margin-bottom:1.5rem;">
        <div style="color:#B8B2A7;font-size:.8em;text-transform:uppercase;
                    letter-spacing:.12em;margin-bottom:.3rem;">MentorX AI</div>
        <h1 style="background:linear-gradient(135deg,#E07A5F 0%,#D4A373 50%,#81A684 100%);
                    -webkit-background-clip:text;-webkit-text-fill-color:transparent;
                    background-clip:text;font-size:2.6em !important;margin-bottom:.1rem;">
            MentorX AI</h1>
        <p style="color:#D4A373;font-size:1.15em;margin:0 0 .8rem;">
            Pakistan's Personal Career Coach</p>
        <p style="color:#B8B2A7;font-size:1em;line-height:1.7;max-width:680px;margin:0;">
            Your intelligent career companion. Discover your strengths, explore ideal
            career paths, build personalised learning roadmaps, and get AI-powered
            coaching — all in one platform.</p>
    </div>
    """)

# ── Name Input ───────────────────────────────────────────────────────────────
if st.session_state.get("user_name"):
    col1, col2, col3 = st.columns([1, 3, 1])
    with col2:
        st.html(
            f"""
            <div style="text-align:center;padding:1.2rem 1.5rem;border-radius:12px;
                        background:#1E1E1E;border:1px solid rgba(255,255,255,.05);
                        margin-bottom:1rem;">
                <div style="color:#B8B2A7;font-size:.85em;text-transform:uppercase;
                    letter-spacing:.08em;">Welcome back</div>
                <div style="font-size:1.8em;color:#F5F1E8;font-weight:700;">
                    {st.session_state['user_name']}</div>
                <div style="margin-top:.3rem;color:#B8B2A7;font-size:.9em;">
                    Continue your career coaching journey below</div>
            </div>
            """)
else:
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.html(
            "<div style='text-align:center;margin-bottom:.6rem;'>"
            "<div style='color:#B8B2A7;font-size:.8em;text-transform:uppercase;"
            "letter-spacing:.08em;'>Getting Started</div></div>")
        user_name = st.text_input("Enter your name to begin",
                                  placeholder="e.g. Ahmed Khan",
                                  label_visibility="collapsed")
        c1, c2, c3 = st.columns([1, 2, 1])
        with c2:
            if st.button("Start My Journey", type="primary",
                         width="stretch"):
                if user_name and user_name.strip():
                    db = DatabaseManager()
                    sid = db.create_session(user_name.strip())
                    st.session_state["session_id"] = sid
                    st.session_state["user_name"] = user_name.strip()
                    st.session_state["dashboard_data"] = {
                        "session": {
                            "session_id": sid,
                            "user_name": user_name.strip(),
                        }
                    }
                    st.rerun()
                else:
                    st.warning("Please enter your name to get started.")

# ── Career Journey Stepper ───────────────────────────────────────────────────
st.html(
    """
    <div style="margin:1.2rem 0 .5rem;">
        <div style="color:#F5F1E8;font-size:1.25em;font-weight:700;margin-bottom:.2rem;">
            Your Career Journey</div>
        <div style="color:#B8B2A7;font-size:.88em;margin-bottom:1.2rem;">
            Follow these 7 steps to unlock your full career potential</div>
    </div>
    """)

steps = [
    ("1", "Assessment",  "Discover your strengths & work style"),
    ("2", "Recommendation", "AI-powered career matches"),
    ("3", "Skill Gap",   "Compare your skills vs. industry needs"),
    ("4", "Roadmap",     "Personalised learning timeline"),
    ("5", "Resume",      "AI resume review & scoring"),
    ("6", "Mock Interview", "Practise with AI coaching"),
    ("7", "Dashboard",   "Track your career readiness"),
]

# Build stepper HTML
step_html = """
<div style="overflow-x:auto; white-space:nowrap; padding-bottom:1rem;">
<div style="display:inline-flex; gap:0; align-items:flex-start; min-width:max-content;">
"""

for i, (num, title, desc) in enumerate(steps):
    is_last = (i == len(steps) - 1)

    # Colors: sage for completed, terracotta for current, gray for upcoming
    if st.session_state.get("dashboard_data", {}).get(steps[i][1].lower().replace(" ", "_")):
        circle_bg = "#81A684"
        circle_border = "rgba(129,166,132,.3)"
        num_color = "#151515"
    elif i == 0:
        circle_bg = "#E07A5F"
        circle_border = "rgba(224,122,95,.3)"
        num_color = "#fff"
    else:
        circle_bg = "#2A2A2A"
        circle_border = "rgba(255,255,255,.08)"
        num_color = "#B8B2A7"

    step_html += f"""
    <div style="display:flex;flex-direction:column;align-items:center;
                min-width:140px;text-align:center;position:relative;">
        <div style="width:48px;height:48px;border-radius:50%;
                    background:{circle_bg};border:3px solid {circle_border};
                    display:flex;align-items:center;justify-content:center;
                    font-weight:700;font-size:1.1em;color:{num_color};
                    margin-bottom:10px;position:relative;z-index:2;">
            {num}</div>
        <div style="color:#F5F1E8;font-weight:600;font-size:.85em;
                    white-space:nowrap;margin-bottom:3px;">{title}</div>
        <div style="color:#B8B2A7;font-size:.75em;white-space:normal;
                    max-width:130px;line-height:1.4;">{desc}</div>
    </div>"""

    if not is_last:
        step_html += """
        <div style="width:50px;height:2px;margin-top:24px;flex-shrink:0;
                    background:linear-gradient(90deg,rgba(224,122,95,.25),rgba(212,163,115,.25));"></div>"""

step_html += "</div></div>"
st.html(step_html)

# ── Quick Stats ──────────────────────────────────────────────────────────────
st.divider()
if st.session_state.get("dashboard_data"):
    from src.utils import calculate_readiness_score, get_progress

    dashboard = st.session_state["dashboard_data"]
    readiness = calculate_readiness_score(dashboard)
    progress = get_progress(dashboard)
    completed_steps = sum(1 for p in progress if p["completed"])

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.html(
            f"""<div style="text-align:center;padding:1.2rem;border-radius:12px;
            background:#1E1E1E;border:1px solid rgba(255,255,255,.05);">
                <div style="color:#B8B2A7;font-size:.75em;text-transform:uppercase;
                    letter-spacing:.08em;">Readiness</div>
                <div style="font-size:2em;font-weight:700;color:#E07A5F;
                    margin:.3rem 0;">{readiness}%</div>
                <div style="color:#B8B2A7;font-size:.8em;">Career Score</div>
            </div>""")
    with c2:
        st.html(
            f"""<div style="text-align:center;padding:1.2rem;border-radius:12px;
            background:#1E1E1E;border:1px solid rgba(255,255,255,.05);">
                <div style="color:#B8B2A7;font-size:.75em;text-transform:uppercase;
                    letter-spacing:.08em;">Progress</div>
                <div style="font-size:2em;font-weight:700;color:#D4A373;
                    margin:.3rem 0;">{completed_steps}/6</div>
                <div style="color:#B8B2A7;font-size:.8em;">Steps Done</div>
            </div>""")
    with c3:
        rec = dashboard.get("recommendation")
        top_career = "—"
        if rec and rec.get("recommended_careers"):
            top_career = rec["recommended_careers"][0].get("title", "—")
        st.html(
            f"""<div style="text-align:center;padding:1.2rem;border-radius:12px;
            background:#1E1E1E;border:1px solid rgba(255,255,255,.05);">
                <div style="color:#B8B2A7;font-size:.75em;text-transform:uppercase;
                    letter-spacing:.08em;">Top Match</div>
                <div style="font-size:1.1em;font-weight:700;color:#81A684;
                    margin:.3rem 0;">{top_career}</div>
                <div style="color:#B8B2A7;font-size:.8em;">Best Career</div>
            </div>""")
    with c4:
        resume = dashboard.get("resume", {})
        ats_score = resume.get("feedback", {}).get("overall_score", "—") if resume else "—"
        st.html(
            f"""<div style="text-align:center;padding:1.2rem;border-radius:12px;
            background:#1E1E1E;border:1px solid rgba(255,255,255,.05);">
                <div style="color:#B8B2A7;font-size:.75em;text-transform:uppercase;
                    letter-spacing:.08em;">Resume</div>
                <div style="font-size:2em;font-weight:700;color:#E07A5F;
                    margin:.3rem 0;">{ats_score}</div>
                <div style="color:#B8B2A7;font-size:.8em;">ATS Score</div>
            </div>""")

# ── Footer ───────────────────────────────────────────────────────────────────
st.divider()
st.html(
    """
    <div style="text-align:center;padding:1.2rem 0;">
        <p style="color:#B8B2A7;font-size:.88em;">
            MentorX AI — Pakistan's Personal Career Coach<br>
            <span style="color:#706B63;font-size:.82em;">
            Powered by Google Gemini AI  •  Built for Pakistani students &amp; professionals</span>
        </p>
    </div>
    """)
