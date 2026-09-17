# backend

Run everything from `backend/` with `.venv/bin/<tool>` (the venv is not on PATH).

- `app/main.py` — FastAPI app; lifespan opens/closes the psycopg pool
- `app/config.py` — pydantic-settings (`DATABASE_URL`, `CORS_ORIGINS`) from `.env`
- `app/db.py` — `ConnectionPool` + the `get_conn` request dependency
- `app/routers/` — one module per resource, mounted under `/api`
- `migrations/` — yoyo `.sql` forward + `.rollback.sql` pairs
- `tests/` — pytest against a real, migrated database

`yoyo.ini` carries its own hard-coded DB URL, separate from `.env`; if yoyo
complains about a database URI you are in the wrong directory.
