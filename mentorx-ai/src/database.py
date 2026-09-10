"""
database.py – SQLite database layer for MentorX AI.
Handles all table creation, CRUD operations, and session management.
"""

import sqlite3
import json
import uuid
from datetime import datetime
from pathlib import Path

# Resolve the database file relative to the project root so it works
# regardless of the working directory the app is launched from.
_DB_DIR = Path(__file__).resolve().parent.parent
DB_PATH = str(_DB_DIR / "mentorx.db")


def get_connection():
    """Return a new SQLite connection with row factory enabled."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Create all tables if they do not exist."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sessions (
            session_id TEXT PRIMARY KEY,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            user_name TEXT,
            current_step TEXT DEFAULT 'landing'
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS assessments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            answers TEXT,
            interest_scores TEXT,
            personality_traits TEXT,
            completed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (session_id) REFERENCES sessions(session_id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS recommendations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            recommended_careers TEXT,
            raw_response TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (session_id) REFERENCES sessions(session_id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS skill_analyses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            target_career TEXT,
            current_skills TEXT,
            required_skills TEXT,
            gap_analysis TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (session_id) REFERENCES sessions(session_id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS roadmaps (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            target_career TEXT,
            roadmap_data TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (session_id) REFERENCES sessions(session_id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS resumes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            resume_text TEXT,
            feedback TEXT,
            target_role TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (session_id) REFERENCES sessions(session_id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS interviews (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            target_role TEXT,
            conversation TEXT,
            feedback TEXT,
            completed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (session_id) REFERENCES sessions(session_id)
        )
    """)

    conn.commit()
    conn.close()


# ---------------------------------------------------------------------------
# Session helpers
# ---------------------------------------------------------------------------

def create_session(user_name=""):
    """Create a new user session and return the session_id."""
    session_id = str(uuid.uuid4())
    conn = get_connection()
    conn.execute(
        "INSERT INTO sessions (session_id, user_name) VALUES (?, ?)",
        (session_id, user_name),
    )
    conn.commit()
    conn.close()
    return session_id


def get_session(session_id):
    """Fetch a session row by ID."""
    conn = get_connection()
    row = conn.execute(
        "SELECT * FROM sessions WHERE session_id = ?", (session_id,)
    ).fetchone()
    conn.close()
    return dict(row) if row else None


def update_session_step(session_id, step):
    """Update the current_step tracker for a session."""
    conn = get_connection()
    conn.execute(
        "UPDATE sessions SET current_step = ? WHERE session_id = ?",
        (step, session_id),
    )
    conn.commit()
    conn.close()


# ---------------------------------------------------------------------------
# Assessment
# ---------------------------------------------------------------------------

def save_assessment(session_id, answers, interest_scores, personality_traits):
    """Persist career-assessment results."""
    conn = get_connection()
    conn.execute(
        """INSERT INTO assessments
           (session_id, answers, interest_scores, personality_traits)
           VALUES (?, ?, ?, ?)""",
        (
            session_id,
            json.dumps(answers),
            json.dumps(interest_scores),
            json.dumps(personality_traits),
        ),
    )
    conn.commit()
    conn.close()


def get_assessment(session_id):
    """Return the most recent assessment for a session."""
    conn = get_connection()
    row = conn.execute(
        "SELECT * FROM assessments WHERE session_id = ? ORDER BY id DESC LIMIT 1",
        (session_id,),
    ).fetchone()
    conn.close()
    if row:
        d = dict(row)
        for key in ("answers", "interest_scores", "personality_traits"):
            d[key] = json.loads(d[key]) if d[key] else {}
        return d
    return None


# ---------------------------------------------------------------------------
# Recommendations
# ---------------------------------------------------------------------------

def save_recommendation(session_id, recommended_careers, raw_response=""):
    conn = get_connection()
    conn.execute(
        """INSERT INTO recommendations
           (session_id, recommended_careers, raw_response)
           VALUES (?, ?, ?)""",
        (session_id, json.dumps(recommended_careers), raw_response),
    )
    conn.commit()
    conn.close()


def get_recommendation(session_id):
    conn = get_connection()
    row = conn.execute(
        "SELECT * FROM recommendations WHERE session_id = ? ORDER BY id DESC LIMIT 1",
        (session_id,),
    ).fetchone()
    conn.close()
    if row:
        d = dict(row)
        d["recommended_careers"] = json.loads(d["recommended_careers"]) if d["recommended_careers"] else []
        return d
    return None


