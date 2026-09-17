#!/bin/bash
# PreToolUse (Edit|Write): a migration that git already tracks is immutable.
set -u

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
FILE=$(python3 -c 'import json,sys; d=json.load(sys.stdin); print(d.get("tool_input",{}).get("file_path",""))' 2>/dev/null)

[ -n "$FILE" ] || exit 0

case "$FILE" in
  */backend/migrations/*|backend/migrations/*) ;;
  *) exit 0 ;;
esac

if git -C "$ROOT" ls-files --error-unmatch "$FILE" >/dev/null 2>&1; then
  echo "Applied migrations are immutable. Create a new migration." >&2
  exit 2
fi

exit 0
