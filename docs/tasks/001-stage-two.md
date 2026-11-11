# 001 — Complete the Stage 2 demo

Written November 11, 2026. Status: in progress.

## Goal
A local user can select a demo identity, create/edit/delete their own draft letters,
and inspect a filtered mailbox report backed by PostgreSQL. The November 11 request
supersedes older authentication, tags, delivery, and memory-model plans.

## Files
- Reversible SQL migrations for users, penpalships, letters, constraints, and triggers.
- Repeatable seed script: five users, active pairs, at least fifteen letters.
- FastAPI resource/report routes and parameterized SQL query module.
- React API client, database selectors, compose/edit form, mailbox/report interface.
- Real PostgreSQL integration tests, README, database notes, demo outline, decisions.

## SQL
Primary/foreign keys; canonical user pairs; membership trigger; immutable non-drafts;
SQL word counts; one filtered relation feeds aggregate and detail results without
multiplying letters. UI inserts force draft status. SQL scopes writes to the sender.

## Tests
Constraints, canonical pairs, membership, draft CRUD, other-user writes, immutable
non-drafts, SQL word counts, all report filters, empty reports, changing aggregates,
and database-populated options. Isolate each test in a disposable PostgreSQL schema.

## Out of scope
Authentication, delivery scheduling, animations, deployment, invites, memory permissions.

## Verification
Run migration apply/rollback/apply, pytest, Ruff, frontend build/lint, and browser CRUD
with report/filter assertions. Push coherent commits to the existing public repository.
AI disclosure must state actual assistance; exact course-policy wording is pending.
