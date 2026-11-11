# Letters app
A place to write and receive letters: pen-pal correspondence that takes time to arrive, plus one-off direct sends.
The CS348 project is the MVP milestone; the SQL is what gets graded, so it stays hand-written and visible.

## Commands
Fresh clone, once: `git config core.hooksPath .githooks`
- Postgres up (repo root): `docker compose up -d`
- Migrate / roll back: `cd backend && .venv/bin/yoyo apply --batch` | `.venv/bin/yoyo rollback --batch --all`
- Backend dev: `cd backend && .venv/bin/uvicorn app.main:app --reload --port 8000`
- Frontend dev: `cd frontend && npm run dev`
- Tests: `cd backend && .venv/bin/python -m pytest -q`
- Lint: `cd backend && .venv/bin/ruff check .`
- Typecheck / build: `cd frontend && npx tsc -b --noEmit` | `npm run build`

`yoyo` only works from `backend/` (relative `sources` in `yoyo.ini`). Deps are `requirements.txt` in an
activated `.venv` — no `uv run`, no lockfile. Frontend lints with oxlint; there is no Prettier.

## Layout
- `backend/` — FastAPI app, psycopg3 pool, yoyo `migrations/`, pytest `tests/`
- `frontend/` — Vite + React + TS + Tailwind
- `docs/` — product context, decisions, task specs, handoff
- `.claude/` — coding conventions and reference docs (plain Markdown, readable by any tool)

## Non-negotiables
- Raw parameterized SQL through psycopg3 (`%s` placeholders). No ORM, never an f-string or concatenation in a query.
- Migrations are forward + rollback pairs, immutable once committed. Schema changes mean a new migration.
- Tests run against a real Postgres. Never mock the database.
- Stage 2 uses only users, penpalships, and letters. Demo-user selection replaces auth.
- SQL triggers enforce pair membership and draft-only edit/delete. All API creates are drafts.
- Do not add auth, sending/delivery jobs, invites, tags, or memory permissions for Stage 2.
- The frontend holds no business logic.

## Read before editing
- `backend/migrations/**` or `backend/app/db/**` → `.claude/rules/sql.md`
- `backend/app/**/*.py` → `.claude/rules/api.md`
- `frontend/src/**` → `.claude/rules/frontend.md`
- `backend/tests/**` → `.claude/rules/tests.md`
- letters, penpalships or delivery logic → `.claude/skills/data-model/SKILL.md`
- grading criteria → `.claude/skills/cs348-rubric/SKILL.md`

## Process
- Write a spec to `docs/tasks/NNN-<name>.md` before work touching more than one file.
- Run the tests and the typecheck before declaring anything done.
- Append decisions to `docs/DECISIONS.md`; update `docs/HANDOFF.md` at session end.

## Commits
Commit after every coherent change, not at the end of a task. Subject line ≤ 50 characters, imperative, plain
English, no scope prefixes or conventional-commit tags. Body only when the subject can't carry it, ≤ 3 lines.
If a message would need "and", make two commits. No AI attribution of any kind: no Co-Authored-By, no
"Generated with", no session links.
