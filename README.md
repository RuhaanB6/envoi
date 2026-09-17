# CS348 Project -- a letters app

**Status:** the domain is decided. This is a letters app: pen-pal
correspondence between users, where a letter takes time to arrive based on the
distance between them, plus one-off direct sends via a share link. Stage 1
proved the stack end to end (React → FastAPI → psycopg → Postgres); the real
schema and features are Stage 2.

The product, domain, schema and plan live in
[`docs/project-context.md`](docs/project-context.md) -- that document is the
source of truth, not this README.

## Stack

| Layer        | Choice                                              |
|--------------|------------------------------------------------------|
| Frontend     | React + TypeScript + Vite, TanStack Query, React Router, React Hook Form + Zod, Tailwind |
| Backend      | FastAPI + uvicorn                                    |
| DB access    | psycopg 3 (`ConnectionPool`), raw parameterized SQL -- **no ORM** |
| Migrations   | yoyo-migrations (plain `.sql` files)                  |
| Database     | PostgreSQL 17 (Docker Compose locally, Neon later)    |
| Python env   | uv                                                    |

Every query goes through psycopg's `%s` placeholders -- never f-strings or
string concatenation. Multi-table writes use `with conn.transaction():`.

## Prerequisites

- Docker Desktop (or another Docker Engine) running
- [uv](https://docs.astral.sh/uv/) installed (`curl -LsSf https://astral.sh/uv/install.sh | sh`)
- Node.js 20+ and npm

## 1. Start Postgres

From the project root:

```bash
docker compose up -d
docker compose ps   # wait until postgres shows "healthy"
```

This starts Postgres 17 on `localhost:5432` with:
- user: `cs348`
- password: `cs348`
- database: `cs348`

(data persists in the named volume `pgdata` between restarts; `docker compose down -v` wipes it)

## 2. Backend: venv, deps, migrations

```bash
cd backend
cp .env.example .env          # defaults already match docker-compose
uv venv .venv
source .venv/bin/activate     # Windows: .venv\Scripts\activate
uv pip install -r requirements.txt
yoyo apply --batch
```

`yoyo apply` runs every pair in `migrations/` in order. The Stage 1
placeholder has been rolled back and deleted; the real `001` is `users` and
`sessions`. (To undo everything: `yoyo rollback --batch --all`.) `yoyo` only
works from `backend/` -- its `sources` path is relative.

## 3. Run the backend

```bash
# still inside backend/, with .venv activated
uvicorn app.main:app --reload --port 8000
```

In another terminal, confirm it's alive:

```bash
curl -s http://localhost:8000/api/health
```

You should get back JSON with `status: "ok"`, a real Postgres version
string, the Python version, and the FastAPI version.

## 4. Run the frontend

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:5173 -- the page calls `/api/health` (proxied by
Vite to `http://localhost:8000`) and renders the same JSON you curled
above.

## 5. Run the tests

```bash
# inside backend/, with .venv activated, Postgres running and migrated
python -m pytest
```

## 6. Lint

```bash
# inside backend/, with .venv activated
ruff check .
```

## Everyday commands (once everything above is set up once)

```bash
# terminal 1
docker compose up -d

# terminal 2
cd backend && source .venv/bin/activate && uvicorn app.main:app --reload --port 8000

# terminal 3
cd frontend && npm run dev
```

## Project layout

```
cs348-project/
├── backend/
│   ├── app/
│   │   ├── main.py           # FastAPI app, CORS, lifespan opens/closes the pool
│   │   ├── config.py         # pydantic-settings: DATABASE_URL, CORS_ORIGINS
│   │   ├── db.py             # psycopg ConnectionPool + get_conn dependency
│   │   └── routers/health.py # GET /api/health
│   ├── migrations/           # yoyo NNN_<name>.sql + NNN_<name>.rollback.sql pairs
│   ├── tests/test_health.py
│   ├── yoyo.ini
│   ├── requirements.txt
│   ├── Dockerfile
│   └── .env.example
├── frontend/                 # Vite + React + TS + Tailwind
├── docs/                     # project-context.md, DECISIONS.md, tasks/
├── docker-compose.yml        # Postgres 17, named volume, port 5432
├── AGENTS.md                 # conventions for AI coding agents
└── README.md
```

## Next steps

The ordered plan is in [`docs/project-context.md`](docs/project-context.md)
("Stage 2 plan"). In short:

- Migration 001: `users` and `sessions`, plus register / login / logout / `me`.
- Migration 002: `penpalships`, `letters`, `letter_recipients`, `tags`.
- Requirement 1: compose, edit, delete and send a letter, with the
  `send_letter` stored procedure and the delivery sweep.
- Requirement 2: the mailbox summary report, filters populated from the
  database.
- Deploy to Neon + Render + Vercel, then the letter-in-transit animations.
