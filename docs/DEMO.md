# Stage 2 demo — about 10 minutes

Prepare: start Docker, apply migrations, run `seed.py`, start FastAPI on port 8000
and Vite on port 5173. Open the app and API docs. Keep the editor open to the
migration, `queries.py`, and `routers/mailbox.py`. Use disposable new drafts,
not a delivered seed letter, for the CRUD demonstration.

## 0:00–1:00 — Scope and identity

Show the demo identity dropdown. Select Ruhaan. Explain that options come from
`GET /api/users` and a PostgreSQL SELECT, rather than frontend sample objects.
There is intentionally no authentication in Stage 2.

## 1:00–3:00 — Database design

Show the three CREATE TABLE statements and PK/FK relationships. Explain one
sender/recipient per letter, no self-sends, canonical pair uniqueness, direct
versus pen-pal CHECK constraints, and the membership trigger. Show that timestamps
use `timestamptz`, and that word count is not a stored letters column.

## 3:00–5:30 — CRUD changes the report

1. Clear filters and record matching count, average, sent, and received.
2. Write a letter to Maya, select Pen pal, and choose the existing pair.
3. Save body `one two three four five` as a new disposable draft.
4. Point out the new table row and changed count/average.
5. Open Edit and replace the body with twenty words. Save and show the new average.
6. Delete the disposable draft and show that all initial statistics return.

The verified seed baseline for Ruhaan was 10 letters, average 22.8, 4 sent,
6 received. A five-word draft produced 11 / 21.2 / 5 / 6; twenty words produced
11 / 22.5 / 5 / 6. Your baseline can differ if seed data was edited.

## 5:30–7:00 — Filters and dynamic selectors

Filter by correspondent, mode, status, then an inclusive UTC creation-date range.
Show that the table and statistics describe the same rows. Clear filters.
Open the compose recipient and pair dropdowns. Explain `/api/options`: database
users, active pairs, and DISTINCT report mode/status values. Seed dates are
relative, so choose the date shown on a visible row.

## 7:00–8:30 — Enforcement and visible SQL

Show `guard_letter()` and its trigger, then guarded UPDATE/DELETE SQL. Show that
in-transit/delivered letters have no edit/delete controls. Run `verify_live.py` to
show the API and direct database reject forbidden writes and mismatched pairs.
Explain that hiding controls alone would be insufficient.

Show `MAILBOX_REPORT`: a single filtered CTE, dynamic word count, aggregate
FILTER clauses, and primary-key user joins. Explain why letters are not counted
twice and why sent plus received equals total.

## 8:30–10:00 — Tests, AI disclosure, and limitations

Show passing pytest, frontend build/lint, and live acceptance output. Show the
README AI Usage section: tools, tasks assisted, and actual verification. Explain
which code you reviewed yourself. Do not claim personal review you have not done.

State scope: local identity selection; drafts only for new letters; seeded
non-draft examples; no sending, scheduler, authentication, or deployment.

## Questions to answer before recording

- Why does swapping pair IDs plus a unique constraint prevent reversed duplicates?
- Why do foreign keys alone not prove membership in a pen-palship?
- What happens if an API caller bypasses the UI and edits a delivered letter?
- Why is `user_id` a demo selection rather than a security credential?
- Where does the transaction commit, and why must it precede a success response?
- How does the report count a received letter without counting it twice?
- What does the word-count function consider a word?
- How are both UTC date boundaries included?
- Which SELECT populates each selector, and what happens with no matching letters?
- How do query keys and invalidation make edits visible in the report?
- Which parts did AI assist with, and what did you personally review and verify?
