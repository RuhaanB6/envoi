---
name: data-model
description: Schema, letter lifecycle and product rules for the letters app. Use when touching migrations, the db module, or anything that reads/writes letters.
---

# Data model

Full product reasoning lives in `docs/project-context.md`. This is the part you
need to write correct SQL.

## Two modes, strictly separate

- **Pen-pal** — an ongoing correspondence between two users. Starts as an
  invite, becomes `active` on accept. Letters take time to arrive, derived from
  the distance between the two users' cities.
- **Direct send** — a one-time letter to anyone, via a share link. The recipient
  need not have an account. Delivered instantly or at a scheduled time.

A letter is one or the other; `penpalship_id` is non-null exactly when
`mode = 'penpal'`.

## Tables

```
users             (id, username UNIQUE, email UNIQUE, password_hash, display_name,
                   city, lat, lng, created_at)
sessions          (id, user_id, token_hash UNIQUE, created_at, expires_at)
penpalships       (id, user_a, user_b, status [invited|active|ended], invited_by,
                   distance_km, delay_seconds, created_at, accepted_at,
                   UNIQUE(least(user_a,user_b), greatest(user_a,user_b)))
letters           (id, sender_id, mode [penpal|direct], penpalship_id NULL,
                   reply_to_id NULL, subject, body, word_count,
                   status [draft|scheduled|in_transit|delivered],
                   created_at, updated_at, send_at, deliver_at, delivered_at)
letter_recipients (letter_id, recipient_user_id NULL, recipient_email NULL,
                   share_token UNIQUE NULL, opened_at NULL)
view_requests     (id, letter_id, requester_id, status [pending|approved|denied],
                   requested_at, decided_at)
tags              (id, name UNIQUE)
letter_tags       (letter_id, tag_id)
```

## Lifecycle

`draft → scheduled → in_transit → delivered`, forward only.

- Editable and deletable **only** while `status IN ('draft','scheduled')`.
  Immutable after that. Enforce in the procedure, not just the UI.
- `send_letter(...)` sets `deliver_at` from the pen-palship's `delay_seconds`,
  moves the letter out of `draft`, writes `letter_recipients`, all in one
  transaction.
- `deliver_due_letters()` sweeps `status = 'in_transit' AND deliver_at <= now()`
  with `FOR UPDATE SKIP LOCKED` and stamps `delivered_at`.
- `accept_penpalship(...)` takes `FOR UPDATE` on the penpalship row so two
  concurrent accepts cannot both win.

## Memory model (the emotional core)

Once a letter is delivered the **sender keeps only a stub**: recipient, date,
subject, word count, distance. Not the body.

- To reread it, the sender opens a `view_requests` row; the recipient approves
  or denies via `decide_view_request(...)`.
- A recipient may also "return" a letter unprompted — an approved view request
  the sender never asked for.
- This visibility rule belongs in every query that reads a letter body, not in
  a Python `if`. A sender selecting their own delivered letter gets the body
  only when an approved `view_requests` row exists.
- Open question in `docs/project-context.md`: whether direct sends to non-users
  get this treatment (probably not — nobody can approve).

## Indexes to justify in the write-up

`letters(sender_id, status)`, `letters(status, deliver_at)` for the sweep,
`letters(penpalship_id, delivered_at)`,
`letter_recipients(recipient_user_id, letter_id)`, `sessions(token_hash)`.

## Demo affordance

Waiting 30 hours to show delivery is not a demo. Keep an admin-only
`advance_clock(interval)` procedure or a `DELIVER_NOW` flag.
