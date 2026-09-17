@AGENTS.md

## Claude Code

- `test-runner` for any test run — it returns failures only, not the full log.
- `sql-reviewer` and `diff-reviewer` before committing a task's work.
- `/verify-app` before calling a task done. `/handoff` before `/clear`.
- `/new-migration <name>` to create a migration; never hand-roll the pair.
- Anything touching more than one file: plan mode first, and write the spec to
  `docs/tasks/NNN-<name>.md`.
- When compacting, preserve the list of modified files, the current task spec
  path, and the last failing test output.
