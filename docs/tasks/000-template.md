# NNN — <task name>

_Written <date>. Status: not started | in progress | done._

## Goal

One paragraph. What is true after this task that is not true now, in product
terms. Not a list of steps.

## Files

Every file this task creates or changes, with a phrase on why.

- `backend/migrations/NNN_<name>.sql` + `.rollback.sql` —
- `backend/app/routers/<x>.py` —
- `frontend/src/<x>.tsx` —

## SQL

The schema changes, the procedures, and the queries, written out. Name each
index and the query it serves. Note where a transaction or a row lock is
required and why.

## Tests

One line per test, named for the business rule it protects. Include the
concurrency and permission cases, not just the happy path.

## Out of scope

What a reasonable reader might expect here but is deliberately not in it, and
where it goes instead.

## Verification

The exact command that proves this task is done.

```
```
