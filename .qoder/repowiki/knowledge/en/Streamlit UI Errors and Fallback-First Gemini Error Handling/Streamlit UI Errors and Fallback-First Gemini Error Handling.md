---
kind: error_handling
name: Streamlit UI Errors and Fallback-First Gemini Error Handling
category: error_handling
scope:
    - '**'
source_files:
    - mentorx-ai/src/gemini_service.py
    - mentorx-ai/pages/1_Career_Assessment.py
    - mentorx-ai/pages/2_Career_Recommendation.py
    - mentorx-ai/pages/3_Skill_Gap_Analysis.py
    - mentorx-ai/pages/4_Learning_Roadmap.py
    - mentorx-ai/pages/5_Resume_Analyzer.py
    - mentorx-ai/src/database.py
    - mentorx-ai/app.py
---

## Overview

This Streamlit-based career coaching app uses a **two-tier error handling strategy**: user-facing validation errors are surfaced through Streamlit's `st.error()` / `st.success()` UI widgets, while external service failures (Google Gemini API) are handled with a **fallback-first** pattern that returns safe default data instead of raising. There is no centralized exception hierarchy, logging framework, or middleware — errors are handled inline at the point of failure.

## 1. User Input Validation (UI-level)

Validation errors in page scripts (`pages/*.py`) are displayed directly to users via Streamlit's notification helpers:

- `st.error(...)` for invalid input (e.g., unanswered questions, missing resume text, missing target role, missing skill selection).
- `st.success(...)` for confirmation messages after successful operations.
- `st.rerun()` is used to refresh the page after state changes.

Examples observed:
- `pages/1_Career_Assessment.py`: checks if all questions are answered before submission and shows `st.error(f"Please answer all {total_questions} questions before submitting. ({answered}/{total_questions} done)")`.
- `pages/5_Resume_Analyzer.py`: validates resume text and target role presence.
- `pages/3_Skill_Gap_Analysis.py`, `4_Learning_Roadmap.py`, `2_Career_Recommendation.py`: validate prerequisites before calling Gemini.

There is no shared validation module; each page handles its own field checks inline.

## 2. External Service Error Handling (Gemini API)

All Google Gemini calls go through `src/gemini_service.py`, which centralizes error behavior via two helpers:

- `_call_gemini(prompt)`: raises `RuntimeError("Google Gemini API key not configured. Please set GOOGLE_API_KEY in your .env file.")` when the model is uninitialized (i.e., `GOOGLE_API_KEY` is missing). This is the only place a Python exception is raised to callers.
- `_safe_call(prompt, fallback=None)`: wraps every LLM call in `try/except Exception as e`, prints `[GeminiService Error] {e}` to stdout, and returns the provided fallback value instead of propagating the error.

Each public function (`get_career_recommendations`, `analyze_skill_gap`, `generate_roadmap`, `review_resume`, `generate_interview_question`, `evaluate_interview_answer`, `generate_interview_summary`) supplies a **domain-specific default dict** as the fallback so callers always receive a well-formed response even when the API fails. For example:
- Recommendations → `{"recommendations": []}`
- Skill gap → `{"matched_skills": [], "gap_skills": [], "overall_match_percentage": 0}`
- Roadmap → `{"phases": [], "total_estimated_hours": 0}`
- Resume review → `{"overall_score": 0, ... empty lists ...}`
- Interview question → `{"question": "What interests you most...", "is_final": ...}`
- Answer evaluation → `{"score": 50, "strengths": [], "improvements": ["Practice more"], "better_example": ""}`
- Final summary → `{"overall_score": 50, "top_tips": [...], "overall_impression": "Keep practicing!"}`

## 3. Database Layer

The SQLite layer in `src/database.py` performs raw `sqlite3` calls with **no try/except blocks**. Connections are opened per function, committed, and closed within each function. Errors from SQLite (e.g., connection failures, constraint violations) will propagate uncaught to the caller. There is no retry logic, transaction wrapping, or structured error types.

## 4. What Is NOT Present

- No custom exception classes or sentinel errors.
- No structured logging library (only a single `print(f"[GeminiService Error] {e}")`).
- No global exception handler or Streamlit error middleware.
- No `try/except` around database operations.
- No HTTP error codes or error response objects — this is a client-side Streamlit app, not an API server.
- No `panic`/`recover` equivalent (Python does not have these concepts).

## Key Files

- `src/gemini_service.py` — Centralized Gemini error handling via `_safe_call` and `_call_gemini`; defines fallback defaults for every LLM endpoint.
- `pages/*.py` — Inline user-input validation using `st.error()` / `st.success()`.
- `src/database.py` — SQLite layer with no error handling (fail-fast propagation).
- `app.py` — App bootstrap; no global error handling.
- `src/utils.py` — Pure utility functions; no error handling needed.