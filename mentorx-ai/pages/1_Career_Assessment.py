"""
Page 1 – Career Assessment
"""

import streamlit as st
import json
from pathlib import Path

import sys

src_dir = Path(__file__).resolve().parent.parent
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

from src.utils import AssessmentEngine, DatabaseManager, inject_theme, score_color, score_label

st.set_page_config(
    page_title="Career Assessment – MentorX AI",
    page_icon="📝",
    layout="wide",
)

inject_theme()

# ── Header ───────────────────────────────────────────────────────────────────
st.html(
    """
    <div style="margin-bottom:1rem;">
        <div style="color:#B8B2A7;font-size:.78em;text-transform:uppercase;
                    letter-spacing:.1em;margin-bottom:.3rem;">Step 1 of 7</div>
        <h1>📝 Career Assessment</h1>
        <p style="color:#B8B2A7;font-size:.95em;">
            Answer 20 questions to discover your professional strengths, work style
            and interests. This takes about 5 minutes.</p>
    </div>
    """)

# ── Gate ─────────────────────────────────────────────────────────────────────
if "session_id" not in st.session_state:
    st.warning("Please start from the home page and enter your name first.")
    st.stop()

# ── Load questions ───────────────────────────────────────────────────────────
engine = AssessmentEngine()
questions = engine.questions

if "assessment_answers" not in st.session_state:
    st.session_state["assessment_answers"] = {}

# ── Instructions ─────────────────────────────────────────────────────────────
st.html(
    """
    <div style="background:#1E1E1E;border:1px solid rgba(255,255,255,.05);
                border-radius:12px;padding:1.2rem 1.5rem;margin-bottom:1.2rem;">
        <div style="display:flex;align-items:center;gap:.5rem;margin-bottom:.5rem;">
            <span style="font-size:1.3em;">💡</span>
            <span style="color:#F5F1E8;font-weight:600;font-size:1em;">How it works</span>
        </div>
        <p style="color:#B8B2A7;font-size:.9em;line-height:1.6;margin:0;">
            Select the option that best describes you. There are no right or wrong answers —
            this assessment helps us understand your natural preferences and strengths.</p>
    </div>
    """)

# ── Questions ────────────────────────────────────────────────────────────────
current_category = None
category_icons = {
    "interests": "⭐",
    "work_style": "🏢",
    "skills": "💪",
    "values": "🎯",
}
category_labels = {
    "interests": "Your Interests",
    "work_style": "Work Style & Environment",
    "skills": "Skills & Strengths",
    "values": "Values & Goals",
}

for i, q in enumerate(questions):
    cat = q["category"]

    # Category header
    if cat != current_category:
        current_category = cat
        icon = category_icons.get(cat, "📌")
        label = category_labels.get(cat, cat.replace("_", " ").title())
        st.html(
            f"""<div style="display:flex;align-items:center;gap:.6rem;margin:1.5rem 0 .8rem;">
                <div style="width:4px;height:28px;border-radius:4px;
                            background:linear-gradient(180deg,#E07A5F,#D4A373);"></div>
                <span style="font-size:1.1em;">{icon}</span>
                <h3 style="margin:0;font-size:1.1em;color:#F5F1E8;">{label}</h3>
            </div>""")

    qid = q["id"]
    saved = st.session_state["assessment_answers"].get(qid, q["options"][0])

    st.html(
        f"<p style='color:#F5F1E8;font-weight:600;margin-bottom:.3rem;'>"
        f"Q{i+1}. {q['question']}</p>")

    answer = st.radio(
        str(qid), options=q["options"],
        index=q["options"].index(saved) if saved in q["options"] else 0,
        key=f"q_{qid}", label_visibility="collapsed",
        horizontal=True,
    )
    st.session_state["assessment_answers"][qid] = answer
    st.markdown("---")

# ── Submit ───────────────────────────────────────────────────────────────────
st.html(
    """<div style="text-align:center;margin:1.5rem 0 .8rem;">
        <p style="color:#B8B2A7;font-size:.9em;">
            Ready? Submit to get your personalised career profile.</p>
    </div>""")

