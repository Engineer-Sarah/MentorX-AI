"""
utils.py – Shared helpers, formatters, and constants for MentorX AI.
"""

import json
from pathlib import Path

import streamlit as st


DATA_DIR = Path(__file__).resolve().parent.parent / "data"

# Scale mapping: radio option text → numeric score
SCALE_MAP = {
    "Strongly Disagree": 1,
    "Disagree": 2,
    "Neutral": 3,
    "Agree": 4,
    "Strongly Agree": 5,
}
SCALE_OPTIONS = ["Strongly Disagree", "Disagree", "Neutral", "Agree", "Strongly Agree"]

# ---------------------------------------------------------------------------
# Demo fallbacks – keep the app usable if the Gemini API is unavailable
# ---------------------------------------------------------------------------

_FALLBACK_CAREERS = [
    {
        "title": "Software Engineer",
        "match_score": 88,
        "reasoning": "Your strong technical and analytical scores make engineering a natural fit.",
        "salary_range": "PKR 80,000 – 250,000/month",
        "growth_outlook": "High demand in Pakistan and globally, strong remote-work opportunities.",
        "key_skills": ["Python", "Problem Solving", "Git", "SQL"],
    },
    {
        "title": "Data Analyst",
        "match_score": 82,
        "reasoning": "You enjoy working with data, finding patterns, and communicating insights.",
        "salary_range": "PKR 60,000 – 180,000/month",
        "growth_outlook": "Growing rapidly across fintech, e-commerce, and telecom sectors.",
        "key_skills": ["Excel", "SQL", "Data Visualization", "Statistics"],
    },
    {
        "title": "UX/UI Designer",
        "match_score": 76,
        "reasoning": "Your creative and social strengths align well with user-centred design.",
        "salary_range": "PKR 50,000 – 160,000/month",
        "growth_outlook": "Strong freelance and startup demand.",
        "key_skills": ["Figma", "User Research", "Prototyping", "Visual Design"],
    },
]

_FALLBACK_SKILL_GAP = {
    "matched_skills": [
        {"skill": "Communication", "proficiency_note": "Solid foundation"},
        {"skill": "Problem Solving", "proficiency_note": "Good analytical ability"},
    ],
    "gap_skills": [
        {"skill": "Python", "priority": "Critical", "description": "Core language for most tech roles."},
        {"skill": "SQL", "priority": "Important", "description": "Essential for data and backend roles."},
        {"skill": "Project Management", "priority": "Nice-to-have", "description": "Useful for senior positions."},
    ],
    "overall_match_percentage": 45,
}

_FALLBACK_ROADMAP = {
    "phases": [
        {
            "name": "Phase 1: Foundations",
            "duration": "4 weeks",
            "description": "Build the core skills required for your target role.",
            "milestones": [
                {"title": "Learn Python basics", "resource": "freeCodeCamp Python (YouTube)", "resource_type": "Video", "estimated_hours": 20, "is_free": True},
                {"title": "SQL fundamentals", "resource": "SQLBolt interactive lessons", "resource_type": "Website", "estimated_hours": 10, "is_free": True},
            ],
        },
        {
            "name": "Phase 2: Core Skills",
            "duration": "6 weeks",
            "description": "Deepen your practical, job-ready abilities.",
            "milestones": [
                {"title": "Build 2 portfolio projects", "resource": "Kaggle datasets", "resource_type": "Dataset", "estimated_hours": 30, "is_free": True},
                {"title": "Learn Git & GitHub", "resource": "GitHub Skills", "resource_type": "Tutorial", "estimated_hours": 8, "is_free": True},
            ],
        },
        {
            "name": "Phase 3: Job Ready",
            "duration": "4 weeks",
            "description": "Prepare for applications and interviews.",
            "milestones": [
                {"title": "Polish resume & LinkedIn", "resource": "MentorX resume analyzer", "resource_type": "Tool", "estimated_hours": 5, "is_free": True},
                {"title": "Practice mock interviews", "resource": "MentorX mock interview", "resource_type": "Tool", "estimated_hours": 10, "is_free": True},
            ],
        },
    ],
    "total_estimated_hours": 83,
}

_FALLBACK_RESUME_FEEDBACK = {
    "overall_score": 60,
    "section_feedback": [
        {"section": "Summary", "score": 55, "comments": "Add a concise, role-focused summary.", "suggestions": "Tailor to target role"},
        {"section": "Skills", "score": 60, "comments": "Include more role-specific keywords.", "suggestions": "Python, SQL, communication"},
        {"section": "Experience", "score": 65, "comments": "Good, but quantify achievements.", "suggestions": "Add metrics and impact"},
    ],
    "ats_tips": ["Use standard section headings", "Add relevant keywords"],
    "top_improvements": ["Quantify achievements", "Tailor summary", "Add missing skills"],
    "strengths": ["Clear formatting", "Relevant experience"],
}

