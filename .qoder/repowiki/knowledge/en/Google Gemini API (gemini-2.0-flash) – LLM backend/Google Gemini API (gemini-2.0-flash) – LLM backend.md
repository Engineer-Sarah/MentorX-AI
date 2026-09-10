---
kind: external_dependency
name: Google Gemini API (gemini-2.0-flash) – LLM backend
slug: google-gemini-api
category: external_dependency
category_hints:
    - vendor_identity
    - auth_protocol
scope:
    - '**'
---

All generative-AI functionality in MentorX AI is routed through Google's Gemini API via the `google-generativeai` SDK (`genai.GenerativeModel`). The model name is pinned to `gemini-2.0-flash` and the API key is read from the `GOOGLE_API_KEY` environment variable loaded by `python-dotenv`. Every LLM call goes through `src/gemini_service.py`, which wraps calls in `_safe_call` that parse JSON out of markdown-fenced responses; if no key is configured, a `RuntimeError` is raised before any network call.

Integration points:
- `.env.example` documents where to obtain the key (`https://aistudio.google.com/app/apikey`).
- `src/gemini_service.py` centralises 7 prompt-driven functions: career recommendation, skill-gap analysis, learning roadmap generation, resume review, interview question generation, answer evaluation, and final interview summary.
- All prompts are role-prompted to act as "MentorX AI, a career coach specialising in the Pakistani job market" and return structured JSON consumed by Streamlit pages under `pages/`.

Operational notes: the service is stateless per-call; conversation history for the mock interview is passed in-band via the `conversation_history` parameter rather than using Gemini's built-in chat sessions.