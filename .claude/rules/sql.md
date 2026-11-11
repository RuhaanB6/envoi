---
paths: ["backend/migrations/**", "backend/app/db/**"]
---

# SQL conventions

- Migration files: `NNN_<snake_name>.sql` + `NNN_<snake_name>.rollback.sql`,
  zero-padded to three digits. yoyo pairs them by filename; both must exist.
- Once a migration is committed it is immutable. Correct it with a new one.
- Every rollback fully undoes its forward file, in reverse order, including
  `DROP FUNCTION`/`DROP PROCEDURE` for anything the forward file created.
- Tables and columns: `snake_case`, plural table names, `id` primary keys,
  `*_id` foreign keys, `_at` suffix on every timestamp (`timestamptz`, never
  `timestamp`). Status columns are text with a `CHECK` listing the values.
- Application queries use `%s` placeholders only. Never f-strings, never
  `.format()`, never concatenation — including for identifiers and `ORDER BY`;
  map user-supplied sort keys through a fixed dict.
- Transactions: the `get_conn` dependency yields a pooled connection in
  autocommit-off mode. Wrap multi-statement writes in `with conn.transaction():`
  so the whole unit commits or rolls back together. Do not open your own
  connections outside the pool.
- Lock pair rows while validating letter membership. Protect referenced pair
  participants and non-draft letters with database triggers.
- Every `CREATE INDEX` gets a one-line comment above it naming the query it
  serves. An index with no named query does not get created.
- Stored procedures and functions live in migrations, never in Python strings.
- Stage 2 edit/delete is draft-only, enforced in SQL triggers and guarded writes.
  All API creates are drafts. No delivery or memory-permission implementation.