_FALLBACK_INTERVIEW_FEEDBACK = {
    "overall_score": 65,
    "question_breakdown": [],
    "top_tips": ["Use the STAR method", "Provide specific examples", "Quantify achievements"],
    "overall_impression": "Keep practicing structured answers with concrete examples.",
}


# ---------------------------------------------------------------------------
# Facade classes (adapt standalone backend functions for page use)
# ---------------------------------------------------------------------------

class AssessmentEngine:
    """Page-friendly wrapper around assessment_engine standalone functions."""

    def __init__(self):
        from src.assessment_engine import load_questions
        self.questions = load_questions()
        # Add "question" and "options" keys so pages can use q["question"] and q["options"]
        for q in self.questions:
            q.setdefault("question", q.get("statement", ""))
            q.setdefault("options", SCALE_OPTIONS)

    def evaluate(self, answers: dict) -> dict:
        """Convert text answers → numeric scores → interest_scores + traits."""
        from src.assessment_engine import compute_scores, derive_traits, PRIMARY_INTEREST_DIMENSIONS
        numeric = {}
        for qid, val in answers.items():
            if isinstance(val, str):
                numeric[str(qid)] = SCALE_MAP.get(val, 3)
            else:
                numeric[str(qid)] = int(val)
        all_scores = compute_scores(numeric)
        # derive_traits needs ALL dimensions (teamwork, leadership, etc.)
        personality_traits = derive_traits(all_scores)
        # Filter to the 5 primary interest dimensions for Gemini prompts,
        # dashboard radar chart, and career recommendations.
        interest_scores = {
            dim: all_scores[dim]
            for dim in PRIMARY_INTEREST_DIMENSIONS
            if dim in all_scores
        }
        return {
            "interest_scores": interest_scores,
            "personality_traits": personality_traits,
            "raw_answers": answers,
        }


