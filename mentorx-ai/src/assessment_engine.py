"""
assessment_engine.py – Scoring logic for the career assessment quiz.
Computes dimension scores and derives personality traits from answers.
"""

import json
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / "data"

# ---------------------------------------------------------------------------
# Dimension metadata
# ---------------------------------------------------------------------------

# The five primary interest dimensions used for Gemini prompts, career
# recommendations, and the dashboard radar chart.
PRIMARY_INTEREST_DIMENSIONS = [
    "technical", "creative", "social", "analytical", "entrepreneurial",
]

DIMENSION_LABELS = {
    # Primary interest dimensions
    "technical":           "Technical & Technology Interest",
    "creative":            "Creative & Design Interest",
    "social":              "Social & Helping Orientation",
    "analytical":          "Analytical & Research Interest",
    "entrepreneurial":     "Entrepreneurial & Business Drive",
    # Work-style dimensions
    "teamwork":            "Teamwork Preference",
    "flexibility":         "Flexibility & Adaptability",
    "remote":              "Remote Work Preference",
    "communication":       "Communication Strength",
    "leadership":          "Leadership Potential",
    # Skill dimensions
    "analytical_thinking": "Analytical Thinking",
    "communication_skill": "Communication Skill",
    "problem_solving":     "Problem-Solving Strength",
    "creativity":          "Creative Thinking Ability",
    "technical_ability":   "Technical Skill Confidence",
    # Value dimensions
    "salary":              "Financial Motivation",
    "work_life":           "Work-Life Balance Priority",
    "impact":              "Social Impact Drive",
    "growth":              "Growth & Learning Priority",
    "stability":           "Stability Preference",
}

# Higher-level groupings used for Gemini prompts
CATEGORY_MAP = {
    "interests":  ["technical", "creative", "social", "analytical", "entrepreneurial"],
    "work_style": ["teamwork", "flexibility", "communication", "leadership"],
    "skills":     ["technical_skill", "problem_solving", "communication", "leadership", "creativity_skill"],
    "values":     ["salary", "work_life", "impact", "growth", "stability"],
}


def load_questions() -> list:
    """Load assessment questions from the JSON data file."""
    path = DATA_DIR / "assessment_questions.json"
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data["questions"]


def compute_scores(answers: dict) -> dict:
    """
    Compute average score per dimension from raw answers.

    Parameters
    ----------
    answers : dict
        Mapping of question_id (str) -> score (int 1-5).

    Returns
    -------
    dict
        Mapping of dimension -> average score (float, rounded to 1 decimal).
    """
    questions = load_questions()

    # Build dimension -> [scores] mapping
    dim_scores: dict[str, list[int]] = {}
    for q in questions:
        qid = str(q["id"])
        if qid in answers:
            dim = q["dimension"]
            dim_scores.setdefault(dim, []).append(answers[qid])

    # Average each dimension
    result = {}
    for dim, scores in dim_scores.items():
        result[dim] = round(sum(scores) / len(scores), 1) if scores else 0.0

    return result


def derive_traits(interest_scores: dict) -> dict:
    """
    Derive human-readable personality/career traits from dimension scores.

    Returns a dict of trait_name -> description string.
    """
    traits = {}

    # Interest-based traits
    if interest_scores.get("technical", 0) >= 3.5:
        traits["Tech-Oriented"] = "Strong interest in technology and building digital solutions."
    if interest_scores.get("creative", 0) >= 3.5:
        traits["Creative Thinker"] = "Drawn to design, content, and visual problem-solving."
    if interest_scores.get("social", 0) >= 3.5:
        traits["People-Focused"] = "Motivated by helping others and working with communities."
    if interest_scores.get("analytical", 0) >= 3.5:
        traits["Analytical Mind"] = "Enjoys research, data analysis, and systematic thinking."
    if interest_scores.get("entrepreneurial", 0) >= 3.5:
        traits["Entrepreneurial Spirit"] = "Driven by business building, risk-taking, and innovation."

    # Work-style traits
    if interest_scores.get("teamwork", 0) >= 4.0:
        traits["Team Player"] = "Thrives in collaborative environments."
    elif interest_scores.get("teamwork", 0) <= 2.0:
        traits["Independent Worker"] = "Prefers focused solo work over group settings."
    if interest_scores.get("flexibility", 0) >= 4.0:
        traits["Adaptable"] = "Comfortable with change and dynamic environments."
    if interest_scores.get("leadership", 0) >= 4.0:
        traits["Natural Leader"] = "Comfortable taking charge and guiding teams."

    # Skill traits
    if interest_scores.get("problem_solving", 0) >= 4.0:
        traits["Strong Problem Solver"] = "Excels at breaking down complex challenges."
    if interest_scores.get("communication", 0) >= 4.0:
        traits["Effective Communicator"] = "Strong written and verbal communication skills."

    # Value traits
    if interest_scores.get("growth", 0) >= 4.0:
        traits["Growth-Driven"] = "Prioritises learning and career development."
    if interest_scores.get("impact", 0) >= 4.0:
        traits["Impact-Oriented"] = "Wants work to make a meaningful difference."

    # Fallback
    if not traits:
        traits["Versatile"] = "Balanced profile with diverse interests and skills."

    return traits


def get_full_assessment_result(answers: dict) -> tuple[dict, dict]:
    """
    Convenience wrapper: compute scores and derive traits in one call.

    Returns
    -------
    tuple of (interest_scores dict, personality_traits dict)
    """
    scores = compute_scores(answers)
    traits = derive_traits(scores)
    return scores, traits