c1, c2, c3 = st.columns([1, 2, 1])
with c2:
    if st.button("🎯  Get My Career Profile", type="primary",
                 width="stretch"):
        answers = st.session_state["assessment_answers"]
        results = engine.evaluate(answers)

        # Save to database
        db = DatabaseManager()
        db.save_assessment(st.session_state["session_id"], results)

        # Store in session
        st.session_state["assessment_results"] = results

        # Update dashboard
        if "dashboard_data" not in st.session_state:
            st.session_state["dashboard_data"] = {}
        st.session_state["dashboard_data"]["assessment"] = results
        st.session_state["assessment_completed"] = True

        st.rerun()

# ── Results ──────────────────────────────────────────────────────────────────
if "assessment_results" in st.session_state:
    results = st.session_state["assessment_results"]

    st.html(
        """<div style="margin:1rem 0 .5rem;">
            <h2>📊 Your Assessment Results</h2>
            <p style="color:#B8B2A7;font-size:.9em;">
                Here's what we discovered about your professional profile</p>
        </div>""")

    # Interest scores
    scores = results.get("interest_scores", {})
    if scores:
        st.html(
            """<div style="background:#1E1E1E;border:1px solid rgba(255,255,255,.05);
                        border-radius:12px;padding:1.2rem 1.5rem;margin-bottom:1rem;">
                <div style="color:#F5F1E8;font-weight:700;font-size:1.05em;
                            margin-bottom:.8rem;">Interest Profile</div>
            </div>""")

        sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        for dim, score in sorted_scores:
            color = score_color(score * 20)
            label = score_label(score * 20)
            pct = score / 5 * 100
            dim_label = dim.replace("_", " ").title()

            st.html(
                f"""<div style="margin-bottom:.8rem;">
                    <div style="display:flex;justify-content:space-between;align-items:center;
                                margin-bottom:4px;">
                        <span style="color:#F5F1E8;font-weight:500;font-size:.9em;">
                            {dim_label}</span>
                        <span style="color:{color};font-weight:600;font-size:.85em;">
                            {score}/5  ·  {label}</span>
                    </div>
                    <div style="background:#252525;border-radius:6px;height:8px;overflow:hidden;">
                        <div style="background:linear-gradient(90deg,{color},{color});
                                    height:100%;width:{pct}%;border-radius:6px;"></div>
                    </div>
                </div>""")

    # Personality traits
    traits = results.get("personality_traits", {})
    if traits:
        st.html(
            """<div style="margin-top:1.2rem;margin-bottom:.8rem;">
                <h3 style="color:#F5F1E8;">Personality Profile</h3>
            </div>""")
        cols = st.columns(3)
        trait_items = list(traits.items())
        for idx, (trait, desc) in enumerate(trait_items):
            with cols[idx % 3]:
                st.html(
                    f"""<div style="background:#1E1E1E;border:1px solid rgba(224,122,95,.12);
                                border-radius:10px;padding:.9rem 1rem;text-align:center;">
                        <div style="color:#E07A5F;font-size:1.05em;font-weight:700;
                                    margin-bottom:.3rem;">{trait.replace('_', ' ').title()}</div>
                        <div style="color:#B8B2A7;font-size:.82em;line-height:1.5;">
                                    {desc}</div>
                    </div>""")

    # Summary
    summary = results.get("summary", "")
    if summary:
        st.html(
            f"""<div style="background:#1E1E1E;border:1px solid rgba(255,255,255,.05);
                        border-radius:12px;padding:1.2rem 1.5rem;margin-top:1rem;">
                <div style="color:#F5F1E8;font-weight:700;font-size:1.05em;
                            margin-bottom:.5rem;">Summary</div>
                <p style="color:#B8B2A7;font-size:.9em;line-height:1.7;margin:0;">
                    {summary}</p>
            </div>""")

    # Next step
    st.html(
        """<div style="text-align:center;margin:1.5rem 0;">
            <p style="color:#B8B2A7;font-size:.9em;">
                ✅ Assessment complete! Head to Career Recommendation next.</p>
        </div>""")

    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        if st.button("🎯  Go to Career Recommendation", type="primary",
                     width="stretch"):
            st.switch_page("pages/2_Career_Recommendation.py")