class GeminiService:
    """Page-friendly wrapper around gemini_service standalone functions."""

    def __init__(self):
        from src.gemini_service import is_gemini_available
        self.is_available = is_gemini_available()

    def recommend_careers(self, assessment: dict, user_name: str = "") -> dict:
        from src.gemini_service import get_career_recommendations
        try:
            result = get_career_recommendations(
                assessment.get("interest_scores", {}),
                assessment.get("personality_traits", {}),
            )
        except RuntimeError:
            result = None
        api_failed = not result or not result.get("recommendations")
        if api_failed:
            result = {"recommendations": _FALLBACK_CAREERS}
        recs = result.get("recommendations", [])
        adapted = []
        for r in recs:
            adapted.append({
                "title": r.get("title", "Unknown"),
                "match_score": r.get("match_score", 0),
                "why_matches": r.get("reasoning", ""),
                "your_strengths": r.get("key_skills", []),
                "skill_gaps": [],
                "salary_range_pkr": r.get("salary_range", ""),
                "growth_outlook": r.get("growth_outlook", ""),
            })
        return {"recommended_careers": adapted, "demo": api_failed}

    def analyze_skill_gap(self, assessment: dict, target_career: str) -> dict:
        from src.gemini_service import analyze_skill_gap
        scores = assessment.get("interest_scores", {})
        current_skills = [
            dim.replace("_", " ").title()
            for dim, val in sorted(scores.items(), key=lambda x: x[1], reverse=True)
            if val >= 3.0
        ]
        if not current_skills:
            current_skills = ["General problem solving", "Communication"]
        try:
            result = analyze_skill_gap(target_career, current_skills)
        except RuntimeError:
            result = None
        api_failed = not result or (not result.get("matched_skills") and not result.get("gap_skills"))
        if api_failed:
            result = _FALLBACK_SKILL_GAP
        matched = result.get("matched_skills", [])
        gaps = result.get("gap_skills", [])
        comparison = []
        for s in matched:
            name = s.get("skill", "") if isinstance(s, dict) else str(s)
            if name:
                comparison.append({"skill": name, "current_level": 6, "required_level": 7})
        for s in gaps:
            name = s.get("skill", "") if isinstance(s, dict) else str(s)
            if name:
                comparison.append({"skill": name, "current_level": 3, "required_level": 8})
        return {
            "gap_analysis": {
                "overall_match_percentage": result.get("overall_match_percentage", 0),
                "skills_comparison": comparison,
                "matched_skills": matched,
                "gap_skills": gaps,
            },
            "demo": api_failed,
        }

    def generate_roadmap(self, target_career: str, skill_analysis: dict) -> dict:
        from src.gemini_service import generate_roadmap
        gap = skill_analysis.get("gap_analysis", {})
        gap_skills = gap.get("gap_skills", [])
        if not gap_skills:
            gap_skills = gap.get("skills_comparison", [])
        try:
            result = generate_roadmap(target_career, gap_skills)
        except RuntimeError:
            result = None
        api_failed = not result or not result.get("phases")
        if api_failed:
            result = _FALLBACK_ROADMAP
        phases_raw = result.get("phases", [])
        phases = []
        for i, p in enumerate(phases_raw):
            milestones_in = p.get("milestones", [])
            milestones = [m.get("title", "") for m in milestones_in if isinstance(m, dict)]
            resources = []
            for m in milestones_in:
                if isinstance(m, dict):
                    title = m.get("resource", m.get("title", ""))
                    url = m.get("url", "")
                    # Validate URL – must be a real HTTPS link
                    if not (isinstance(url, str) and url.startswith("https://") and len(url) > 10):
                        url = ""
                    # Smart fallback: recognise well-known resource names
                    if not url and title:
                        _t = title.lower()
                        if "freecodecamp" in _t:
                            url = "https://www.freecodecamp.org/"
                        elif "coursera" in _t:
                            url = "https://www.coursera.org/"
                        elif "kaggle" in _t:
                            url = "https://www.kaggle.com/learn"
                        elif "udemy" in _t:
                            url = "https://www.udemy.com/"
                        elif "youtube" in _t:
                            url = "https://www.youtube.com/results?search_query=" + title.replace(" ", "+")
                        elif "github" in _t:
                            url = "https://github.com/"
                        elif "sqlbolt" in _t:
                            url = "https://sqlbolt.com/"
                        elif "w3school" in _t:
                            url = "https://www.w3schools.com/"
                    resources.append({
                        "title": title,
                        "url": url,
                        "is_free": m.get("is_free", False),
                    })
            dur_str = p.get("duration", "")
            weeks = 4
            try:
                import re
                nums = re.findall(r"\d+", str(dur_str))
                if nums:
                    weeks = max(int(n) for n in nums)
            except Exception:
                pass
            hours = p.get("estimated_hours", 0)
            if not hours:
                hours = sum(m.get("estimated_hours", 10) for m in milestones_in if isinstance(m, dict))
            phases.append({
                "name": p.get("name", f"Phase {i+1}"),
                "duration_weeks": weeks,
                "duration": dur_str or f"{weeks} weeks",
                "description": p.get("description", ""),
                "topics": [m.get("title", "") for m in milestones_in if isinstance(m, dict)],
                "milestones": milestones,
                "resources": resources,
            })
        total_hrs = result.get("total_estimated_hours", 0)
        return {
            "phases": phases,
            "total_weeks": sum(p["duration_weeks"] for p in phases) or total_hrs // 10,
            "demo": api_failed,
        }

    def analyze_resume(self, parsed: dict, target_career: str = "") -> dict:
        from src.gemini_service import review_resume
        text = parsed.get("text", parsed.get("full_text", ""))
        if not text:
            return {"error": "No resume text found."}
        try:
            result = review_resume(text, target_career or "General")
        except RuntimeError:
            result = None
        api_failed = not result or not result.get("section_feedback")
        if api_failed:
            result = _FALLBACK_RESUME_FEEDBACK
        overall = result.get("overall_score", 0)
        section_fb = result.get("section_feedback", [])
        content_s = 50
        format_s = 50
        ats_s = 50
        for sf in section_fb:
            sec = sf.get("section", "").lower()
            sc = sf.get("score", 50)
            if "content" in sec or "experience" in sec or "summary" in sec:
                content_s = sc
            elif "skill" in sec:
                ats_s = sc
            elif "education" in sec or "format" in sec:
                format_s = sc
        suggestions = result.get("top_improvements", []) + result.get("ats_tips", [])
        strengths = result.get("strengths", [])
        keywords_found = []
        keywords_missing = []
        for sf in section_fb:
            sec = sf.get("section", "").lower()
            if "skill" in sec:
                comments = sf.get("comments", "").lower()
                if "missing" in comments or "add" in comments:
                    keywords_missing = [w.strip() for w in comments.split(",") if len(w.strip()) > 3][:5]
                else:
                    keywords_found = [w.strip() for w in sf.get("suggestions", "").split(",") if len(w.strip()) > 3][:5]
        return {
            "feedback": {
                "overall_score": overall,
                "scores": {
                    "content": content_s,
                    "formatting": format_s,
                    "ats_compatibility": ats_s,
                },
                "suggestions": suggestions[:8],
                "missing_keywords": keywords_missing,
                "found_keywords": keywords_found,
                "strengths": strengths,
            }
        }

    def generate_interview_question(self, target_career: str = "",
                                     history: list = None) -> str:
        from src.gemini_service import generate_interview_question
        q_num = len(history or []) + 1
        try:
            result = generate_interview_question(
                target_career or "Software Engineer", history or [], q_num
            )
        except RuntimeError:
            return ""
        return result.get("question", "") if result else ""

    def evaluate_interview_answer(self, question: str, answer: str,
                                   target_career: str = "") -> str:
        from src.gemini_service import evaluate_interview_answer
        try:
            result = evaluate_interview_answer(
                question, answer, target_career or "Software Engineer"
            )
        except RuntimeError:
            result = None
        if not result:
            # Context-aware offline fallback when API quota is exhausted
            role = target_career or "this"
            answer_len = len(answer.split()) if answer else 0
            strengths = ["You attempted the question."]
            improvements = []
            if answer_len < 15:
                improvements.append("Expand your answer with more detail — aim for 3-5 sentences.")
            if "example" not in answer.lower() and "instance" not in answer.lower():
                improvements.append(f"Add a concrete example from your experience relevant to {role} work.")
            if any(word in question.lower() for word in ["challenge", "problem", "difficult", "conflict"]):
                if "star" not in answer.lower() and not ("situation" in answer.lower() and "action" in answer.lower() and "result" in answer.lower()):
                    improvements.append("Use the STAR method: Situation, Task, Action, Result.")
            if not improvements:
                improvements.append(f"Connect your answer more directly to skills required for {role} roles.")
            result = {
                "score": 55 if answer_len >= 20 else 45,
                "strengths": strengths,
                "improvements": improvements[:2],
                "better_example": f"For a {role} role, a stronger answer would describe a specific situation, explain what you did, and share the outcome or what you learned.",
            }

        def _esc(text: str) -> str:
            return str(text).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

        score = result.get("score", 50)
        strengths = result.get("strengths", [])
        imps = result.get("improvements", [])
        example = result.get("better_example", "")

        html = f"<strong>Score:</strong> {score}/100"
        if strengths:
            html += f"<br><strong>Strengths:</strong> {_esc('; '.join(strengths))}"
        if imps:
            html += f"<br><strong>Improve:</strong> {_esc('; '.join(imps))}"
        if example:
            html += f"<br><strong>Better answer:</strong> {_esc(example)}"
        return html

    def generate_interview_feedback(self, history: list) -> dict:
        from src.gemini_service import generate_interview_summary
        conversation = []
        scores = []
        for entry in history:
            conversation.append({"role": "interviewer", "message": entry.get("question", "")})
            conversation.append({"role": "candidate", "message": entry.get("answer", "")})
            scores.append(50)
        try:
            result = generate_interview_summary("Software Engineer", conversation, scores)
        except RuntimeError:
            result = None
        if not result:
            result = _FALLBACK_INTERVIEW_FEEDBACK
        breakdown = result.get("question_breakdown", [])
        return {
            "overall_score": result.get("overall_score", 50),
            "strengths": result.get("top_tips", [])[:3],
            "areas_for_improvement": [result.get("overall_impression", "Keep practising!")],
        }


