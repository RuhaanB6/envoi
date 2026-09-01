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

from psycopg import Connection
from psycopg_pool import ConnectionPool

from app.config import settings

# min_size=1 keeps at least one warm connection; max_size=10 is plenty for a
# course project. open=False: the pool is opened explicitly during the
# FastAPI lifespan instead of at import time.
pool = ConnectionPool(
    conninfo=settings.database_url,
    min_size=1,
    max_size=10,
    open=False,
)


def get_conn() -> Iterator[Connection]:
    """FastAPI dependency that yields a pooled connection for one request."""
    with pool.connection() as conn:
        yield conn
