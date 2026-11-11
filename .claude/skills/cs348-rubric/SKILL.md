---
name: cs348-rubric
description: Stage 2 acceptance criteria from the approved November 11 implementation request.
---

# Stage 2 acceptance mapping

This is the project's approved acceptance mapping, not a copy of an official rubric.

1. Three related tables with primary/foreign keys, canonical pen-pal pairs,
   mode/pair consistency, membership enforcement, and immutable non-drafts.
2. UI demo-identity selection; letter list; draft create/edit/delete with
   database-populated recipients and existing pen-palships.
3. Mailbox report with correspondent/mode/status/date filters, counts, SQL average
   word count, sent/received totals, and matching rows without double counting.
4. Successful CRUD must visibly change the report; delete restores its baseline.
5. Database queries populate identity, recipient, pair, and report filter options.
6. Reversible migrations, five seeded users, active pairs, and at least fifteen letters.
7. Real PostgreSQL tests plus mandatory running browser/API/database acceptance.
8. Schema/SQL/run/test documentation, 5–15-minute demo, and accurate AI Usage
   identifying tools, assisted tasks, verification, and student understanding.

No authentication, scheduling, invites, animations, deployment, or memory workflow.
Do not infer extra requirements from the superseded product plan.
