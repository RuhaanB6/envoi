"""
GET /api/health

Proves every layer of the stack is real: it runs an actual query
(`SELECT version()`) through the psycopg connection pool against Postgres,
and reports the Python and FastAPI versions of the process answering the
request.
"""

import sys

import fastapi
from fastapi import APIRouter, Depends
from psycopg import Connection

from app.db import get_conn

router = APIRouter()


@router.get("/health")
def health(conn: Connection = Depends(get_conn)) -> dict:
    # Raw parameterized SQL -- no params needed here, but this is the pattern
    # every other query in the project will follow: conn.execute(sql, params)
    row = conn.execute("SELECT version();").fetchone()
    postgres_version = row[0] if row else "unknown"

    return {
        "status": "ok",
        "postgres_version": postgres_version,
        "python_version": sys.version.split()[0],
        "fastapi_version": fastapi.__version__,
    }
