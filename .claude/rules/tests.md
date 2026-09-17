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
- One test per business rule the rubric cares about, named for the rule:
  editing a delivered letter is rejected, the delivery sweep only moves letters
  past `deliver_at`, two concurrent accepts of one invite yield one active
  penpalship, a sender cannot read a delivered body without an approved view
  request, the report's aggregates match hand-computed values on fixed data.
- Assert on behaviour and returned values, not on the SQL text.
