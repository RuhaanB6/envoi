---
name: cs348-rubric
description: What CS348 grades and which part of this app satisfies each criterion. Use when reviewing SQL, planning a task, or deciding whether something is demo-ready.
---

# CS348 grading criteria

The course grades the database work, not the product. Every item below must be
demonstrable and defensible out loud — the TA asks the student, not the tool.

**Requirement 1 — CRUD on a main table with supporting tables.**
`letters` is the main table, with cascading writes to `letter_recipients` and
`letter_tags`. Create, read, update, delete all reachable from the UI. Update
and delete are allowed only while `status IN ('draft','scheduled')`, and that
restriction is enforced in the stored procedure.

**Requirement 2 — a report with DB-populated filters and aggregates.**
The mailbox summary. Filters are populated from the database, not hard-coded:
pen pal (the user's own penpalships), mode, status, date range. Aggregates:
letters sent and received, average word count, average reply time, response
rate per pen pal, longest streak, days since the last letter, total distance
travelled. Written as hand-written SQL, ideally one indexed query.

**Stored procedures.** `send_letter(...)`, `deliver_due_letters()`,
`accept_penpalship(...)`, `decide_view_request(...)`. They live in migrations
and carry the business rules; the API calls them rather than reimplementing.

**Transactions and concurrency.** Sending is atomic (letter + recipients + tags
in one transaction). The delivery sweep uses `FOR UPDATE SKIP LOCKED`. Accepting
an invite takes `FOR UPDATE` on the penpalship row so two accepts cannot race.

**Indexing.** Each index exists to serve a named query — the report's filter
shapes, the delivery sweep's `(status, deliver_at)` scan, session lookup by
`token_hash`. Be able to show the `EXPLAIN` that justifies it.

**Cloud bonus.** Neon (Postgres), Render (API), Vercel (frontend).

When reviewing, weigh a finding by whether it would cost points or fail a demo.
