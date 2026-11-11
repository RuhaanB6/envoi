---
name: data-model
description: Current Stage 2 schema and letter rules. Read for migrations and letter queries.
---

# Stage 2 data model

The November 11, 2026 user request supersedes the historical eight-table plan.
See docs/DATABASE.md and README.md for the implemented design.

- users: id, username, email, display_name, created_at.
- penpalships: id, user_a_id, user_b_id, status, created_at. A trigger sorts IDs;
  a strict-order CHECK and UNIQUE pair constraint reject self/duplicate pairs.
- letters: id, sender_id, recipient_id, optional penpalship_id, subject, body,
  mode, status, created_at, updated_at, send_at, deliver_at, delivered_at.
- One existing sender and recipient per letter; they must differ.
- Pen-pal mode requires a matching pair; direct mode requires NULL pair.
- SQL triggers prevent changing referenced participants and enforce membership.
- Only drafts can be edited/deleted. Non-draft rows are immutable even in SQL.
- API-created letters always remain drafts. Word count is computed in SQL.
- Demo-user selection is not authentication. Scope reads/writes to the selected ID.
- No auth, tags, delivery scheduler, invites, or memory-permission workflows.