class DatabaseManager:
    """Page-friendly wrapper around database standalone functions."""

    def create_session(self, user_name: str) -> str:
        from src.database import init_db, create_session
        init_db()
        return create_session(user_name)

    def save_assessment(self, session_id: str, results: dict):
        from src.database import save_assessment
        save_assessment(
            session_id,
            results.get("raw_answers", {}),
            results.get("interest_scores", {}),
            results.get("personality_traits", {}),
        )

    def save_recommendation(self, session_id: str, recs: dict):
        """Save the recommendation list in the database's expected shape."""
        from src.database import save_recommendation
        save_recommendation(session_id, recs.get("recommended_careers", []))

    def save_skill_analysis(self, session_id: str, target_career: str, analysis: dict):
        from src.database import save_skill_analysis
        gap = analysis.get("gap_analysis", {})
        save_skill_analysis(
            session_id, target_career,
            gap.get("matched_skills", []),
            gap.get("gap_skills", []),
            gap,
        )

    def save_roadmap(self, session_id: str, roadmap: dict, target_career: str = ""):
        """Persist a roadmap together with its selected target career."""
        from src.database import save_roadmap
        save_roadmap(session_id, target_career, roadmap)

    def save_resume_analysis(self, session_id: str, result: dict):
        from src.database import save_resume
        save_resume(session_id, "", result.get("feedback", {}), "")

    def save_interview(self, session_id: str, feedback: dict):
        from src.database import save_interview
        save_interview(session_id, "", [], feedback)

    def get_session_data(self, session_id: str) -> dict:
        """Load dashboard data and normalize persisted wrapper shapes."""
        from src.database import init_db, get_dashboard_data
        init_db()

        data = get_dashboard_data(session_id)
        recommendation = data.get("recommendation")
        if recommendation:
            careers = recommendation.get("recommended_careers", [])
            # Support data saved by the earlier facade implementation, which
            # accidentally stored the wrapper dict inside this database field.
            if isinstance(careers, dict):
                careers = careers.get("recommended_careers", [])
            recommendation["recommended_careers"] = careers

        roadmap = data.get("roadmap")
        if roadmap and "roadmap_data" in roadmap:
            data["roadmap"] = roadmap.get("roadmap_data") or {}

        return data


