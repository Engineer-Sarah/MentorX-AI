---
kind: configuration_system
name: Streamlit + dotenv-based Configuration for MentorX AI
category: configuration_system
scope:
    - '**'
source_files:
    - mentorx-ai/.env.example
    - mentorx-ai/.streamlit/config.toml
    - mentorx-ai/src/gemini_service.py
    - mentorx-ai/src/utils.py
    - mentorx-ai/app.py
    - mentorx-ai/data/career_database.json
    - mentorx-ai/data/assessment_questions.json
---

## What system/approach is used

The application uses a minimal, file-based configuration approach with two layers:

1. **Runtime secrets** are loaded via `python-dotenv` from a `.env` file at the project root. The only secret is `GOOGLE_API_KEY`, which authenticates calls to Google Gemini.
2. **Application and UI settings** are declared in Streamlit's native config file `.streamlit/config.toml`, which controls theme colors, server mode, and browser telemetry.
3. **Static data/configuration** (career profiles, assessment questions) lives as JSON files under `data/` and is read directly by Python code — there is no schema validation layer around them.

There is no centralized configuration module; each subsystem reads its own inputs where needed.

## Key files and packages

- `mentorx-ai/.env.example` — template documenting the required `GOOGLE_API_KEY` environment variable.
- `mentorx-ai/.env` — actual secrets file (gitignored by convention; not committed).
- `mentorx-ai/.streamlit/config.toml` — Streamlit runtime configuration: theme palette (`primaryColor`, `backgroundColor`, etc.), `server.headless = true`, and `browser.gatherUsageStats = false`.
- `mentorx-ai/src/gemini_service.py` — the only place that loads `.env` via `load_dotenv()` and reads `GOOGLE_API_KEY` through `os.getenv("GOOGLE_API_KEY", "")`. This is the single point of secret ingestion.
- `mentorx-ai/data/career_database.json`, `data/assessment_questions.json` — static configuration data consumed by `src/utils.py` (`load_career_database`) and the assessment pages.
- `mentorx-ai/app.py` — sets page-level config via `st.set_page_config(...)` (title, icon, layout, sidebar state), which overrides or supplements `config.toml` per-page.

## Architecture and conventions

- **Secrets are isolated**: Only `gemini_service.py` imports `dotenv` and accesses `GOOGLE_API_KEY`. Other modules never touch `.env` or `os.environ` directly, keeping credential exposure localized.
- **Environment variables are optional with defaults**: `os.getenv("GOOGLE_API_KEY", "")` returns an empty string if the key is missing, so the app can start without a configured API key (calls to Gemini will fail later, but startup succeeds).
- **Streamlit config is declarative**: All visual/theme/server behavior is expressed in `config.toml`; page-specific overrides live inline in `app.py` via `st.set_page_config`. There is no programmatic merging logic — Streamlit resolves precedence itself.
- **Static data is plain JSON**: No ORM, no config parser, no schema enforcement. `utils.load_career_database()` opens `data/career_database.json` and expects a top-level `careers` list. Consumers assume this shape.
- **No feature flags or environment toggles**: The repo has no mechanism to enable/disable features based on env vars or config keys. Behavior differences come from page routing (`pages/1_*.py` … `7_Career_Dashboard.py`) rather than configuration.
- **Session state replaces persistent config**: User identity and progress are held in `st.session_state` and persisted to the local SQLite database (`mentorx.db`) via `src/database.py` — not treated as application configuration.

## Conventions and constraints

- **One secret, one env var**: The only supported environment variable is `GOOGLE_API_KEY`. New secrets should follow the same pattern: add a `.env.example` entry, load via `load_dotenv()` in the service that needs it, and read with `os.getenv(key, default)`.
- **`.env` is never committed**: The presence of `.env.example` alongside `.env` signals the standard copy-and-fill convention.
- **Streamlit config lives under `.streamlit/`**: Theme and server options must be placed in `.streamlit/config.toml` rather than passed programmatically, except for per-page overrides done through `st.set_page_config`.
- **Data files are immutable at runtime**: `data/*.json` are treated as read-only configuration; there is no write path in the codebase that modifies them.
- **Database initialization is side-effect driven**: `init_db()` runs once on first run (guarded by `"db_initialized" not in st.session_state`); this is a bootstrap configuration step, not user-configurable.
- **No validation or schema enforcement**: Neither the JSON data files nor the `.env` contents are validated at load time. Missing fields or malformed values surface as runtime errors in downstream logic.