# Claude Code workflow for the letters app

_Drafted 2026-09-17. Sources: code.claude.com/docs (best-practices, sub-agents, memory), shanraisshan/claude-code-best-practice, and a few large community configs. Verify anything version-specific with `claude --version`; several features below need Claude Code ≥ 2.1.2xx._

## 1. The honest verdict on subagents

Subagents are efficient for exactly one thing: **keeping noise out of the main context window**. The main window is the scarce resource; performance degrades as it fills, and a subagent's tool calls, file reads and test output stay in its own window while only a summary comes back.

They are *not* efficient for:

- **Parallel implementation on a solo project.** Each subagent starts cold (no conversation history, no files already read), so it re-reads what the main session already knows. Anthropic's own guidance says to keep implementation in the main conversation when phases share context or need back-and-forth.
- **"Teams of 20 specialists" configs.** Popular repos ship dozens of agent files. Each `description` is loaded at startup (there's a 15k-token warning threshold), and the routing gets worse, not better, with more choices. Three well-defined agents beat thirty.
- **Anything you'd want to steer mid-task.** Subagents don't plan interactively and don't take `AskUserQuestion`.

So the design below uses subagents in the three places where the evidence says they pay off: **exploration** (cheap model, read-only), **verbose verification** (test runs, builds), and **fresh-context review** (a reviewer that didn't write the code). Everything else runs in the main session.

## 2. Principles this environment is built on

1. **Context is the constraint.** Anything loaded every session must earn it. Target: `AGENTS.md` under 50 lines plus a `CLAUDE.md` under 20 that imports it. Everything else loads on demand.
2. **Verification closes the loop.** Every task ends with a check Claude can run: tests against real Postgres, `tsc --noEmit`, a build. Hooks make the fast checks unavoidable.
3. **Explore → plan → implement → verify → review → commit.** Plan mode for anything multi-file; skip it for one-line fixes.
4. **Advisory vs. deterministic.** CLAUDE.md is advice. Hooks and `permissions.deny` are enforcement. Rules that must never be broken (don't edit an applied migration, don't read `.env`) go in hooks/permissions, not prose.
5. **Fresh context for review.** The model that wrote the code is biased toward it. Review runs in a subagent that sees only the diff and the task spec.
6. **New task = `/clear`.** Related follow-ups can share a session; unrelated work gets a fresh one. Write a handoff note before clearing.
7. **CLI over MCP.** `psql`, `uv`, `gh`, `docker compose` are cheaper in tokens than MCP tool definitions and Claude already knows them. No Postgres MCP server.

## 3. Target layout

```
cs348-project/
├── AGENTS.md                      # tool-agnostic source of truth, ≤50 lines; Codex/Cursor/Copilot read it natively
├── CLAUDE.md                      # line 1: @AGENTS.md, then ≤15 Claude-only lines
├── GEMINI.md                      # symlink → AGENTS.md (or set context.fileName in Gemini settings)
├── .claude/
│   ├── settings.json              # permissions, hooks, env, model defaults (committed)
│   ├── settings.local.json        # personal overrides (gitignored)
│   ├── rules/                     # path-scoped; load only when matching files are read
│   │   ├── sql.md                 # backend/migrations/**, backend/app/db/**
│   │   ├── api.md                 # backend/app/**/*.py
│   │   ├── frontend.md            # frontend/src/**
│   │   └── tests.md               # backend/tests/**
│   ├── skills/                    # on-demand knowledge and workflows
│   │   ├── data-model/SKILL.md    # schema, lifecycle rules, memory model
│   │   ├── cs348-rubric/SKILL.md  # what is graded; reviewers preload this
│   │   ├── new-migration/SKILL.md # /new-migration <name>  (manual-only)
│   │   ├── verify-app/SKILL.md    # /verify-app  (manual-only)
│   │   └── handoff/SKILL.md       # /handoff — write docs/HANDOFF.md before /clear
│   ├── agents/
│   │   ├── Explore.md             # overrides built-in; model: sonnet
│   │   ├── test-runner.md         # Bash/Read/Grep; returns failures only
│   │   ├── sql-reviewer.md        # read-only; preloads cs348-rubric
│   │   └── diff-reviewer.md       # read-only; checks diff against docs/tasks/<task>.md
│   └── hooks/
│       ├── format-on-edit.sh      # PostToolUse Edit|Write
│       ├── protect-migrations.sh  # PreToolUse Edit|Write
│       └── stop-gate.sh           # Stop: ruff + tsc, blocks turn end on failure
├── docs/
│   ├── project-context.md         # the product/domain/schema doc (already written)
│   ├── DECISIONS.md               # ADR-lite, append-only, one paragraph each
│   ├── HANDOFF.md                 # last session's state; overwritten each time
│   └── tasks/                     # one spec per task, written in plan mode
│       └── 001-auth.md
├── backend/
│   └── CLAUDE.md                  # ≤20 lines: commands + layout of backend only
└── frontend/
    └── CLAUDE.md                  # ≤20 lines: commands + layout of frontend only
```

### Portability across CLIs (Codex, Gemini, Cursor, Copilot)

AGENTS.md is the cross-tool standard; Codex CLI, Cursor, Copilot, Aider and others read it on their own, while Claude Code reads only CLAUDE.md and Gemini CLI reads GEMINI.md. So the split is:

- **AGENTS.md** holds everything that is true regardless of tool: what the project is, commands, layout, non-negotiables, and *plain file paths* to the conventions and knowledge docs. It never mentions skills by slash name, subagents, hooks, or plan mode.
- **CLAUDE.md** is `@AGENTS.md` on line one (Claude Code imports it at launch) followed by a short Claude-only section: which subagents to use when, the `/skill` names, compaction instructions.
- **GEMINI.md** is a symlink to AGENTS.md, or set `"context": {"fileName": "AGENTS.md"}` in Gemini's settings.

The `.claude/rules/*.md` and `.claude/skills/*/SKILL.md` files are plain Markdown, so other tools can read them when told to. AGENTS.md does the telling: "Before editing anything under `backend/migrations/`, read `.claude/rules/sql.md`. Before touching letters/schema logic, read `.claude/skills/data-model/SKILL.md`." Claude Code loads those automatically and ignores the sentence; Codex follows it. One copy of every rule, no drift.

What doesn't port: hooks, `permissions`, and subagent definitions are Claude Code mechanisms. Codex gets its equivalents from `config.toml` (sandbox mode, model choice) if you ever set it up; that's a separate five-minute job, not something to solve now.

### What loads when

| Always (every session) | On demand |
|---|---|
| root `CLAUDE.md` (which imports `AGENTS.md`), rules **without** `paths`, agent `description` lines, skill `description` lines | path-scoped rules (when a matching file is read), skill bodies (when invoked), subagent bodies (when spawned), `backend/CLAUDE.md` / `frontend/CLAUDE.md` (when working in that dir), `docs/*` (when read) |

Check it with `/context` after setup. The always-loaded set should be a few thousand tokens, not tens of thousands.

**Two known gotchas with `.claude/rules/`:** quote every glob in the `paths:` list (unquoted `**/*.py` is invalid YAML), and there have been reports of path-scoped rules loading unconditionally on some versions. After setup, run `/memory` in a fresh session: if the scoped rules show as loaded before you touch a matching file, move their content into `backend/CLAUDE.md` / `frontend/CLAUDE.md` instead (nested CLAUDE.md files are lazy by design).

## 4. Day-to-day loop

**Starting a session**

```
claude                     # Opus 5, in repo root
/context                   # sanity-check what loaded
cat docs/HANDOFF.md        # or just ask "what's the handoff say?"
```

**Per task (multi-file work)**

1. `Shift+Tab` into plan mode. "Read docs/project-context.md section X and the current auth code. Write a spec for task NNN to docs/tasks/NNN-<name>.md: files to change, SQL to write, tests to add, out of scope, and the verification command." Edit the spec with `Ctrl+G` if needed.
2. Approve the plan. Implement. Hooks format on every edit and gate the turn on `ruff` + `tsc`.
3. "Use test-runner to run the backend tests and report only failures." Fix. Repeat.
4. "Use sql-reviewer on the migration and db module for this task." Then "Use diff-reviewer to check the diff against docs/tasks/NNN.md. Report gaps only." Fix real gaps; ignore style noise.
5. `/verify-app` for the end-to-end check (docker up, migrate, rollback, migrate, pytest, build).
6. Commits happen as you go (AGENTS.md says so); at the end, "commit anything outstanding." If a message comes back long, say "split that into smaller commits" once and it will.
7. `/handoff`, then `/clear`.

**Small fixes:** skip the plan and the reviewers. "Rename X to Y and run ruff." Done.

**Context hygiene:** `/btw` for side questions; `/compact focus on <thing>` mid-task if needed; after two failed corrections on the same issue, `/clear` and re-prompt with what you learned.

## 5. Subagent rules

| Agent | Model | Tools | Purpose | Never |
|---|---|---|---|---|
| Explore (override) | sonnet | read-only | codebase search so it never runs on Opus | writes |
| test-runner | sonnet | Bash, Read, Grep, Glob | run pytest / build; return failing tests + errors only | edit files, "fix" things |
| sql-reviewer | opus (always, regardless of session) | Read, Grep, Glob, Bash(read-only psql) | review SQL for correctness, injection, transaction boundaries, indexes, rubric fit | edit files |
| diff-reviewer | inherit (opus) | Read, Grep, Glob, Bash(git diff/log) | compare diff to task spec; report gaps affecting correctness or requirements | style opinions, edits |

Rules that apply to all of them:

- One goal, one output format, no writes unless the job is writing.
- `description` ≤ 2 sentences (it's loaded every session); detail goes in the body.
- Reviewers get `skills: [cs348-rubric]` so they know what's graded without the main session carrying it.
- No nested agents (`disallowedTools: Agent`).
- If you find yourself wanting a fourth "specialist," ask whether it's really a skill (knowledge/workflow, runs in main context) instead.

## 6. Hooks (deterministic)

| Event | Matcher | Script | Behaviour |
|---|---|---|---|
| PostToolUse | `Edit\|Write` | `format-on-edit.sh` | `.py` → `backend/.venv/bin/ruff format` + `ruff check --fix` on that file; `.ts/.tsx` → `npx oxlint --fix` on that file (no Prettier in the repo yet). Silent on success. |
| PreToolUse | `Edit\|Write` | `protect-migrations.sh` | If the target is under `backend/migrations/` and already tracked by git → exit 2 with "applied migrations are immutable; create a new migration". |
| Stop | — | `stop-gate.sh` | If any `.py` changed since HEAD → `backend/.venv/bin/ruff check backend`; if any `.ts/.tsx` changed → `cd frontend && npx tsc -b --noEmit`. Exit 2 with the error on failure so the turn can't end broken. |

`permissions.deny` (native, no script): `Read(./.env*)`, `Read(./backend/.env*)`, `Bash(git push --force*)`, `Bash(rm -rf *)`, `Bash(docker compose down -v*)`.

Commit hygiene is three layers because the first is unreliable: `attribution: {"commit": "", "pr": ""}` in settings, a committed `.githooks/commit-msg` that strips `Co-Authored-By: Claude`, `Generated with [Claude Code]` and `Claude-Session:` lines, and the commit rule in AGENTS.md (≤ 50-char subject, split rather than lengthen, commit as you go).

`permissions.allow`: `Bash(uv *)`, `Bash(backend/.venv/bin/*)`, `Bash(python -m pytest*)`, `Bash(ruff *)`, `Bash(uvicorn *)`, `Bash(npm run *)`, `Bash(npx tsc *)`, `Bash(npx oxlint *)`, `Bash(docker compose up *)`, `Bash(docker compose ps *)`, `Bash(git status*)`, `Bash(git diff*)`, `Bash(git log*)`, `Bash(git add *)`, `Bash(git commit *)`, `Bash(psql *)`, `Bash(yoyo *)`, `Bash(gh pr *)`.

## 7. Setup prompt for Opus 5

**Pre-flight, before running it (5 minutes, you do this by hand):**

1. Roll back and delete the placeholder migration while it's still cheap: `cd backend && .venv/bin/yoyo rollback --batch --all` (yoyo lives in the venv, not on your PATH), then `git rm migrations/001_initial.sql migrations/001_initial.rollback.sql`. It creates a throwaway `stack_check` table; once the immutable-migrations hook exists you'd have to carry it forever. The real schema becomes `001_users_sessions.sql`.
2. Move the health check off `stack_check` if anything referenced it (nothing does today; `health.py` only runs `SELECT version()`).
3. Copy `docs/project-context.md` into the repo (`mkdir docs`).
4. Update `README.md`'s status line and "Next steps": the domain is decided. Or let Opus do it; it's told to.

**What the repo actually looks like (Opus is told to read it, but this is what it will find):**

- Backend runs from `backend/` with an activated `.venv`; deps are in `requirements.txt` installed via `uv pip`, not a `uv`-managed pyproject, so there is no `uv run` and no lockfile. Commands: `yoyo apply --batch`, `yoyo rollback --batch --all`, `uvicorn app.main:app --reload --port 8000`, `python -m pytest`, `ruff check .`. `yoyo.ini` must be run from `backend/` (relative `sources`) and carries its own hard-coded DB URL separate from `.env`.
- Frontend: Vite 8, React 19, TS 6, Tailwind v4 via the Vite plugin, TanStack Query, RHF, Zod, React Router (installed, unused). Lint is **oxlint**, not ESLint; there is no Prettier. Scripts: `npm run dev`, `npm run build` (`tsc -b && vite build`), `npm run lint`.
- Postgres 17.6 in Docker Compose with a health check, creds `cs348/cs348`.
- Layout: `backend/app/{main,config,db}.py`, `backend/app/routers/health.py`, `backend/tests/test_health.py` (real TestClient with lifespan, hits the real DB), `backend/migrations/`, `frontend/src/{App,main}.tsx`.
- No CLAUDE.md, no Makefile, no CI, no hooks. Clean slate.

Copy `docs/project-context.md` into the repo first (create `docs/`). Then open Claude Code in the repo root and paste this. It is long on purpose; Opus should not have to guess.

````text
You are setting up the Claude Code environment for this repository. Read
docs/project-context.md first — it is the source of truth for the product,
stack, schema and plan. Then read the existing backend/ and frontend/ trees
(README.md, backend/pyproject.toml, backend/requirements.txt,
backend/yoyo.ini, frontend/package.json, docker-compose.yml, migrations/,
tests/) so every command you write is one that actually works here. Facts
you will find and must respect: the backend uses an activated .venv with
requirements.txt (no `uv run`, no lockfile); yoyo runs from backend/; the
frontend lints with oxlint and has no Prettier; `npm run build` is
`tsc -b && vite build`. Do not add tools. Do not change application code in
this session except README.md (update its status and next-steps to say the
domain is decided and point to docs/project-context.md); only create the
files listed below. If something in the repo contradicts
project-context.md, stop and ask me before writing.

Design goals, in priority order:
1. Token efficiency. AGENTS.md ≤ 50 lines and CLAUDE.md ≤ 20 lines (it
   imports AGENTS.md). Nothing loads every session
   unless removing it would cause mistakes. Detail lives in path-scoped rules,
   skills, subagent bodies and docs/, all of which load on demand.
2. Verification. Every task ends with a check Claude can run. Hooks enforce
   the fast checks; a skill runs the full one.
3. Enforcement over advice. Rules that must never be broken go in hooks or
   permissions.deny, not prose.
4. Fresh-context review. Reviewers are read-only subagents that see the diff
   and the task spec, not the reasoning that produced the code.

Create exactly these files. Keep every one as short as it can be while still
being unambiguous.

### 1. AGENTS.md (repo root, ≤ 50 lines) — the tool-agnostic source of truth
This file is read natively by Codex CLI, Cursor, Copilot and others, and
imported by CLAUDE.md. It must not mention Claude Code features: no skill
slash-names, no subagent names, no hooks, no plan mode. Sections, in order:
- What this is: two lines. A letters/pen-pal app; CS348 project is the MVP
  milestone; SQL quality is what's graded, so SQL stays hand-written and
  visible.
- Commands: the exact commands for docker up, migrate, rollback, backend dev
  server, frontend dev server, pytest, ruff, tsc, build. Read them from the
  repo; do not invent.
- Layout: one line per top-level directory. No file-by-file descriptions.
- Non-negotiables (≤ 8 bullets): raw parameterized SQL via psycopg3, no ORM,
  no f-string SQL; migrations are forward+rollback pairs and immutable once
  committed; tests hit real Postgres (no DB mocks); business rules that the
  rubric cares about (edit-before-delivery-only, delivery sweep, view
  requests) are enforced in SQL/stored procedures, not only in the API;
  frontend never contains business logic.
- Read-before-editing map (plain paths, so any tool can follow it):
  "Before editing backend/migrations/** or backend/app/db/** read
  .claude/rules/sql.md. Before backend/app/**/*.py read .claude/rules/api.md.
  Before frontend/src/** read .claude/rules/frontend.md. Before
  backend/tests/** read .claude/rules/tests.md. Before touching letters,
  penpalships or delivery logic read .claude/skills/data-model/SKILL.md.
  Grading criteria: .claude/skills/cs348-rubric/SKILL.md."
- Process (≤ 5 bullets, tool-neutral): write a spec to docs/tasks/ before
  multi-file work; run the tests and tsc before declaring anything done;
  append decisions to docs/DECISIONS.md; update docs/HANDOFF.md at the end
  of a session.
- Commits (exact wording, keep it): "Commit after every coherent change, not
  at the end of a task. Subject line ≤ 50 characters, imperative, plain
  English, no scope prefixes or conventional-commit tags. Body only when the
  subject can't carry it, ≤ 3 lines. If a message would need 'and', make two
  commits. No AI attribution of any kind: no Co-Authored-By, no 'Generated
  with', no session links." 

### 2. CLAUDE.md (repo root, ≤ 20 lines)
Line 1 is exactly `@AGENTS.md`. Then a "Claude Code" section only:
- Use test-runner for test output, sql-reviewer and diff-reviewer before
  committing, /verify-app before calling a task done, /handoff before /clear,
  /new-migration <name> for migrations.
- Plan mode + docs/tasks/NNN-<name>.md for anything touching more than one
  file.
- Compaction: "When compacting, preserve the list of modified files, the
  current task spec path, and the last failing test output."
Also create GEMINI.md as a symlink to AGENTS.md (`ln -s AGENTS.md GEMINI.md`).

### 2b. backend/CLAUDE.md and frontend/CLAUDE.md (≤ 20 lines each)
Commands and layout for that half only. Nothing already in AGENTS.md.

### 3. .claude/rules/ (path-scoped; quote every glob)
- sql.md — paths: ["backend/migrations/**", "backend/app/db/**"].
  Conventions for SQL: naming, parameter style, transaction pattern used in
  this repo (read the pool/connection code and describe the actual pattern),
  every index gets a one-line comment justifying it, stored procedures live
  in migrations with a matching DROP in the rollback, delivery/visibility
  rules enforced in SQL.
- api.md — paths: ["backend/app/**/*.py"]. FastAPI conventions actually used
  here: router layout, pydantic models, how a request gets a connection,
  error response shape, auth dependency.
- frontend.md — paths: ["frontend/src/**"]. TanStack Query for server state,
  React Hook Form + Zod for forms, one api client module, Tailwind only,
  components stay dumb.
- tests.md — paths: ["backend/tests/**"]. Real Postgres via docker, fixtures
  that reset state, one test per business rule in the rubric.
Each rule file ≤ 30 lines. Only things Claude can't infer from the code.

### 4. .claude/skills/
- data-model/SKILL.md — the schema, lifecycle rules, two modes, memory
  model, from docs/project-context.md. Description: "Schema, letter lifecycle
  and product rules for the letters app. Use when touching migrations, the
  db module, or anything that reads/writes letters." Body ≤ 80 lines; link
  to docs/project-context.md for the rest instead of duplicating it.
- cs348-rubric/SKILL.md — what the course grades (requirement 1 CRUD with
  supporting tables, requirement 2 report with DB-populated filters and
  aggregates, stored procedures, transactions/concurrency, indexing, cloud
  bonus) and the specific places in this app that satisfy each. ≤ 40 lines.
- new-migration/SKILL.md — disable-model-invocation: true. Takes
  $ARGUMENTS as the migration name. Steps: next sequence number, create the
  forward + rollback pair using the repo's naming, apply, rollback, apply
  again, run pytest, print the two file paths. Refuse if a tracked migration
  is being edited.
- verify-app/SKILL.md — disable-model-invocation: true. From the repo
  root: `docker compose up -d`, then poll `docker compose ps` until postgres
  is healthy (fail after 60s with a clear message if Docker isn't running);
  cd backend and `.venv/bin/yoyo apply --batch`; start uvicorn in the
  background and curl /api/health; pytest; ruff; cd frontend and tsc, npm run
  build. Print a pass/fail table and the raw output only for failures.
- handoff/SKILL.md — disable-model-invocation: true. Overwrite
  docs/HANDOFF.md with: task in progress + spec path, files modified this
  session, what's verified vs. not, next step, open questions. ≤ 25 lines of
  output.

### 5. .claude/agents/
- Explore.md — name: Explore, model: sonnet, read-only tools. Overrides the
  built-in so exploration never runs on Opus. Body: two lines.
- test-runner.md — model: sonnet; tools: Bash, Read, Grep, Glob;
  disallowedTools: Agent. Description ≤ 2 sentences. Body: run the command
  it's given (default: cd backend && .venv/bin/python -m pytest -q), return
  ONLY failing test names, assertion messages and the relevant traceback
  lines. If the failure is a psycopg connection refused on port 5432, return
  the single line "Postgres not reachable — run `docker compose up -d` from
  the repo root" and nothing else. Never edit files; never suggest fixes
  longer than one line.
- sql-reviewer.md — model: opus (pinned, not inherit — SQL review always
  runs on Opus even in a Sonnet session); tools: Read, Grep, Glob, Bash;
  skills: [cs348-rubric]; disallowedTools: Agent, Edit, Write. Body: review
  checklist — parameterization, transaction boundaries, FOR UPDATE where
  concurrent writes are possible, index coverage for the query shapes in the
  report, rollback correctness, rubric fit. Output grouped Critical /
  Should-fix / Optional with file:line. No style commentary.
- diff-reviewer.md — model: inherit; tools: Read, Grep, Glob, Bash;
  skills: [cs348-rubric]; disallowedTools: Agent, Edit, Write. Body: run git
  diff against the base, read the task spec path given in the prompt, report
  only gaps that affect correctness or stated requirements, plus anything
  changed outside the task's scope. Say "no gaps" when there are none.

### 6. .claude/hooks/ (bash, executable, macOS)
- format-on-edit.sh (PostToolUse, matcher Edit|Write): read the file path
  from stdin JSON; .py → backend/.venv/bin/ruff format + ruff check --fix on
  that file; .ts/.tsx → npx oxlint --fix on that file (Prettier is not
  installed; do not add it). Exit 0 always.
- protect-migrations.sh (PreToolUse, matcher Edit|Write): if the path is
  under backend/migrations/ and `git ls-files --error-unmatch` succeeds,
  print "Applied migrations are immutable. Create a new migration." to
  stderr and exit 2.
- stop-gate.sh (Stop): if `git diff --name-only HEAD` includes any .py under
  backend → run `backend/.venv/bin/ruff check backend`; if any .ts/.tsx under
  frontend → run `npx tsc -b --noEmit` in frontend. On failure print the errors to stderr
  and exit 2. Exit 0 otherwise. Keep it under 2 seconds when nothing changed.

### 7. .claude/settings.json (committed)
- hooks wired to the three scripts above.
- permissions.deny: Read(./.env*), Read(./backend/.env*),
  Bash(git push --force*), Bash(rm -rf *), Bash(docker compose down -v*).
- permissions.allow: uv *, backend/.venv/bin/*, python -m pytest*, ruff *,
  uvicorn *, npm run *, npx tsc *, npx oxlint *,
  docker compose up *, docker compose ps *, git status/diff/log/add/commit,
  psql *, yoyo *, gh pr *.
- attribution: {"commit": "", "pr": ""}.
- env: CLAUDE_CODE_MAX_SUBAGENT_SPAWN_DEPTH=1.
Add .claude/settings.local.json and docs/HANDOFF.md to .gitignore.

### 7b. Git hook (belt and braces; the attribution setting is known to be
### ignored on some versions)
Create .githooks/commit-msg (executable) that deletes any line matching
`^Co-Authored-By: Claude`, `Generated with \[Claude Code\]`, or
`^Claude-Session:` from the message file, then run
`git config core.hooksPath .githooks` and mention in AGENTS.md's Commands
section that a fresh clone must run that command once.

### 8. docs/
- docs/DECISIONS.md — seed with the stack decisions and the domain decisions
  from project-context.md, one paragraph each, dated.
- docs/tasks/000-template.md — the spec template: Goal / Files / SQL /
  Tests / Out of scope / Verification command.
- docs/HANDOFF.md — placeholder.

### 9. Verify your own work, then report
- Run `claude plugin validate .claude/agents` and fix anything it flags.
- Run each hook script by hand with a fake stdin payload and show it works.
- Count lines in AGENTS.md, CLAUDE.md and every rule/skill file; list any over budget. Confirm AGENTS.md contains no Claude-specific terms (skill names, subagents, hooks, plan mode).
- Report: a tree of what you created, the line count of everything that
  loads at startup, and anything you were unsure about. Do not summarize
  file contents back to me; I'll read them.
````

## 8. After the setup session

1. Restart Claude Code (new `agents/` and `skills/` directories need a restart the first time).
2. `/context` — confirm the always-loaded set is small. `/memory` — confirm path-scoped rules are *not* listed until you read a matching file.
3. `/doctor` — it proposes cuts to CLAUDE.md for anything derivable from the codebase. Take most of them.
4. Trust the folder when prompted; project-level hooks and agent frontmatter hooks don't run until you do.
5. Run `/verify-app` once on a clean checkout to make sure the baseline passes.
6. First real task: `docs/tasks/001-auth.md` in plan mode.

## 9. Things to revisit after two weeks of use

- If Claude keeps ignoring a CLAUDE.md line, the file is too long or the line is ambiguous. Prune, or convert it to a hook.
- If a reviewer keeps returning noise, tighten its "report only X" clause; don't add a second reviewer.
- If Explore on Sonnet misses things, switch it to `inherit` and eat the cost.
- If the Stop gate is annoying because tsc is slow, move tsc to `/verify-app` and keep only ruff in the gate.