class ResumeParser:
    """Page-friendly wrapper for resume text parsing."""

    def parse(self, uploaded_file) -> dict:
        """Extract text from a TXT, DOCX, or text-based PDF resume."""
        from io import BytesIO
        from src.resume_parser import clean_text, split_sections, get_resume_stats

        try:
            raw = uploaded_file.read()
        except Exception as exc:
            return {"error": f"Could not read the uploaded file: {exc}"}

        if len(raw) > 5 * 1024 * 1024:
            return {"error": "Resume files must be 5 MB or smaller."}

        file_name = getattr(uploaded_file, "name", "").lower()
        try:
            if file_name.endswith(".pdf"):
                from pypdf import PdfReader
                reader = PdfReader(BytesIO(raw))
                text = "\n".join(page.extract_text() or "" for page in reader.pages)
            elif file_name.endswith(".docx"):
                from docx import Document
                document = Document(BytesIO(raw))
                text = "\n".join(paragraph.text for paragraph in document.paragraphs)
            else:
                text = raw.decode("utf-8", errors="replace")
        except ImportError:
            return {"error": "PDF and DOCX support is not installed. Run `pip install -r requirements.txt` and restart the app."}
        except Exception as exc:
            return {"error": f"Could not extract text from this resume: {exc}"}

        text = clean_text(text)
        if len(text.strip()) < 50:
            return {"error": "No readable resume text was found. Upload a text-based PDF, DOCX, or TXT resume."}

        return {
            "text": text,
            "sections": split_sections(text),
            "stats": get_resume_stats(text),
        }


# ---------------------------------------------------------------------------
# Theme system
# ---------------------------------------------------------------------------

_THEME_CSS_INJECTED = False


def inject_theme():
    """Inject the MentorX AI warm charcoal / terracotta premium theme."""
    global _THEME_CSS_INJECTED
    if _THEME_CSS_INJECTED:
        return
    _THEME_CSS_INJECTED = True
    st.html(_THEME_CSS)


