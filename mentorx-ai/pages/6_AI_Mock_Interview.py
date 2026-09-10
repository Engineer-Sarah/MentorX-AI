"""
Page 6 – AI Mock Interview
"""

import streamlit as st
from datetime import datetime

import sys
from pathlib import Path

src_dir = Path(__file__).resolve().parent.parent
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

from src.utils import GeminiService, DatabaseManager, inject_theme

st.set_page_config(
    page_title="AI Mock Interview – MentorX AI",
    page_icon="🎤",
    layout="wide",
)

inject_theme()

MAX_QUESTIONS = 6

# ── Header ───────────────────────────────────────────────────────────────────
st.html(
    """
    <div style="margin-bottom:1rem;">
        <div style="color:#B8B2A7;font-size:.78em;text-transform:uppercase;
                    letter-spacing:.1em;margin-bottom:.3rem;">Step 6 of 7</div>
        <h1>🎤 AI Mock Interview</h1>
        <p style="color:#B8B2A7;font-size:.95em;">
            Practise interview questions with real-time AI coaching and feedback.</p>
    </div>
    """)

# ── Gate ─────────────────────────────────────────────────────────────────────
if "session_id" not in st.session_state:
    st.warning("Please start from the home page and enter your name first.")
    st.stop()

gemini = GeminiService()

# ── Session init ─────────────────────────────────────────────────────────────
if "interview_started" not in st.session_state:
    st.session_state["interview_started"] = False
    st.session_state["interview_history"] = []
    st.session_state["current_question"] = None
    st.session_state["interview_feedback"] = None
    st.session_state["question_count"] = 0

target_career = st.session_state.get("dashboard_data", {}).get("target_career", "")

# ── Start Screen ─────────────────────────────────────────────────────────────
if not st.session_state["interview_started"]:
    st.html(
        f"""<div style="background:#1E1E1E;border:1px solid rgba(255,255,255,.05);
                    border-radius:14px;padding:1.5rem 1.8rem;margin-bottom:1.5rem;">
            <div style="display:flex;align-items:center;gap:.5rem;margin-bottom:.8rem;">
                <span style="font-size:1.3em;">🎯</span>
                <span style="color:#F5F1E8;font-weight:700;font-size:1.1em;">
                    Interview Practice Session</span>
            </div>
            <p style="color:#B8B2A7;font-size:.9em;line-height:1.7;margin:0;">
                {"Practising for <strong style='color:#E07A5F;'>" + target_career + "</strong> interviews. " if target_career else ""}
                You'll receive {MAX_QUESTIONS} questions with AI coaching after each answer.
                Take your time and answer as you would in a real interview.</p>
            <div style="display:flex;gap:1.5rem;margin-top:1rem;">
                <div style="color:#B8B2A7;font-size:.85em;">
                    <span style="color:#E07A5F;font-weight:600;">{MAX_QUESTIONS}</span> Questions</div>
                <div style="color:#B8B2A7;font-size:.85em;">
                    <span style="color:#81A684;font-weight:600;">AI</span> Feedback each answer</div>
            </div>
        </div>""")

    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        if st.button("🎤  Start Interview", type="primary",
                     width="stretch"):
            st.session_state["interview_started"] = True
            st.session_state["interview_history"] = []
            st.session_state["question_count"] = 0
            st.session_state["interview_feedback"] = None

            # Get first question
            with st.spinner("Preparing your first question…"):
                question = gemini.generate_interview_question(
                    target_career=target_career,
                    history=[],
                )
            st.session_state["current_question"] = question or "Tell me about yourself and why you're interested in this role."
            st.rerun()

