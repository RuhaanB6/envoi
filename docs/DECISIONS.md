# Decisions

Append-only. One paragraph per decision, newest at the bottom. Record the
decision and why, not the discussion.

## 2026-09-02 — Stack: FastAPI + React + raw psycopg3, no ORM

Backend is FastAPI with uvicorn; the frontend is React + TypeScript on Vite with
TanStack Query, React Router, React Hook Form + Zod, and Tailwind. Database
access is psycopg 3's `ConnectionPool` with raw parameterized SQL and **no ORM**,
because the SQL is what CS348 grades and an ORM would hide it. Ruled out: any
ORM, the MERN stack, Supabase/PostgREST (hides the SQL layer), and Flask (it
would duplicate an existing resume project).

## 2026-09-02 — Migrations: yoyo, plain .sql forward + rollback pairs

yoyo-migrations over Alembic, because Alembic is built around SQLAlchemy models
we deliberately do not have. Each migration is a hand-written `.sql` file with a
matching `.rollback.sql`, which keeps the schema reviewable as SQL and makes
"apply, roll back, apply again" a real test.

## 2026-09-02 — Postgres 17 locally via Docker, Neon later

Docker Compose runs Postgres 17.6 pinned to match what Neon supports, so moving
to the cloud is a `DATABASE_URL` change and nothing else. Deploy targets: Neon
for the database, Render for the API, Vercel for the frontend — which also
covers the course's cloud bonus.

## 2026-09-17 — Domain: a letters app

The product is a place where letters behave like letters: you write to someone,
send it, and it leaves you. It is not a chat app with stationery. Two strictly
separate modes — pen-pal correspondence between two users, and one-off direct
sends via a share link to anyone. Correspondence with one person is a
first-class object with its own history. CS348 is the excuse, not the point;
every decision is made as if the app outlives the course.

## 2026-09-17 — Delivery takes time, based on distance

Pen-pal letters are delayed by a duration derived from the city-level distance
between the two users (opt-in location). This is the visual and emotional core:
letters as signals crossing space, so the UI is built around a letter in transit
rather than an inbox. The delay function and its range are still undecided. The
goal is not a Slowly clone, and the delay applies to pen-pal mode only — direct
sends are instant or scheduled.

## 2026-09-17 — Memory model: the sender keeps a stub, not the body

Once a letter is delivered the sender retains only a stub — recipient, date,
subject, word count, distance — and not the text. To reread it, the sender asks
the recipient, who approves or denies; a recipient may also "return" a letter
unprompted. This makes sending a decision and creates an interaction no
messaging product has. Marked "to confirm" in `docs/project-context.md`: whether
this is the default (vs. the sender keeping a copy), and whether direct sends to
non-users are exempt — probably yes, since nobody can approve a request.

## 2026-09-17 — Letters are immutable after delivery

Edit and delete are allowed only while a letter is in `draft` or `scheduled`.
This is enforced inside the stored procedure, not in the API or the UI, so the
rule holds no matter what calls the database. It also gives Requirement 1's CRUD
a real business rule to defend.

## 2026-09-17 — Real auth from the start

Username + email + password with argon2 hashing, and server-side sessions in a
database table rather than JWTs. Sessions being a table means they are part of
the schema work rather than a library's black box, and an httpOnly cookie is
simpler to reason about for a course demo.

## 2026-09-17 — Deferred past the MVP

Not in Stage 2 or 3, in rough order for later: real email delivery for direct
sends, the polished memory/return flow, pen-pal discovery and stranger matching,
gifts attached to letters, physical print-and-mail.

## 2026-11-11 — Finish Stage 2 with three tables

The approved deadline scope is users, canonical penpalships, and letters with one
sender and recipient. Local database-backed demo identity selection replaces
authentication. API-created letters remain drafts; triggers reject edits/deletes
of non-drafts and enforce pair membership. A single SQL report computes word
counts dynamically and returns aggregates plus the matching rows. Sending,
delivery scheduling, invitations, tags, memory permissions, animations, and cloud
deployment are excluded. The November 11 user request overrides the older plan.

## 2026-11-11 — Commit writes before sending success

The mailbox connection dependency uses FastAPI function scope. Live HTTP testing
showed that request-scope cleanup could otherwise commit after a client received
success. Explicit transaction blocks plus connection-context cleanup now complete
before the response is sent; a second connection verifies immediate persistence.
