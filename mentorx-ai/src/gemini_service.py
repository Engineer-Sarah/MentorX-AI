"""
gemini_service.py – All Google Gemini API interactions for MentorX AI.
Every LLM call is centralised here with structured JSON prompts.
"""

import os
import json
import re
import time
import warnings
from pathlib import Path

with warnings.catch_warnings():
    warnings.simplefilter("ignore", FutureWarning)
    import google.generativeai as genai
from dotenv import load_dotenv

# ---------------------------------------------------------------------------
# Load environment variables – resolve .env relative to THIS file so the key
# is found regardless of the working directory Streamlit was launched from.
# ---------------------------------------------------------------------------

_ENV_PATH = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=_ENV_PATH)

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

MODEL_NAME = "gemini-3.5-flash"

_GENERATION_CONFIG = {
    "temperature": 0.7,
    "top_p": 0.95,
    "top_k": 40,
    "max_output_tokens": 4096,
}


def _get_api_key() -> str:
    """Retrieve the Gemini API key from environment or Streamlit secrets."""
    key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY", "")
    if key:
        return key
    # Fallback to Streamlit secrets (available when deployed on Streamlit Cloud)
    try:
        import streamlit as _st
        key = _st.secrets.get("GEMINI_API_KEY", "")
        if not key:
            key = _st.secrets.get("GOOGLE_API_KEY", "")
    except Exception:
        pass
    return key


API_KEY = _get_api_key()

if API_KEY:
    genai.configure(api_key=API_KEY)

_model = (
    genai.GenerativeModel(MODEL_NAME, generation_config=_GENERATION_CONFIG)
    if API_KEY
    else None
)


def is_gemini_available() -> bool:
    """Return True when the Gemini model is initialised and ready."""
    return _model is not None


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_MAX_RETRIES = 2
_RETRY_DELAY = 1  # seconds


def _call_gemini(prompt: str) -> str:
    """Send a prompt to Gemini and return the raw text response.

    Retries transient errors (rate-limits, temporary server errors) up to
    ``_MAX_RETRIES`` additional attempts with exponential back-off.
    Authentication errors (invalid key) are raised immediately as
    ``RuntimeError`` so callers can show a clear setup message.
    """
    if not _model:
        raise RuntimeError(
            "Google Gemini API key not configured. "
            "Please add your key to the .env file:\n"
            "  GEMINI_API_KEY=your_actual_key_here\n"
            "Get a key from https://aistudio.google.com/app/apikey"
        )

    last_error: Exception | None = None
    for attempt in range(_MAX_RETRIES + 1):
        try:
            response = _model.generate_content(prompt)
            return response.text
        except Exception as exc:
            last_error = exc
            error_msg = str(exc).lower()

            # Authentication / key errors must never be silently swallowed
            if any(token in error_msg for token in (
                "api_key_invalid", "api key not valid", "invalid api key",
                "api_key_expired",
            )):
                raise RuntimeError(
                    "The Gemini API key in your .env file is invalid or expired. "
                    "Please update it:\n"
                    "  GEMINI_API_KEY=your_actual_key_here\n"
                    "Get a new key from https://aistudio.google.com/app/apikey"
                ) from exc

            # Model-not-found / decommissioned model errors
            if any(token in error_msg for token in (
                "no longer available", "not found", "404",
            )):
                raise RuntimeError(
                    "The Gemini model is no longer available. "
                    "Please update MODEL_NAME in src/gemini_service.py "
                    "to a current model (e.g. gemini-3.5-flash).\n"
                    f"Original error: {exc}"
                ) from exc

            # Only retry on transient / rate-limit errors
            is_transient = any(
                token in error_msg
                for token in ("429", "500", "503", "504", "resource", "quota", "rate", "overloaded")
            )
            if is_transient and attempt < _MAX_RETRIES:
                time.sleep(_RETRY_DELAY * (2 ** attempt))
                continue
            raise

    # Should not normally reach here, but just in case
    raise last_error  # type: ignore[misc]


