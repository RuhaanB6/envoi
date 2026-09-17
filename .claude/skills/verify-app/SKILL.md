---
name: verify-app
description: Full end-to-end check: docker, migrations, health, tests, lint, typecheck, build.
disable-model-invocation: true
---

# /verify-app

Run every step from the repo root. Keep going after a failure so the table is
complete; capture each step's output.

1. **Docker** — `docker compose up -d`. Then poll `docker compose ps` until the
   postgres service reports `healthy`, checking every 3s. If 60s pass without
   it, stop the whole run and report: "Postgres never became healthy — is Docker
   Desktop running?" Do not continue to the later steps.
2. **Migrations** — `cd backend && .venv/bin/yoyo apply --batch`
3. **Health** — start `.venv/bin/uvicorn app.main:app --port 8000` in the
   background from `backend/`, wait for it to answer, then
   `curl -fsS http://localhost:8000/api/health`. Kill the server afterwards,
   including on failure.
4. **Tests** — `cd backend && .venv/bin/python -m pytest -q`
5. **Lint** — `cd backend && .venv/bin/ruff check .`
6. **Typecheck** — `cd frontend && npx tsc -b --noEmit`
7. **Build** — `cd frontend && npm run build`

Output: a single table of step / pass or fail. Below it, the raw output of the
failing steps only — nothing for the ones that passed. End with one line saying
whether the app is verified.
