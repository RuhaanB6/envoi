---
name: handoff
description: Write docs/HANDOFF.md so the next session can resume without reconstruction.
disable-model-invocation: true
---

# /handoff

Gather from this session, not from guesswork: `git status --short`,
`git diff --stat HEAD`, `git log --oneline -5`, and the task spec path in play.

Overwrite `docs/HANDOFF.md` with exactly these sections:

- **Task in progress** — one line, plus the `docs/tasks/NNN-*.md` spec path
  (or "none — clean stopping point").
- **Files modified this session** — the paths, uncommitted ones marked.
- **Verified** — what actually ran green (tests, /verify-app, a manual check).
- **Not verified** — what was written but never run. Be honest; this is the
  section that saves the next session.
- **Next step** — the single next action, concrete enough to start from.
- **Open questions** — decisions waiting on Ruhaan. Empty is fine.

Date it. Keep the whole file under 25 lines; it is a handoff, not a log.
Then say in one line that it is written, and remind that `/clear` is next.