def _parse_json(text: str) -> dict | list:
    """Extract JSON from a Gemini response, handling markdown fences and
    leading/trailing prose around the JSON block."""
    # 1. Try stripping ```json ... ``` wrappers first
    match = re.search(r"```(?:json)?\s*([\s\S]*?)```", text)
    if match:
        text = match.group(1).strip()

    # 2. Try parsing directly
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # 3. Fall back: find the first { or [ and match to its closing pair
    for start_char, end_char in [("{", "}"), ("[", "]")]:
        start = text.find(start_char)
        if start == -1:
            continue
        # Walk from the end backwards to find the matching closer
        end = text.rfind(end_char)
        if end > start:
            candidate = text[start : end + 1]
            try:
                return json.loads(candidate)
            except json.JSONDecodeError:
                continue

    raise ValueError(f"Could not extract JSON from Gemini response: {text[:200]}...")


def _safe_call(prompt: str, fallback=None):
    """Call Gemini, parse JSON, and return fallback on transient errors.

    ``RuntimeError`` (missing or invalid API key) always propagates so
    pages can display a clear setup instruction instead of a generic
    "try again later" message.
    """
    try:
        raw = _call_gemini(prompt)
        return _parse_json(raw)
    except RuntimeError:
        # API key missing or invalid – propagate immediately
        raise
    except Exception as e:
        print(f"[GeminiService Error] {e}")
        return fallback



# =========================================================================
# 1. Career Recommendations
# =========================================================================

def get_career_recommendations(interest_scores: dict, personality_traits: dict) -> dict:
    """
    Given assessment scores, return top 5 career recommendations.

    Returns dict with key "recommendations": list of objects with:
      - title, match_score (0-100), reasoning, salary_range (PKR),
        growth_outlook, key_skills (list)
    """
    prompt = f"""You are MentorX AI, a career coach specialising in the Pakistani job market.

A user has completed a career assessment. Here are their results:

Interest Scores (1-5 scale):
{json.dumps(interest_scores, indent=2)}

Personality Traits:
{json.dumps(personality_traits, indent=2)}

Based on this profile, recommend the TOP 5 careers that best fit this person.
Focus on careers relevant to Pakistan's growing economy (tech, freelancing, startups, remote work).

Return ONLY valid JSON in this exact format:
{{
  "recommendations": [
    {{
      "title": "Career Title",
      "match_score": 85,
      "reasoning": "Why this career fits the profile...",
      "salary_range": "PKR 80,000 - 200,000/month",
      "growth_outlook": "High demand in Pakistan and globally",
      "key_skills": ["Skill 1", "Skill 2", "Skill 3"]
    }}
  ]
}}

Ensure match_score is a realistic integer 0-100. Provide detailed reasoning."""

    return _safe_call(prompt, {"recommendations": []})


# =========================================================================
# 2. Skill Gap Analysis
# =========================================================================

def analyze_skill_gap(target_career: str, current_skills: list) -> dict:
    """
    Compare user's current skills against requirements for target_career.

    Returns dict with:
      - matched_skills: list of {skill, proficiency_note}
      - gap_skills: list of {skill, priority: "Critical"|"Important"|"Nice-to-have", description}
      - overall_match_percentage: int
    """
    prompt = f"""You are MentorX AI, a career coach for the Pakistani job market.

Target Career: {target_career}

User's Current Skills:
{json.dumps(current_skills, indent=2)}

Analyse the skill gap between what the user has and what is required for a
{target_career} role in Pakistan's job market.

Return ONLY valid JSON in this exact format:
{{
  "matched_skills": [
    {{"skill": "Python", "proficiency_note": "Foundational – needs advanced practice"}}
  ],
  "gap_skills": [
    {{"skill": "Machine Learning", "priority": "Critical", "description": "Core requirement for most {target_career} roles in Pakistan"}},
    {{"skill": "SQL", "priority": "Important", "description": "Needed for data pipeline work"}}
  ],
  "overall_match_percentage": 35
}}

Include 3-6 matched skills and 5-10 gap skills.
Priority levels: "Critical" (must-have), "Important" (strongly recommended), "Nice-to-have"."""

    return _safe_call(
        prompt,
        {"matched_skills": [], "gap_skills": [], "overall_match_percentage": 0},
    )


# =========================================================================
# 3. Learning Roadmap
# =========================================================================

