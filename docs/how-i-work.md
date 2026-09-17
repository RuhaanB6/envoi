# How I work on this repo

_For me, not for Claude. Nothing in the repo points here. The design rationale is in claude-code-workflow.md; this is the operating manual._

## Starting

```
cd ~/Desktop/Purdue/"Fall 2027"/Information\ Systems/cs348-project
docker compose up -d           # Postgres; safe to run if already up
claude                         # always from the root
```

Then, first message: **"What does the handoff say?"** That's the ramp-up. If the last session ended mid-task and cleanly, `claude --continue` instead of a new session.

Pick the model with `/model`:

| Use Opus for | Use Sonnet for |
|---|---|
| plan-mode specs | endpoints that copy an existing pattern |
| migrations, stored procedures, indexes | React pages, forms, styling |
| the report query, transactions, concurrency | tests, refactors, docs |
| anything I'd have to defend in the demo | anything I could write myself in an hour |

The SQL reviewer is pinned to Opus and runs there whatever the session model. The diff reviewer and test-runner follow the session (Sonnet on a Sonnet session), which is fine.

## The three sizes of work

Decide the size before typing. Getting this wrong is the most common mistake.

**Tiny** (one-sentence diff): rename, add a field, fix a message. Just say it. No plan, no reviewers.

**Task** (a migration + endpoint + UI, one stored procedure, one report): the normal unit. Full loop below. Most Stage 2 work is this size.

**Milestone** (all of auth, all of Requirement 2): never in one session. Spend one plan-mode session breaking it into tasks and writing the specs, then one session per task.

## The loop for a task

1. `Shift+Tab` until the footer says plan mode.
2. "Read docs/project-context.md, section <X>, and the current <area> code. Write a spec for task <NNN> to docs/tasks/NNN-<name>.md using the template." Read the spec. `Ctrl+G` opens it in my editor if it needs changes.
3. Approve the plan (Shift+Tab back). Let it work. Don't narrate; interrupt with `Esc` only if it's visibly wrong.
4. When it says done: "Use test-runner to run the tests." Then "Fix those." Repeat until clean.
5. "Use sql-reviewer on this task." Then "Use diff-reviewer against docs/tasks/NNN-<name>.md." Fix real gaps. Ignore style opinions; if a reviewer is consistently noisy, tighten its prompt, don't argue with it.
6. **Read the SQL myself.** Every migration, every procedure. The TA will ask me, not Claude.
7. `/verify-app` if the task touched migrations or delivery logic.
8. "Commit anything outstanding." Check `git log --oneline -5` reads like a changelog.
9. `/handoff`, then `/clear` or close the terminal.

Steps 4–7 take five minutes and catch most of what would otherwise become a debugging session later.

## Commands I actually use

| | |
|---|---|
| `Shift+Tab` | cycle permission modes; plan mode is the read-only one |
| `Esc` | stop mid-action, context kept |
| `Esc Esc` / `/rewind` | go back to a checkpoint (conversation, code, or both) |
| `/clear` | new task, fresh context |
| `/compact focus on X` | mid-task, when context is getting heavy |
| `/btw <question>` | side question that doesn't enter history |
| `/context` | what's loaded; check after any config change |
| `/model` | switch Opus ↔ Sonnet |
| `/verify-app` | full check: docker, migrate, health, tests, lint, build |
| `/new-migration <name>` | creates the forward+rollback pair, applies, rolls back, re-applies |
| `/handoff` | writes docs/HANDOFF.md |
| `/doctor` | proposes cuts to CLAUDE.md; run it monthly |
| `@"sql-reviewer (agent)"` | force a specific agent instead of hoping it's picked |

## Prompts that work

- "Write a failing test for <rule>, then make it pass." Better than "implement <rule>".
- "Look at how `health.py` does it and follow the same pattern for <thing>."
- "The build fails with: <paste>. Fix the root cause and show me the passing build."
- "Knowing everything you know now, scrap this and do the clean version."
- "Grill me on this design before you write the spec." (plan mode; makes it interview me)

Prompts that don't: "make it better", "clean this up", "investigate the auth flow" with no scope.

## Rules I hold myself to

- **Two corrections, then `/clear`.** If I've corrected the same thing twice, the context is full of failed attempts. Start over with a better first prompt.
- **New task, new session.** Related follow-ups can share; unrelated work can't.
- **Never end without a handoff.** Twenty minutes of reconstruction next time otherwise.
- **`git diff --staged` before every commit** when I wasn't watching the whole time. My name is on it.
- **Decide, then ask.** The delay function, the memory-model rules, what a "task" includes: these are mine. Write the decision into project-context.md or DECISIONS.md, then ask for the implementation. Claude checks its work against those docs.

## Commits

One logical change per commit, every commit passes ruff/tsc/tests, subject ≤ 50 chars in plain imperative English, body only for "why". Migration and the code that uses it ship together. No attribution lines (the `commit-msg` hook strips them if they sneak in; `git config core.hooksPath .githooks` once on a fresh clone).

## When something is off

| Symptom | Fix |
|---|---|
| Claude ignores a rule in AGENTS.md | file too long, or line ambiguous. Prune. `/doctor`. |
| Startup context feels big (`/context`) | something crept into an always-loaded file; move it to a rule with `paths:` or a skill |
| Path-scoped rules show as loaded in `/memory` before I touch matching files | known bug on some versions; move that content into backend/CLAUDE.md or frontend/CLAUDE.md |
| Stop hook is slow/annoying | move tsc into `/verify-app`, keep only ruff in the gate |
| Reviewer returns noise every time | tighten "report only gaps affecting correctness" in its file |
| Explore on Sonnet misses things | set its `model: inherit` and pay for it |
| Tests fail with connection refused | `docker compose up -d` from root, wait for healthy |
| `yoyo` errors about a database URI | I'm not in `backend/` |
| Subagent not found | new `agents/` dir needs a Claude Code restart the first time |

## Weekly

- `/context` in a fresh session: is the always-loaded set still small?
- `git log --oneline -30`: does it read like a changelog?
- `docs/DECISIONS.md`: anything decided in chat that isn't written down?
- `docs/HANDOFF.md`: still accurate, or stale from a session that didn't end cleanly?
