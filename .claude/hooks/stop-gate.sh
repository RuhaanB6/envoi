#!/bin/bash
# Stop: refuse to end the turn with a broken lint or typecheck.
# Cheap when nothing changed -- one `git diff --name-only` and out.
set -u

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
CHANGED=$(git -C "$ROOT" diff --name-only HEAD 2>/dev/null)
[ -n "$CHANGED" ] || exit 0

STATUS=0
OUT=""

if echo "$CHANGED" | grep -qE '^backend/.*\.py$'; then
  RUFF="$ROOT/backend/.venv/bin/ruff"
  if [ -x "$RUFF" ]; then
    if ! RESULT=$("$RUFF" check "$ROOT/backend" 2>&1); then
      OUT="$OUT$RESULT"$'\n'
      STATUS=2
    fi
  fi
fi

if echo "$CHANGED" | grep -qE '^frontend/.*\.tsx?$'; then
  if [ -d "$ROOT/frontend/node_modules/typescript" ]; then
    if ! RESULT=$(cd "$ROOT/frontend" && npx tsc -b --noEmit 2>&1); then
      OUT="$OUT$RESULT"$'\n'
      STATUS=2
    fi
  fi
fi

if [ "$STATUS" -ne 0 ]; then
  echo "$OUT" >&2
  exit 2
fi

exit 0
