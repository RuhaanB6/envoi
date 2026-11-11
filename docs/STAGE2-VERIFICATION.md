# Stage 2 acceptance record

Verified November 11, 2026, using local PostgreSQL 17.6, a running FastAPI server,
and React/Vite in the browser. This records checks performed by the coding
assistant; it does not attest to the student's independent review.

## Mandatory workflow

| Step | Result and evidence |
|---|---|
| Start PostgreSQL, API, frontend | PostgreSQL healthy; FastAPI 8000 and Vite 5173 started; live health HTTP 200. |
| Select database-backed identity | Browser switched Maya → Ruhaan; `/users` compared with a direct SQL SELECT. |
| Record baseline | Ruhaan: 10 matching, 22.8 average words, 4 sent, 6 received. |
| Create draft through UI | Created a five-word pen-pal draft to Maya using pair #1. |
| Verify PostgreSQL and report | Direct SQL found draft #19 with matching sender/recipient/pair; report 11 / 21.2 / 5 / 6. |
| Edit body through UI | Changed to twenty words; direct SQL returned word count 20; browser average became 22.5. |
| Delete through UI | Deleted the disposable draft; browser returned to 10 / 22.8 / 4 / 6. |
| Apply all report filters | Browser: Maya + pen-pal + delivered + October 27, 2026 through the same date returned one 25-word letter. |
| Verify option sources | Live users, recipients, DISTINCT modes/statuses compared with PostgreSQL; integration test adds a user and observes new recipient option. Active pair options are selected with a database JOIN. |
| Reject invalid pair | Running HTTP API returned 422 for mismatched recipient/pair; integration tests exercise direct SQL and invalid updates too. |
| Reject immutable writes | Running HTTP API returned 409 for UPDATE/DELETE of owned in-transit/delivered rows. Direct SQL UPDATE/DELETE raised CheckViolation. Browser showed Read only. |
| Review relevant SQL/API | Raw parameter values use `%s`; schema enforces keys/checks/membership; write WHERE clauses scope sender/status; one report statement avoids row multiplication. |

The HTTP acceptance script separately creates, edits, verifies, and removes a
direct draft. Its baseline/create/edit/delete statistics match the browser flow.
It checks individual filter counts against independent SQL and leaves the original
demo statistics unchanged. No seeded letters were deleted during acceptance.

## Corrections found during verification

- A pooled connection could commit after an HTTP success was received. The mailbox
  connection dependency now has function scope, so commit completes before sending.
  The live script verifies persistence immediately through another connection.
- Native date-field interaction needed blur handling as well as change handling.
  Browser testing confirmed date filters after the fix, including a same-day range.
- React Hook Form observation uses `useWatch`, eliminating its lint warning.

## Additional checks

- Migration apply → rollback → apply succeeded before seeding.
- Running seed twice retained 5 users, 5 active pairs, and 18 letters.
- Backend integration tests: **39 passed**, twice consecutively, using disposable
  schemas that preserve demo data.
- Frontend production build and Oxlint succeeded.
- Backend Ruff succeeded.

A final browser regression also created/edited/deleted a direct draft to Nora,
observing the same 10 → 11 → 10 counts and 22.8 → 21.2 → 22.5 → 22.8 averages.

The final commit is recorded in the completion response. The
installed Starlette/httpx TestClient emits a deprecation warning; tests pass.
There are no unverified mandatory workflow steps. The student's personal
understanding and explanation remain their responsibility.
