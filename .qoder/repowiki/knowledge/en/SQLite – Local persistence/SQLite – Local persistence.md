---
kind: external_dependency
name: SQLite – Local persistence
slug: sqlite
category: external_dependency
category_hints:
    - client_constraint
scope:
    - '**'
---

Local relational storage is provided by SQLite via `src/database.py`, backed by the `mentorx.db` file checked into the repository. It defines 7 tables and exposes full CRUD operations used by the Streamlit pages to persist assessment results, career selections, roadmap milestones, and interview transcripts. Being file-backed, there is no separate database server process; concurrency is limited to single-writer semantics typical of SQLite.