# ---------------------------------------------------------------------------
# Skill Analysis
# ---------------------------------------------------------------------------

def save_skill_analysis(session_id, target_career, current_skills, required_skills, gap_analysis):
    conn = get_connection()
    conn.execute(
        """INSERT INTO skill_analyses
           (session_id, target_career, current_skills, required_skills, gap_analysis)
           VALUES (?, ?, ?, ?, ?)""",
        (
            session_id,
            target_career,
            json.dumps(current_skills),
            json.dumps(required_skills),
            json.dumps(gap_analysis),
        ),
    )
    conn.commit()
    conn.close()


def get_skill_analysis(session_id):
    conn = get_connection()
    row = conn.execute(
        "SELECT * FROM skill_analyses WHERE session_id = ? ORDER BY id DESC LIMIT 1",
        (session_id,),
    ).fetchone()
    conn.close()
    if row:
        d = dict(row)
        for key in ("current_skills", "required_skills", "gap_analysis"):
            d[key] = json.loads(d[key]) if d[key] else {}
        return d
    return None


# ---------------------------------------------------------------------------
# Roadmap
# ---------------------------------------------------------------------------

def save_roadmap(session_id, target_career, roadmap_data):
    conn = get_connection()
    conn.execute(
        """INSERT INTO roadmaps (session_id, target_career, roadmap_data)
           VALUES (?, ?, ?)""",
        (session_id, target_career, json.dumps(roadmap_data)),
    )
    conn.commit()
    conn.close()


def get_roadmap(session_id):
    conn = get_connection()
    row = conn.execute(
        "SELECT * FROM roadmaps WHERE session_id = ? ORDER BY id DESC LIMIT 1",
        (session_id,),
    ).fetchone()
    conn.close()
    if row:
        d = dict(row)
        d["roadmap_data"] = json.loads(d["roadmap_data"]) if d["roadmap_data"] else {}
        return d
    return None


# ---------------------------------------------------------------------------
# Resume
# ---------------------------------------------------------------------------

def save_resume(session_id, resume_text, feedback, target_role):
    conn = get_connection()
    conn.execute(
        """INSERT INTO resumes (session_id, resume_text, feedback, target_role)
           VALUES (?, ?, ?, ?)""",
        (session_id, resume_text, json.dumps(feedback), target_role),
    )
    conn.commit()
    conn.close()


def get_resume(session_id):
    conn = get_connection()
    row = conn.execute(
        "SELECT * FROM resumes WHERE session_id = ? ORDER BY id DESC LIMIT 1",
        (session_id,),
    ).fetchone()
    conn.close()
    if row:
        d = dict(row)
        d["feedback"] = json.loads(d["feedback"]) if d["feedback"] else {}
        return d
    return None


# ---------------------------------------------------------------------------
# Interview
# ---------------------------------------------------------------------------

def save_interview(session_id, target_role, conversation, feedback):
    conn = get_connection()
    conn.execute(
        """INSERT INTO interviews
           (session_id, target_role, conversation, feedback)
           VALUES (?, ?, ?, ?)""",
        (
            session_id,
            target_role,
            json.dumps(conversation),
            json.dumps(feedback),
        ),
    )
    conn.commit()
    conn.close()


def get_interview(session_id):
    conn = get_connection()
    row = conn.execute(
        "SELECT * FROM interviews WHERE session_id = ? ORDER BY id DESC LIMIT 1",
        (session_id,),
    ).fetchone()
    conn.close()
    if row:
        d = dict(row)
        d["conversation"] = json.loads(d["conversation"]) if d["conversation"] else []
        d["feedback"] = json.loads(d["feedback"]) if d["feedback"] else {}
        return d
    return None


# ---------------------------------------------------------------------------
# Dashboard aggregation
# ---------------------------------------------------------------------------

def get_dashboard_data(session_id):
    """Pull together all data for the readiness dashboard."""
    return {
        "session": get_session(session_id),
        "assessment": get_assessment(session_id),
        "recommendation": get_recommendation(session_id),
        "skill_analysis": get_skill_analysis(session_id),
        "roadmap": get_roadmap(session_id),
        "resume": get_resume(session_id),
        "interview": get_interview(session_id),
    }
