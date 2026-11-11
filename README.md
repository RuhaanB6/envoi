# Envoi — Letters, done right

Envoi is a local CS348 Stage 2 application built with React, TypeScript, Vite,
FastAPI, psycopg 3, and PostgreSQL 17. SQL is hand-written; there is no ORM.

Select a demo user, read their sent and received letters, create a draft, edit it,
and delete it. The mailbox report shows matching letters, average word count,
and sent/received totals. Correspondent, mode, status, and creation-date filters
run in PostgreSQL. Successful writes refresh the report and selector queries.

## Run locally

Prerequisites: Docker Desktop running, Node **20.19+ or 22.12+**, npm, and Python
3.12+ with `uv` (or an equivalent virtual environment setup). The verified local
setup used Python 3.13 and Node 26. PostgreSQL is pinned to 17.6 in Compose.

From the repository root:

```bash
docker compose up -d
docker compose ps
```

First-time backend setup:

```bash
cd backend
cp .env.example .env
uv venv .venv
uv pip install --python .venv/bin/python -r requirements.txt
.venv/bin/yoyo apply --batch
.venv/bin/python seed.py
```

For an existing environment, run just the migration and seed commands. Do not
replace an existing `.env`. Yoyo must run from `backend/`; `yoyo.ini` targets the
local Compose database independently of the API's `DATABASE_URL`. For a different
database, use yoyo's `--database` option with a `postgresql+psycopg://` URL.

Start the API in a terminal:

```bash
cd backend
.venv/bin/uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Start the frontend in another terminal:

```bash
cd frontend
npm ci
npm run dev -- --host 127.0.0.1
```

Open **http://127.0.0.1:5173**. Vite proxies `/api` to FastAPI on port 8000.
API documentation is at **http://127.0.0.1:8000/docs**.

The seed script creates five users, five active pen-palships, and eighteen letters.
It is repeatable: rerunning it does not duplicate seed rows. It restores deleted
seed letters, but does not overwrite edits to existing seed letters. Demo dates
are relative to the time the seed is first loaded.

## Database and API

Exactly three application tables exist: `users`, `penpalships`, and `letters`.
Every letter has one sender and one recipient. Foreign keys, check constraints,
and triggers enforce correspondence rules. Only drafts can be edited/deleted;
all API-created letters are drafts. Word count is computed from the body in SQL,
not stored. See [database notes](docs/DATABASE.md) for columns, constraints,
relationships, SQL, transaction behavior, and index rationale.

| Route | Purpose |
|---|---|
| `GET /api/health` | Real PostgreSQL connectivity and runtime versions |
| `GET /api/users` | Database-populated demo identities |
| `GET /api/options?user_id=…` | Recipients, active pen-palships, and report options |
| `GET /api/letters?user_id=…` | User's sent and received letters |
| `POST /api/letters?user_id=…` | Create a draft |
| `PUT /api/letters/{id}?user_id=…` | Update the sender's draft |
| `DELETE /api/letters/{id}?user_id=…` | Delete the sender's draft |
| `GET /api/report?user_id=…` | Filtered aggregates and matching letter rows |

Report filters: `correspondent_id`, `mode`, `status`, `date_from`, `date_to`.
Date boundaries are inclusive UTC calendar dates applied to `created_at`.
The sender and recipient primary-key joins cannot multiply rows. Sent plus
received equals matching count; an empty result has zero counts and average.

Identity selection is **not authentication**. Anyone using this local demo can
select any identity. There is no sending, automatic delivery, invitation,
permission, or cloud-deployment workflow. In-transit/delivered rows are seed data.
Do not expose this demo to untrusted users.

## Verification

With PostgreSQL running and migrations applied:

```bash
cd backend
.venv/bin/python -m pytest -q
.venv/bin/ruff check .
```

Tests create and remove a uniquely named PostgreSQL schema per test; they do not
mock the database or truncate the demo tables. The database role must be able to
create schemas. Run the tests twice to check isolation.

With the API also running:

```bash
cd backend
.venv/bin/python verify_live.py
```

This calls the real HTTP server, checks persistence using a second PostgreSQL
connection, checks aggregate changes and filters, and verifies rejected writes.
It creates one disposable draft and removes it in `finally`. It assumes the
provided seed identities and immutable-status examples are present.

```bash
cd frontend
npm run build
npm run lint
```

A destructive migration rollback command, for a **disposable** database only:

```bash
cd backend
.venv/bin/yoyo rollback --batch --all
.venv/bin/yoyo apply --batch
.venv/bin/python seed.py
```

Rollback drops the three application tables and their data. The migration was
verified with apply → rollback → apply before seeding the demo.

See [acceptance evidence](docs/STAGE2-VERIFICATION.md) and the
[10-minute demo outline](docs/DEMO.md).

## AI Usage

**Tools used:** OpenAI Codex (ChatGPT coding assistant), its terminal and browser
tools, and the project's existing development tools. Earlier repository scaffolding
also contains Claude Code configuration; those files do not establish which tools
were used for every historical commit.

**Tasks assisted with in Stage 2:** implementation planning; schema and reversible
migrations; PostgreSQL constraints, triggers, and SQL queries; seed data; FastAPI
endpoints; React forms and reports; integration tests; debugging; documentation;
and the demo outline. Codex produced substantial implementation code, not just
suggestions. Git commits use the repository's configured human author; the
attribution does not replace this disclosure.

**Review and verification:** the assistant inspected the existing repository,
reviewed SQL parameterization, relationships, trigger behavior, and API write
conditions, ran migration apply/rollback/reapply, ran real-PostgreSQL tests,
built/linted the frontend, and exercised the running UI and API against PostgreSQL.
The acceptance record identifies what was actually verified. Live testing exposed
and corrected a commit-timing issue before completion.

**Student understanding:** the course permits AI assistance, as confirmed by the
student. The student remains responsible for reviewing the code and being able to
explain the schema, SQL, triggers, transactions, report filters, and UI refresh.
The assistant cannot attest that this student review has already occurred.
[The demo outline](docs/DEMO.md) includes explanation questions for that review.
