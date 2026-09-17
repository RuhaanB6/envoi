# CS348 Project — Context, Domain, Schema, Plan

_Last updated: 2026-09-17. Replaces `claude/stack-decision-and-stage1-status.md`, which is stale — delete that file._

## Status

- Stage 1 (hello world + demo video) submitted before the 9/2 deadline.
- Stack finalized (below). FastAPI + React scaffold exists locally at `~/Desktop/Purdue/Fall 2027/Information Systems/cs348-project` (reviewed 9/17): `backend/app/{main,config,db}.py` + `routers/health.py`, one real integration test, `migrations/001_initial.sql` (placeholder `stack_check` table — roll back and delete before the real schema), Docker Compose Postgres 17.6, Vite 8 / React 19 / TS 6 / Tailwind v4 frontend with a health page. Backend deps via `requirements.txt` + `uv pip` into an activated `.venv`; lint is `ruff` (backend) and `oxlint` (frontend). No CLAUDE.md, CI, or hooks yet — see `claude-code-workflow.md`.
- Domain finalized 9/17: **a letters app** (see below).

## What this actually is

CS348 is the excuse, not the point. This is a product Ruhaan wants to use and may ship to real users. The semester deliverable is the MVP; every decision below should be made as if the app will outlive the course.

The pitch: a place where letters behave like letters. You write to someone, you send it, and it leaves you. It takes time to arrive if they're far away. You keep a memory of having written it, not the text. If you want to read it again, you ask them. Correspondence with one person over time is a first-class thing with its own history, not a chat thread.

Why that's different from what exists:

- Gifft.me is an ecard maker with a feed. Slowly is stranger-matching with a distance delay. FutureMe is letters to yourself. Lettre is handwriting. None of them treat the *sender's* side as ephemeral; all of them keep a feed of what you sent.
- The memory model is the emotional core. It makes sending feel like a decision, and it creates a small, human interaction ("can I see what I wrote you?") that no messaging product has.
- The distance delay is the visual core. Letters as signals crossing space — the animations and pages should be built around a letter in transit, not around an inbox.

Creative directions raised so far, not yet specced:

- A "letter in transit" page: where it is, how far it's travelled, when it lands.
- The memory stub as an artefact in its own right (date, place, distance, length, first line) — should feel like a stamp or a postmark, not a database row.
- Recipients can "return" a letter unprompted, granting the sender access without being asked.
- The mailbox summary as a shareable, aesthetic report rather than a stats table.

Layers that come after the semester, in rough order: real email delivery for direct sends → the memory/return flow polished → pen-pal discovery/matching → gifts attached to letters → physical print-and-mail. None of these should be built into Stage 2 or 3.

## Stack (final)

| Layer      | Choice |
|------------|--------|
| Frontend   | React + TypeScript + Vite, TanStack Query, React Router, React Hook Form + Zod, Tailwind |
| Backend    | FastAPI + uvicorn, Python env via uv |
| DB access  | psycopg 3 `ConnectionPool`, raw parameterized SQL — **no ORM** |
| Migrations | yoyo-migrations, plain `.sql` forward + rollback pairs |
| Database   | PostgreSQL 17 (Docker Compose locally → Neon) |
| Deploy     | Vercel (frontend), Render (backend), GitHub Actions CI |

Principle: the SQL must stay visible, because that is what's graded. Ruled out: any ORM, MERN, Supabase/PostgREST, Flask (duplicates a resume project).

## Domain: letters

A place to write and receive letters, with a permanent record of correspondence. Two strictly separate modes:

1. **Pen-pal mode.** An ongoing correspondence between two app users. A pen-palship starts with an invite one user sends and the other accepts. Letters take time to arrive based on the distance between the two users (city-level, opt-in location). Delay ranges TBD — the goal is not a Slowly clone.
2. **Direct send.** A one-time letter, delivered instantly or at a scheduled time, via a share link. The recipient does not have to be a user. Real email delivery is a later layer.

Rules that shape the schema:

- A letter is editable and deletable **before** delivery, immutable **after**.
- **Memory model (to confirm):** once delivered, the sender keeps only a stub of the letter (who, when, subject, length), not the body. To reread it the sender requests permission from the recipient, who can grant or deny. The recipient can also proactively "return" a letter (grant access unprompted).
- Letters can optionally reply to another letter.
- Real auth: username + email + password (argon2), server-side sessions in a DB table.

