---
paths: ["backend/tests/**"]
---

# Test conventions

- Integration tests against the real Docker Postgres. Never mock psycopg, a
  connection, or a query result. If a test needs the DB and it is not up, the
  right outcome is a loud connection error, not a mock.
- Use `TestClient(app)` as a context manager so the lifespan opens the pool:
  see `tests/test_health.py`.
- State resets per test: a fixture wraps the test in a transaction and rolls
  back, or truncates the touched tables in teardown. Tests must pass in any
  order and twice in a row.
- Fixtures create their own data explicitly. No shared seed file, no reliance
  on rows another test left behind.
- Test draft CRUD, ownership, invalid pen-pal associations, canonical pairs,
  immutable statuses, SQL word count, report filters/aggregates, and DB options.
- Use disposable PostgreSQL schemas so demo data is preserved.
- Assert on behaviour and returned values, not on the SQL text.