_THEME_CSS = """
<style>
/* ═══════════ GLOBAL ═══════════ */
[data-testid="stAppViewContainer"] > .main .block-container {
    padding-top: 2rem;
    padding-bottom: 2rem;
    max-width: 1200px;
}

/* ═══════════ TYPOGRAPHY ═══════════ */
h1, h2, h3 { font-weight: 700 !important; letter-spacing: -0.02em; }
h1 {
    background: linear-gradient(135deg, #E07A5F 0%, #D4A373 100%);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    background-clip: text; font-size: 2.4em !important; padding-bottom: .3rem;
}
h2 { color: #F5F1E8 !important; font-size: 1.55em !important; }
h3 { color: #E8E2D6 !important; font-size: 1.2em !important; }
p, li, span { color: #D4CFC4; }

/* ═══════════ SIDEBAR ═══════════ */
section[data-testid="stSidebar"] {
    background: #111111 !important;
    border-right: 1px solid rgba(255,255,255,.05);
}
section[data-testid="stSidebar"] h1,
section[data-testid="stSidebar"] h2,
section[data-testid="stSidebar"] h3 {
    background: none !important; -webkit-text-fill-color: unset !important;
    color: #F5F1E8 !important;
}
section[data-testid="stSidebar"] .stMarkdown { color: #B8B2A7; }
section[data-testid="stSidebar"] hr { border-color: rgba(255,255,255,.06); }

/* ═══════════ HORIZONTAL RULES ═══════════ */
.main hr {
    border: none; height: 1px; margin: 1.8rem 0;
    background: linear-gradient(90deg, transparent, rgba(224,122,95,.18), transparent);
}

/* ═══════════ PRIMARY BUTTON ═══════════ */
.stButton > button[kind="primary"],
.stDownloadButton > button[kind="primary"] {
    background: linear-gradient(135deg, #E07A5F, #C96B50) !important;
    color: #fff !important; border: none !important; border-radius: 10px !important;
    padding: .7rem 1.8rem !important; font-size: 1em !important; font-weight: 600 !important;
    box-shadow: 0 4px 16px rgba(224,122,95,.25) !important;
    transition: all .25s ease !important;
}
.stButton > button[kind="primary"]:hover,
.stDownloadButton > button[kind="primary"]:hover {
    transform: translateY(-1px) !important;
    box-shadow: 0 6px 22px rgba(224,122,95,.35) !important;
}

/* ═══════════ SECONDARY BUTTON ═══════════ */
.stButton > button[kind="secondary"],
.stDownloadButton > button[kind="secondary"] {
    background: rgba(224,122,95,.06) !important; color: #E07A5F !important;
    border: 1px solid rgba(224,122,95,.18) !important; border-radius: 8px !important;
}
.stButton > button[kind="secondary"]:hover {
    background: rgba(224,122,95,.12) !important;
}

/* ═══════════ INPUTS ═══════════ */
.stTextArea textarea, .stTextInput input, .stNumberInput input {
    background: #1E1E1E !important; color: #F5F1E8 !important;
    border: 1px solid rgba(255,255,255,.08) !important; border-radius: 8px !important;
}
.stTextArea textarea:focus, .stTextInput input:focus, .stNumberInput input:focus {
    border-color: #E07A5F !important; box-shadow: 0 0 0 2px rgba(224,122,95,.12) !important;
}

/* ═══════════ METRIC CARDS ═══════════ */
[data-testid="stMetric"] {
    background: #1E1E1E; border: 1px solid rgba(255,255,255,.05);
    border-radius: 12px; padding: 1rem 1.2rem;
}
[data-testid="stMetricLabel"] { color: #B8B2A7 !important; }
[data-testid="stMetricValue"] { color: #F5F1E8 !important; }

/* ═══════════ TABS ═══════════ */
.stTabs [data-baseweb="tab-list"] { gap: .3rem; }
.stTabs [data-baseweb="tab"] {
    background: #1E1E1E; border-radius: 8px 8px 0 0;
    color: #B8B2A7; padding: .5rem 1.1rem;
}
.stTabs [aria-selected="true"] {
    background: rgba(224,122,95,.08) !important;
    color: #E07A5F !important; border-bottom: 2px solid #E07A5F;
}

/* ═══════════ EXPANDERS ═══════════ */
[data-testid="stExpander"] {
    background: #1E1E1E; border: 1px solid rgba(255,255,255,.05);
    border-radius: 10px;
}
[data-testid="stExpander"] summary span { color: #F5F1E8 !important; }

/* ═══════════ CHAT MESSAGES ═══════════ */
[data-testid="stChatMessage"] {
    background: #1E1E1E !important;
    border: 1px solid rgba(255,255,255,.05); border-radius: 12px;
}

/* ═══════════ PROGRESS BAR ═══════════ */
[data-testid="stProgress"] > div {
    background: #252525 !important; border-radius: 8px; overflow: hidden;
}
[data-testid="stProgress"] > div > div > div {
    background: linear-gradient(90deg, #E07A5F, #D4A373) !important; border-radius: 8px;
}

/* ═══════════ ALERTS ═══════════ */
[data-testid="stAlert"] {
    border-radius: 10px !important; border: 1px solid rgba(255,255,255,.06) !important;
}

/* ═══════════ SELECTBOX / RADIO ═══════════ */
.stSelectbox > div > div, .stMultiSelect > div > div {
    background: #1E1E1E !important; color: #F5F1E8 !important;
    border: 1px solid rgba(255,255,255,.08) !important; border-radius: 8px !important;
}

/* ═══════════ RADIO PILLS ═══════════ */
div[role="radiogroup"] {
    gap: 6px !important; display: flex !important; flex-wrap: wrap !important;
}
div[role="radiogroup"] > label {
    background: #1E1E1E !important; border-radius: 8px !important;
    padding: .35rem .75rem !important; border: 1px solid rgba(255,255,255,.07) !important;
    transition: all .2s ease !important; cursor: pointer !important;
    color: #B8B2A7 !important;
}
div[role="radiogroup"] > label:hover {
    border-color: rgba(224,122,95,.3) !important;
    background: rgba(224,122,95,.05) !important;
    color: #F5F1E8 !important;
}
div[role="radiogroup"] > label[data-baseweb="radio"] {
    border-color: #E07A5F !important;
    background: rgba(224,122,95,.1) !important;
    color: #F5F1E8 !important;
}
div[role="radiogroup"] > label[data-baseweb="radio"] > div:first-child > div {
    background-color: #E07A5F !important;
    border-color: #E07A5F !important;
}

/* ═══════════ CHAT INPUT ═══════════ */
[data-testid="stChatInput"] textarea {
    background: #1E1E1E !important; color: #F5F1E8 !important;
    border: 1px solid rgba(255,255,255,.1) !important; border-radius: 12px !important;
}

/* ═══════════ CHECKBOX ═══════════ */
.stCheckbox > label { color: #D4CFC4 !important; }

/* ═══════════ SCROLLBAR ═══════════ */
::-webkit-scrollbar { width: 5px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: rgba(224,122,95,.2); border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: rgba(224,122,95,.35); }

/* ═══════════ PLOTLY ═══════════ */
.js-plotly-plot .plotly { border-radius: 12px; overflow: hidden; }

/* ═══════════ DOWNLOAD BUTTON ═══════════ */
.stDownloadButton > button {
    background: #1E1E1E !important; color: #E07A5F !important;
    border: 1px solid rgba(224,122,95,.18) !important; border-radius: 8px !important;
}

/* ═══════════ RESPONSIVE ═══════════ */
@media (max-width: 768px) {
    h1 { font-size: 1.8em !important; }
    h2 { font-size: 1.3em !important; }
    h3 { font-size: 1.05em !important; }
    [data-testid="stAppViewContainer"] > .main .block-container {
        padding-top: 1rem; padding-bottom: 1rem;
    }
}
</style>
"""


