# CS348 Project -- Stage 1

**Status:** Stage 1 scaffold only. Proves the stack is installed and wired
together end to end (React → FastAPI → psycopg → Postgres). No application
features yet -- the domain is still undecided.

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

`yoyo apply` runs `migrations/001_initial.sql`, which creates a trivial
`stack_check` table and inserts one row -- just enough to prove migrations
reach a real database. (To undo it: `yoyo rollback --batch --all`.)

## 3. Run the backend

```bash
# still inside backend/, with .venv activated
uvicorn app.main:app --reload --port 8000
```

In another terminal, confirm it's alive:

```bash
curl http://localhost:8000/api/health
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
│   ├── migrations/
│   │   ├── 001_initial.sql            # forward SQL
│   │   └── 001_initial.rollback.sql   # matching rollback SQL
│   ├── tests/test_health.py
│   ├── yoyo.ini
│   ├── requirements.txt
│   ├── Dockerfile
│   └── .env.example
├── frontend/                 # Vite + React + TS
├── docker-compose.yml        # Postgres 17, named volume, port 5432
└── README.md
```

## Next steps

- Pick the application domain (Stage 2).
- Design the real schema, add indexing, stored procedures, transactions,
  and the two required interfaces (data management + reporting).
- Point `DATABASE_URL` at a Neon connection string when moving off local
  Docker Postgres -- no code changes needed, just the `.env` value.