def generate_roadmap(target_career: str, gap_skills: list) -> dict:
    """
    Generate a phased learning roadmap to close skill gaps.

    Returns dict with:
      - phases: list of {
          name, duration, description,
          milestones: [{title, resource, resource_type, estimated_hours, is_free}]
        }
      - total_estimated_hours: int
    """
    gap_names = ", ".join(
        s.get("skill", s) if isinstance(s, dict) else str(s) for s in gap_skills
    )

    prompt = f"""You are MentorX AI, a career coach for the Pakistani job market.

Target Career: {target_career}
Skills the user needs to learn: {gap_names}

Create a detailed 3-phase learning roadmap.
Include FREE and paid resources accessible from Pakistan (Coursera, YouTube, Udemy, freeCodeCamp, etc.).

Return ONLY valid JSON in this exact format:
{{
  "phases": [
    {{
      "name": "Phase 1: Foundations",
      "duration": "Month 1-2",
      "description": "Build core fundamentals...",
      "milestones": [
        {{
          "title": "Complete Python Basics",
          "resource": "freeCodeCamp Python Course (YouTube)",
          "resource_type": "Video Course",
          "estimated_hours": 20,
          "is_free": true
        }}
      ]
    }}
  ],
  "total_estimated_hours": 200
}}

Each phase should have 3-5 milestones. Include a mix of free and paid resources.
Be specific with resource names – real courses and tutorials that exist."""

    return _safe_call(prompt, {"phases": [], "total_estimated_hours": 0})


# =========================================================================
# 4. Resume Review
# =========================================================================

def review_resume(resume_text: str, target_role: str) -> dict:
    """
    Analyse a resume against a target role.

    Returns dict with:
      - overall_score: int (0-100)
      - section_feedback: list of {section, score, comments, suggestions}
      - ats_tips: list of strings
      - top_improvements: list of strings
      - strengths: list of strings
    """
    prompt = f"""You are MentorX AI, an expert resume reviewer for the Pakistani and international job market.

Target Role: {target_role}

Resume Text:
---
{resume_text}
---

Evaluate this resume thoroughly.

Return ONLY valid JSON in this exact format:
{{
  "overall_score": 72,
  "section_feedback": [
    {{
      "section": "Summary",
      "score": 65,
      "comments": "The summary is too generic...",
      "suggestions": "Add specific achievements and metrics..."
    }},
    {{
      "section": "Experience",
      "score": 70,
      "comments": "Good detail but missing impact metrics.",
      "suggestions": "Quantify achievements with numbers."
    }},
    {{
      "section": "Education",
      "score": 80,
      "comments": "Clear and relevant.",
      "suggestions": "Add relevant coursework or projects."
    }},
    {{
      "section": "Skills",
      "score": 60,
      "comments": "Missing key technical skills for the role.",
      "suggestions": "Add cloud, CI/CD, and testing tools."
    }}
  ],
  "ats_tips": [
    "Add more keywords related to {target_role}",
    "Use standard section headings"
  ],
  "top_improvements": [
    "Quantify achievements with metrics",
    "Tailor summary to target role",
    "Add relevant certifications"
  ],
  "strengths": [
    "Clean formatting",
    "Relevant work experience"
  ]
}}

Be constructive but honest. Scores should reflect real quality."""

    return _safe_call(
        prompt,
        {
            "overall_score": 0,
            "section_feedback": [],
            "ats_tips": [],
            "top_improvements": [],
            "strengths": [],
        },
    )


# =========================================================================
# 5. Mock Interview – Question Generation
# =========================================================================

