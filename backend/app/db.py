"""
Database access layer.

A single psycopg ConnectionPool is created once at app startup (see
app/main.py's lifespan) and closed at shutdown. Routes get a connection via
the `get_conn` FastAPI dependency, which checks a connection out of the pool
for the duration of the request and returns it automatically afterward.

No ORM: every query in this project is raw, parameterized SQL sent through
psycopg. Never use f-strings / string concatenation to build a query --
always pass parameters via %s placeholders so psycopg can safely escape
them and the driver can use prepared statements.
"""

from collections.abc import Iterator

from fastapi import Request
from psycopg import Connection
from psycopg_pool import ConnectionPool

from app.config import settings


def create_pool() -> ConnectionPool:
    """Create a fresh pool for each application lifespan (also safe in tests)."""
    return ConnectionPool(
        conninfo=settings.database_url,
        min_size=1,
        max_size=10,
        open=False,
    )


def get_conn(request: Request) -> Iterator[Connection]:
    """Yield a connection; the pool context commits or rolls back the request."""
    with request.app.state.pool.connection() as conn:
        yield conn