Deferred: gifts, stranger matching, email delivery.

The physics theme survives only as the delivery mechanic — letters as signals that take time to cross a distance. Build the animations around that.

## Draft schema

```
users            (id, username UNIQUE, email UNIQUE, password_hash, display_name,
                  city, lat, lng, created_at)
sessions         (id, user_id → users, token_hash UNIQUE, created_at, expires_at)

penpalships      (id, user_a → users, user_b → users, status
                  [invited|active|ended], invited_by → users, distance_km,
                  delay_seconds, created_at, accepted_at,
                  UNIQUE(least(user_a,user_b), greatest(user_a,user_b)))

letters          (id, sender_id → users, mode [penpal|direct],
                  penpalship_id → penpalships NULL, reply_to_id → letters NULL,
                  subject, body, word_count,
                  status [draft|scheduled|in_transit|delivered],
                  created_at, updated_at, send_at, deliver_at, delivered_at)

letter_recipients (letter_id → letters, recipient_user_id → users NULL,
                   recipient_email NULL, share_token UNIQUE NULL,
                   opened_at NULL, PRIMARY KEY(letter_id, coalesce-key))

view_requests    (id, letter_id → letters, requester_id → users,
                  status [pending|approved|denied], requested_at, decided_at)

tags             (id, name UNIQUE)          -- optional second M:N
letter_tags      (letter_id, tag_id)
```

Indexes to justify in the write-up: `letters(sender_id, status)`, `letter_recipients(recipient_user_id, letter_id)`, `letters(penpalship_id, delivered_at)`, `letters(status, deliver_at)` for the delivery sweep, `sessions(token_hash)`.

## How the rubric maps

- **Requirement 1 (CRUD on a main table):** `letters`, with cascading writes to `letter_recipients` and `letter_tags`. Edit/delete only allowed while `status IN ('draft','scheduled')` — enforce in the stored procedure, not just the UI.
- **Requirement 2 (report):** the user's mailbox summary. Filters populated from the DB: pen pal (dropdown of the user's pen-palships), mode, status, date range. Stats: letters sent/received, avg word count, avg reply time, response rate per pen pal, longest streak, days since last letter, total distance travelled.
- **Stored procedures:** `send_letter(...)` (sets `deliver_at` from the pen-palship delay, flips draft → scheduled/in_transit, writes recipients, all in one transaction); `deliver_due_letters()` (sweeps `status='in_transit' AND deliver_at <= now()`); `accept_penpalship(...)`; `decide_view_request(...)`.
- **Transactions/concurrency:** send is atomic; the delivery sweep uses `SELECT ... FOR UPDATE SKIP LOCKED`; accepting an invite uses `FOR UPDATE` on the penpalship row so two accepts can't race.
- **Cloud:** Neon + Render + Vercel for the bonus.
- **Dev tool for demos:** an admin-only `advance_clock(interval)` procedure or a `DELIVER_NOW` env flag so you don't wait 30 hours to show delivery.

## Stage 2 plan (order of work)

1. Bring the existing scaffold up: `docker compose up -d`, `GET /api/health` hitting the DB, both dev servers running. Roll back and delete the placeholder `001_initial` migration; the real `001` is users + sessions.
2. Migration 001: `users`, `sessions`. Auth endpoints: register, login, logout, `GET /me`. Argon2 via `argon2-cffi`; session cookie, httpOnly.
3. Migration 002: `penpalships`, `letters`, `letter_recipients`, `tags`, `letter_tags`. Seed script with a few users and letters.
4. Requirement 1 UI: compose/edit/delete letter, choose pen pal or direct recipients, tags. Stored procedure `send_letter`.
5. Delivery sweep procedure + a scheduled call from FastAPI (background task on an interval is fine for the course).
6. Requirement 2 UI: mailbox summary with filters and stats. Write the SQL by hand; make it one well-indexed query where possible.
7. Memory model: `view_requests` + the visibility rule in every letter-read query. (If this slips, it's the first thing to cut from Stage 2 and move to Stage 3.)
8. Deploy: Neon, Render, Vercel. Then animations.

## Open items

- Confirm the memory model as the default (vs. sender keeps a copy).
- Decide delay function and range.
- Whether direct-send letters to non-users should also get the memory treatment (probably not — the recipient has no account to approve a request).