def generate_interview_question(target_role: str, conversation_history: list, question_number: int) -> dict:
    """
    Generate the next interview question based on conversation so far.

    conversation_history items are dicts with keys: question, answer

    Returns dict with:
      - question: str
      - question_type: "behavioral" | "technical" | "situational"
      - context: str (why this question is being asked)
      - is_final: bool (True if this is the last question, i.e. question_number >= 6)
    """
    history_text = ""
    if conversation_history:
        lines = []
        for i, m in enumerate(conversation_history, 1):
            lines.append(f"Q{i}: {m.get('question', '')}")
            lines.append(f"A{i}: {m.get('answer', '')}")
        history_text = "Conversation so far:\n" + "\n".join(lines)

    previously_asked = [m.get("question", "") for m in conversation_history]
    previously_asked_text = "\n".join(f"- {q}" for q in previously_asked if q) or "None yet"

    prompt = f"""You are a professional interviewer conducting a mock interview for a {target_role} position in Pakistan for a student or fresh graduate.

{history_text}

Previously asked questions (NEVER repeat any of these):
{previously_asked_text}

This is question number {question_number} of the interview.
{"This is the FINAL question. After the candidate answers, you will provide overall feedback." if question_number >= 6 else ""}

Generate the NEXT interview question. Important rules:
1. The question must be DIFFERENT from all previously asked questions.
2. Adjust difficulty for a student or fresh graduate — do NOT ask senior-level questions.
3. Mix behavioral, technical, and situational questions across the interview.
4. Make the question realistic for a {target_role} role in Pakistan.

Return ONLY valid JSON:
{{
  "question": "Your new question here",
  "question_type": "behavioral",
  "context": "Why you are asking this",
  "is_final": {"true" if question_number >= 6 else "false"}
}}"""

    # Varied fallback questions so the interview never gets stuck on identical questions
    role = target_role or "this"
    fallbacks = [
        f"Why are you interested in a {role} role, and what skills do you bring?",
        f"Describe a project or task where you used skills relevant to {role} work.",
        f"How would you explain a complex {role} concept to someone without a technical background?",
        f"Tell me about a time you had to learn something new quickly for a {role}-related challenge.",
        f"What do you think is the most important quality for success as a {role}, and why?",
        f"Describe how you would approach a real-world problem commonly faced in {role} roles.",
    ]
    fallback_q = fallbacks[(question_number - 1) % len(fallbacks)]

    return _safe_call(
        prompt,
        {
            "question": fallback_q,
            "question_type": "behavioral",
            "context": "General interview question",
            "is_final": question_number >= 6,
        },
    )


# =========================================================================
# 6. Mock Interview – Answer Feedback
# =========================================================================

def evaluate_interview_answer(question: str, answer: str, target_role: str) -> dict:
    """
    Evaluate a single interview answer.

    Returns dict with:
      - score: int (0-100)
      - strengths: list of strings
      - improvements: list of strings
      - better_example: str (a better version of the answer)
    """
    prompt = f"""You are an experienced interviewer hiring for a {target_role} position in Pakistan. Evaluate this mock-interview answer as it relates specifically to that role.

Target Role: {target_role}
Question Asked: "{question}"
Candidate's Answer: "{answer}"

Provide specific, role-aware feedback. Reference the question directly. Do NOT give generic advice that could apply to any interview.

Return ONLY valid JSON:
{{
  "score": 70,
  "strengths": ["Specific strength tied to the role or question"],
  "improvements": ["Specific, actionable improvement for this role"],
  "better_example": "A concise, stronger example answer tailored to the {target_role} role."
}}"""

    return _safe_call(
        prompt,
        {
            "score": 50,
            "strengths": ["You attempted the question."],
            "improvements": ["Add a concrete example from your experience.", "Connect your answer more directly to the {target_role} role."],
            "better_example": f"For a {target_role} role, a stronger answer would include a relevant example, mention a specific skill, and explain the outcome.",
        },
    )


# =========================================================================
# 7. Mock Interview – Final Summary
# =========================================================================

def generate_interview_summary(target_role: str, conversation: list, answer_scores: list) -> dict:
    """
    Generate a final interview performance summary.

    Returns dict with:
      - overall_score: int (0-100)
      - question_breakdown: list of {question, score, feedback}
      - top_tips: list of strings
      - overall_impression: str
    """
    prompt = f"""You are MentorX AI, providing a final mock interview evaluation.

Target Role: {target_role}

Full Conversation:
{json.dumps(conversation, indent=2)}

Individual Answer Scores:
{json.dumps(answer_scores, indent=2)}

Provide a comprehensive final summary.

Return ONLY valid JSON:
{{
  "overall_score": 68,
  "question_breakdown": [
    {{"question": "Question text...", "score": 75, "feedback": "Strong answer with good examples."}}
  ],
  "top_tips": [
    "Use the STAR method for behavioral questions",
    "Quantify your achievements"
  ],
  "overall_impression": "The candidate shows good communication skills but needs to work on providing specific examples."
}}"""

    return _safe_call(
        prompt,
        {
            "overall_score": 50,
            "question_breakdown": [],
            "top_tips": ["Practice with a friend", "Record yourself answering"],
            "overall_impression": "Keep practicing!",
        },
    )