def themed_fig(fig):
    """Apply warm dark-theme layout to a Plotly figure and return it."""
    fig.update_layout(
        paper_bgcolor="#1E1E1E",
        plot_bgcolor="#151515",
        font_color="#B8B2A7",
        title_font_color="#F5F1E8",
        legend_font_color="#B8B2A7",
        margin=dict(t=50, b=30, l=30, r=30),
    )
    return fig


def gradient_card(title: str, value: str, subtitle: str = "",
                  gradient: str = "135deg, #E07A5F, #D4A373") -> str:
    """Return HTML for a premium gradient card."""
    sub_html = f"<div style='color:#B8B2A7;font-size:.88em;margin-top:6px'>{subtitle}</div>" if subtitle else ""
    return f"""
    <div style="text-align:center;padding:1.4rem 1rem;border-radius:12px;
                background:linear-gradient({gradient});
                box-shadow:0 4px 20px rgba(224,122,95,.18)">
        <div style="color:rgba(255,255,255,.82);font-size:.82em;text-transform:uppercase;
                    letter-spacing:.06em">{title}</div>
        <div style="color:#fff;font-size:2.1em;font-weight:700;margin:4px 0">{value}</div>
        {sub_html}
    </div>"""


# ---------------------------------------------------------------------------
# Score formatting
# ---------------------------------------------------------------------------

def score_color(score: int | float) -> str:
    """Return a hex colour based on score thresholds."""
    if score >= 75:
        return "#81A684"   # Sage green – great
    elif score >= 50:
        return "#D4A373"   # Warm amber – decent
    return "#E07A5F"       # Terracotta – needs work


def score_emoji(score: int | float) -> str:
    """Return an emoji indicator for a score."""
    if score >= 75:
        return "🟢"
    elif score >= 50:
        return "🟡"
    return "🔴"


def score_label(score: int | float) -> str:
    """Return a human-readable label for a score."""
    if score >= 85:
        return "Excellent"
    elif score >= 70:
        return "Good"
    elif score >= 50:
        return "Fair"
    return "Needs Improvement"


def short_label(name: str, max_len: int = 22) -> str:
    """Trim a long label so it fits cleanly on chart axes."""
    return name if len(name) <= max_len else name[: max_len - 1].rstrip() + "…"


# ---------------------------------------------------------------------------
# Career database helpers
# ---------------------------------------------------------------------------

def load_career_database() -> list[dict]:
    """Load the static career profiles from JSON."""
    path = DATA_DIR / "career_database.json"
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data.get("careers", [])


def get_career_info(title: str) -> dict | None:
    """Look up a career by title (case-insensitive)."""
    careers = load_career_database()
    for c in careers:
        if c["title"].lower() == title.lower():
            return c
    return None


# ---------------------------------------------------------------------------
# Readiness score calculator
# ---------------------------------------------------------------------------

