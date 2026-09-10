---
kind: dependency_management
name: Python Dependencies via Flat requirements.txt with Pinned Minimum Versions
category: dependency_management
scope:
    - '**'
source_files:
    - mentorx-ai/requirements.txt
    - mentorx-ai/.env
    - mentorx-ai/.env.example
    - mentorx-ai/app.py
    - mentorx-ai/src/gemini_service.py
---

## What system/approach is used

This repository uses the standard Python dependency management approach: a single flat `requirements.txt` file at the project root (`mentorx-ai/requirements.txt`) declares all third-party packages. There is no virtual environment committed, no `pyproject.toml`, no `setup.py`, no `Pipfile`, no lockfile (e.g. `requirements.lock`, `poetry.lock`, `pipenv.lock`), and no vendored dependencies under a `vendor/` directory.

The declared dependencies are minimal and application-focused:
- `streamlit>=1.30.0` — UI framework
- `google-generativeai>=0.3.0` — Google Gemini API client
- `pandas>=2.0.0` — data manipulation
- `plotly>=5.18.0` — visualization
- `python-dotenv>=1.0.0` — `.env` loading for secrets (used alongside `.env` and `.env.example`)

## Key files and packages

- `mentorx-ai/requirements.txt` — the sole manifest of external dependencies; every import in `app.py`, `src/*.py`, and `pages/*.py` ultimately resolves to one of these packages.
- `mentorx-ai/.env` and `mentorx-ai/.env.example` — runtime configuration loaded via `python-dotenv`; not a dependency but part of the external-config surface.
- `mentorx-ai/src/gemini_service.py` — consumes `google-generativeai`.
- `mentorx-ai/pages/*.py` and `app.py` — consume `streamlit`, `pandas`, `plotly`.

## Architecture and conventions

- **Flat manifest**: All dependencies are listed in one file with no subdirectory or per-package manifests. This keeps setup trivial (`pip install -r requirements.txt`) but provides no transitive-dependency pinning.
- **Minimum-version pins only**: Every entry uses `>=X.Y.Z` rather than exact pins (`==X.Y.Z`). This allows newer compatible versions to be installed automatically, which can improve security patching but risks subtle incompatibilities across environments.
- **No lockfile / no reproducible build**: Because there is no lockfile, two installations on different machines may resolve to different minor/patch versions of transitive dependencies. The repo does not enforce deterministic builds.
- **No private registry / no vendoring**: No custom index URLs, no `--extra-index-url`, no `PIP_PRIVATE_INDEX_URL`, and no vendored copies of libraries. All packages are expected to be pulled from PyPI.
- **Runtime config via dotenv**: Secrets (e.g. Gemini API key) are loaded from `.env` using `python-dotenv`, keeping credentials out of source control while still being required locally.

## Conventions and constraints

Observed conventions (descriptive):
- New third-party packages should be added as a single line in `requirements.txt` using the `package>=version` form.
- Secrets are never hard-coded; they are read from `.env` via `python-dotenv`.
- The project has no CI step that validates `requirements.txt` against a lockfile because none exists.

Enforced rules (from code/structure):
- The app will fail to start if any package listed in `requirements.txt` is missing from the active Python environment, since imports occur at module load time in `app.py` and page modules.
- The minimum version constraints in `requirements.txt` are enforced by pip during installation; installing an older incompatible version will be rejected.

Gaps / opportunities:
- Adding a lockfile (e.g. `pip-tools` `requirements.txt` + `requirements-dev.txt`, `pip freeze > requirements.lock`, or migrating to `poetry`/`uv`) would make installs reproducible.
- Splitting into `requirements.txt` (runtime) and `requirements-dev.txt` (testing/linting) would separate concerns.