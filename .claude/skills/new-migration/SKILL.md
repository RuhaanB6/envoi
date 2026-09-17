---
name: new-migration
description: Create, apply, roll back and re-apply a new yoyo migration pair.
disable-model-invocation: true
---

# /new-migration $ARGUMENTS

`$ARGUMENTS` is the migration name in snake_case (e.g. `users_sessions`).
If it is empty, ask for one and stop.

**Refuse and stop** if the task is to change an existing migration: run
`git ls-files --error-unmatch backend/migrations/<file>`; if it succeeds, that
migration is committed and immutable. Say so and offer a new migration instead.

Steps, all from `backend/`:

1. `ls migrations/` → next sequence number, zero-padded to three digits.
   Files are `NNN_$ARGUMENTS.sql` and `NNN_$ARGUMENTS.rollback.sql`.
2. Write the forward file. Read `.claude/rules/sql.md` first — naming,
   `timestamptz`, `CHECK` on status columns, a one-line justifying comment above
   every index.
3. Write the rollback: everything the forward file created, dropped in reverse
   order, procedures and indexes included.
4. `.venv/bin/yoyo apply --batch`
5. `.venv/bin/yoyo rollback --batch --all` — proves the rollback is real.
6. `.venv/bin/yoyo apply --batch` — back to the forward state.
7. `.venv/bin/python -m pytest -q`

If any step fails, stop, show the error, and fix the migration before retrying.

Finish by printing exactly the two file paths and nothing else.