def calculate_readiness_score(dashboard_data: dict) -> int:
    """
    Compute an overall career readiness score (0-100) from dashboard data.

    Weights:
      - Assessment completed:  10%
      - Recommendation done:   10%
      - Skill analysis done:   20% (match percentage contributes)
      - Roadmap generated:     15%
      - Resume score:          25%
      - Interview score:       20%
    """
    score = 0.0

    # Assessment (10%)
    if dashboard_data.get("assessment"):
        score += 10

    # Recommendation (10%)
    if dashboard_data.get("recommendation"):
        score += 10

    # Skill analysis (20%)
    sa = dashboard_data.get("skill_analysis")
    if sa:
        gap = sa.get("gap_analysis", {})
        match_pct = gap.get("overall_match_percentage", 50) if isinstance(gap, dict) else 50
        score += (match_pct / 100) * 20

    # Roadmap (15%)
    if dashboard_data.get("roadmap"):
        score += 15

    # Resume (25%)
    resume = dashboard_data.get("resume")
    if resume:
        fb = resume.get("feedback", {})
        resume_score = fb.get("overall_score", 50) if isinstance(fb, dict) else 50
        score += (resume_score / 100) * 25

    # Interview (20%)
    interview = dashboard_data.get("interview")
    if interview:
        fb = interview.get("feedback", {})
        interview_score = fb.get("overall_score", 50) if isinstance(fb, dict) else 50
        score += (interview_score / 100) * 20

    return round(score)


# ---------------------------------------------------------------------------
# Progress tracker
# ---------------------------------------------------------------------------

STEPS = [
    ("assessment",   "Career Assessment"),
    ("recommendation","Career Recommendation"),
    ("skill_analysis","Skill Gap Analysis"),
    ("roadmap",      "Learning Roadmap"),
    ("resume",       "Resume Analyzer"),
    ("interview",    "AI Mock Interview"),
]


def get_progress(dashboard_data: dict) -> list[dict]:
    """Return a list of step statuses for the progress tracker."""
    progress = []
    for key, label in STEPS:
        completed = dashboard_data.get(key) is not None
        progress.append({
            "step": label,
            "completed": completed,
            "icon": "✅" if completed else "⬜",
        })
    return progress


# ---------------------------------------------------------------------------
# Report export helper
# ---------------------------------------------------------------------------

def generate_text_report(dashboard_data: dict) -> str:
    """Generate a plain-text summary of the user's career coaching journey."""
    lines = []
    lines.append("=" * 50)
    lines.append("  MentorX AI – Career Readiness Report")
    lines.append("=" * 50)

    session = dashboard_data.get("session", {})
    lines.append(f"\nUser: {session.get('user_name', 'N/A')}")
    lines.append(f"Session: {session.get('session_id', 'N/A')}")
    lines.append(f"Started: {session.get('created_at', 'N/A')}")

    readiness = calculate_readiness_score(dashboard_data)
    lines.append(f"\nOverall Readiness Score: {readiness}/100")

    # Assessment
    assessment = dashboard_data.get("assessment")
    if assessment:
        lines.append("\n--- Career Assessment ---")
        scores = assessment.get("interest_scores", {})
        for dim, val in sorted(scores.items(), key=lambda x: x[1], reverse=True):
            lines.append(f"  {dim.replace('_', ' ').title()}: {val}/5")

    # Recommendation
    rec = dashboard_data.get("recommendation")
    if rec:
        lines.append("\n--- Career Recommendations ---")
        for r in rec.get("recommended_careers", []):
            lines.append(f"  {r.get('title', '?')} — {r.get('match_score', '?')}% match")

    # Skill Analysis
    sa = dashboard_data.get("skill_analysis")
    if sa:
        lines.append(f"\n--- Skill Gap Analysis ({sa.get('target_career', '')}) ---")
        gap = sa.get("gap_analysis", {})
        lines.append(f"  Match: {gap.get('overall_match_percentage', 'N/A')}%")

    # Resume
    resume = dashboard_data.get("resume")
    if resume:
        fb = resume.get("feedback", {})
        lines.append(f"\n--- Resume Score: {fb.get('overall_score', 'N/A')}/100 ---")

    # Interview
    interview = dashboard_data.get("interview")
    if interview:
        fb = interview.get("feedback", {})
        lines.append(f"\n--- Interview Score: {fb.get('overall_score', 'N/A')}/100 ---")

    lines.append("\n" + "=" * 50)
    lines.append("  Generated by MentorX AI – Pakistan's Career Coach")
    lines.append("=" * 50)

    return "\n".join(lines)
