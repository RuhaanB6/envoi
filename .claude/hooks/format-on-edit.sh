#!/bin/bash
# PostToolUse (Edit|Write): format and autofix the file that was just written.
# Never blocks -- always exits 0.
set -u

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
FILE=$(python3 -c 'import json,sys; d=json.load(sys.stdin); print(d.get("tool_input",{}).get("file_path",""))' 2>/dev/null)

[ -n "$FILE" ] && [ -f "$FILE" ] || exit 0

case "$FILE" in
  *.py)
    RUFF="$ROOT/backend/.venv/bin/ruff"
    if [ -x "$RUFF" ]; then
      "$RUFF" format "$FILE" >/dev/null 2>&1
      "$RUFF" check --fix "$FILE" >/dev/null 2>&1
    fi
    ;;
  *.ts|*.tsx)
    # oxlint only; Prettier is deliberately not installed in this repo.
    if [ -d "$ROOT/frontend/node_modules/oxlint" ]; then
      (cd "$ROOT/frontend" && npx oxlint --fix "$FILE" >/dev/null 2>&1)
    fi
    ;;
esac

exit 0