# ── Interview Active ─────────────────────────────────────────────────────────
if st.session_state["interview_started"]:
    q_count = st.session_state.get("question_count", 0)
    history = st.session_state.get("interview_history", [])

    # ── Progress bar ─────────────────────────────────────────────────────────
    pct = (q_count / MAX_QUESTIONS) * 100 if MAX_QUESTIONS else 0
    st.html(
        f"""<div style="display:flex;align-items:center;gap:.8rem;padding:.6rem 1rem;
                    background:#1E1E1E;border-radius:10px;
                    border:1px solid rgba(255,255,255,.05);margin-bottom:1rem;">
            <span style="color:#B8B2A7;font-size:.82em;">Question</span>
            <span style="color:#E07A5F;font-weight:700;font-size:1.1em;">
                {q_count + 1}</span>
            <span style="color:#706B63;font-size:.82em;">of {MAX_QUESTIONS}</span>
            <div style="flex:1;background:#252525;border-radius:4px;height:6px;
                        overflow:hidden;">
                <div style="background:linear-gradient(90deg,#E07A5F,#D4A373);
                            height:100%;width:{pct}%;border-radius:4px;"></div>
            </div>
        </div>""")

    # ── Display conversation history ────────────────────────────────────────
    for entry in history:
        # Question
        st.html(
            f"""<div style="background:#1E1E1E;border:1px solid rgba(255,255,255,.05);
                        border-radius:10px;padding:.8rem 1.2rem;margin-bottom:.5rem;">
                <div style="color:#B8B2A7;font-size:.72em;text-transform:uppercase;
                            letter-spacing:.08em;margin-bottom:.3rem;">Interviewer</div>
                <p style="color:#F5F1E8;font-size:.95em;margin:0;">{entry['question']}</p>
            </div>""")
        # Answer
        st.html(
            f"""<div style="background:rgba(224,122,95,.06);border:1px solid rgba(224,122,95,.1);
                        border-radius:10px;padding:.8rem 1.2rem;margin-bottom:.3rem;
                        margin-left:1.5rem;">
                <div style="color:#B8B2A7;font-size:.72em;text-transform:uppercase;
                            letter-spacing:.08em;margin-bottom:.3rem;">Your Answer</div>
                <p style="color:#D4CFC4;font-size:.92em;margin:0;">{entry['answer']}</p>
            </div>""")
        # Feedback
        if entry.get("feedback"):
            st.html(
                f"""<div style="background:#1E1E1E;border:1px solid rgba(129,166,132,.15);
                            border-radius:10px;padding:.8rem 1.2rem;margin-bottom:1rem;
                            margin-left:1.5rem;">
                    <div style="color:#81A684;font-size:.78em;font-weight:600;
                                margin-bottom:.3rem;">💡 AI Feedback</div>
                    <p style="color:#B8B2A7;font-size:.88em;margin:0;line-height:1.6;">
                        {entry['feedback']}</p>
                </div>""")

    # ── Current question ────────────────────────────────────────────────────
    current_q = st.session_state.get("current_question")

    if current_q and q_count < MAX_QUESTIONS:
        q_text = current_q if isinstance(current_q, str) else current_q.get(
            "question", ""
        )
        q_type = "" if isinstance(current_q, str) else current_q.get("type", "")

        st.html(
            f"""<div style="background:#1E1E1E;border:1px solid rgba(255,255,255,.05);
                        border-radius:12px;padding:1rem 1.5rem;margin-bottom:.5rem;">
                <div style="display:flex;justify-content:space-between;align-items:center;
                            margin-bottom:.5rem;">
                    <div style="color:#B8B2A7;font-size:.72em;text-transform:uppercase;
                                letter-spacing:.08em;">Current Question</div>
                    {f'<span style="background:rgba(212,163,115,.12);color:#D4A373;padding:.15rem .5rem;border-radius:5px;font-size:.72em;">{q_type}</span>' if q_type else ''}
                </div>
                <p style="color:#F5F1E8;font-size:1.05em;font-weight:600;
                          line-height:1.5;margin:0;">{q_text}</p>
            </div>""")

        user_answer = st.text_area(
            "Your answer", key=f"answer_{q_count}",
            placeholder="Type your answer here…", height=150,
            label_visibility="collapsed",
        )

        c1, c2 = st.columns([1, 1])
        with c1:
            if st.button("📤  Submit Answer", type="primary",
                         width="stretch"):
                if user_answer and user_answer.strip():
                    # Get feedback
                    with st.spinner("Evaluating your answer…"):
                        feedback = gemini.evaluate_interview_answer(
                            question=q_text,
                            answer=user_answer.strip(),
                            target_career=target_career,
                        )

                    st.session_state["interview_history"].append({
                        "question": q_text,
                        "answer": user_answer.strip(),
                        "feedback": feedback,
                    })
                    st.session_state["question_count"] += 1
                    st.session_state["current_question"] = None
                    st.rerun()
                else:
                    st.warning("Please type an answer before submitting.")

        with c2:
            if st.button("⏭  Skip Question", width="stretch"):
                st.session_state["interview_history"].append({
                    "question": q_text,
                    "answer": "(Skipped)",
                    "feedback": "You skipped this question.",
                })
                st.session_state["question_count"] += 1
                st.session_state["current_question"] = None
                st.rerun()

    # Generate next question after answer submitted
    if (st.session_state.get("current_question") is None
            and q_count < MAX_QUESTIONS):
        # Pass full Q&A history so Gemini can ask contextual, non-repeating questions
        history = [
            {"question": e["question"], "answer": e["answer"]}
            for e in st.session_state["interview_history"]
        ]
        with st.spinner("Preparing next question…"):
            question = gemini.generate_interview_question(
                target_career=target_career,
                history=history,
            )
        st.session_state["current_question"] = question or "What else would you like to share about your experience?"
        st.rerun()

    # ── Interview Complete ───────────────────────────────────────────────────
    if q_count >= MAX_QUESTIONS:
        st.divider()
        st.html(
            """<div style="text-align:center;margin:1rem 0;">
                <h2>🎉 Interview Complete!</h2>
                <p style="color:#B8B2A7;">
                    Great work finishing all questions. Here's your performance summary.</p>
            </div>""")

        # Generate final feedback
        if "interview_feedback" not in st.session_state or st.session_state["interview_feedback"] is None:
            with st.spinner("Generating your performance report…"):
                history_for_fb = [
                    {"question": e["question"], "answer": e["answer"]}
                    for e in st.session_state["interview_history"]
                    if e.get("answer") != "(Skipped)"
                ]
                fb = gemini.generate_interview_feedback(history_for_fb)
                if fb:
                    st.session_state["interview_feedback"] = fb
                    db = DatabaseManager()
                    db.save_interview(st.session_state["session_id"], fb)
                    if "dashboard_data" not in st.session_state:
                        st.session_state["dashboard_data"] = {}
                    st.session_state["dashboard_data"]["interview"] = {"feedback": fb}

        fb = st.session_state.get("interview_feedback", {})
        if fb:
            overall = fb.get("overall_score", 0)
            strengths = fb.get("strengths", [])
            improvements = fb.get("areas_for_improvement", [])

            # Score card
            from src.utils import score_color as sc
            st.html(
                f"""<div style="background:linear-gradient(135deg,rgba(224,122,95,.1),rgba(129,166,132,.06));
                            border:1px solid rgba(224,122,95,.1);border-radius:14px;
                            padding:1.5rem;text-align:center;margin-bottom:1.5rem;">
                    <div style="color:#B8B2A7;font-size:.75em;text-transform:uppercase;
                                letter-spacing:.1em;">Overall Interview Score</div>
                    <div style="font-size:3em;font-weight:700;color:{sc(overall)};
                                line-height:1.1;margin:.3rem 0;">{overall}%</div>
                </div>""")

            if strengths:
                st.html(
                    """<div style="background:#1E1E1E;border:1px solid rgba(129,166,132,.12);
                                border-radius:12px;padding:1rem 1.5rem;margin-bottom:.8rem;">
                        <div style="color:#81A684;font-weight:700;font-size:.95em;
                                    margin-bottom:.5rem;">💪 Strengths</div>
                    </div>""")
                for s in strengths:
                    st.html(
                        f"""<div style="padding:.4rem 0 .4rem 1.2rem;color:#D4CFC4;
                                    font-size:.9em;">
                            <span style="color:#81A684;">✓</span> {s}</div>""")

            if improvements:
                st.html(
                    """<div style="background:#1E1E1E;border:1px solid rgba(224,122,95,.12);
                                border-radius:12px;padding:1rem 1.5rem;margin-bottom:.8rem;">
                        <div style="color:#E07A5F;font-weight:700;font-size:.95em;
                                    margin-bottom:.5rem;">🎯 Areas for Improvement</div>
                    </div>""")
                for imp in improvements:
                    st.html(
                        f"""<div style="padding:.4rem 0 .4rem 1.2rem;color:#D4CFC4;
                                    font-size:.9em;">
                            <span style="color:#E07A5F;">→</span> {imp}</div>""")

        # Actions
        c1, c2, c3 = st.columns([1, 2, 1])
        with c1:
            if st.button("🔄  Practice Again", width="stretch"):
                st.session_state["interview_started"] = False
                st.session_state["interview_history"] = []
                st.session_state["current_question"] = None
                st.session_state["interview_feedback"] = None
                st.session_state["question_count"] = 0
                st.rerun()
        with c3:
            if st.button("📈  View Dashboard", type="primary",
                         width="stretch"):
                st.switch_page("pages/7_Career_Dashboard.py")
