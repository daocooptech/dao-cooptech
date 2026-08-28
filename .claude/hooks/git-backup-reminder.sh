#!/usr/bin/env bash
# Stop hook: periodically reminds Claude to check for uncommitted/unpushed
# changes and ASK the user whether to commit + push to GitHub (never auto-push
# without explicit per-action confirmation — pushing publishes to a public repo).
# Cooldown-gated (not per-turn) to avoid nagging/looping on every response.

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
STATE_FILE="$SCRIPT_DIR/.git-backup-reminder-last"
COOLDOWN=1200  # seconds between reminders (20 min)

NOW=$(date +%s)
LAST=0
if [ -f "$STATE_FILE" ]; then
  LAST=$(cat "$STATE_FILE" 2>/dev/null || echo 0)
  case "$LAST" in ''|*[!0-9]*) LAST=0 ;; esac
fi

if [ $((NOW - LAST)) -lt $COOLDOWN ]; then
  exit 0
fi

cd "$PROJECT_ROOT" || exit 0

# Only fire if this is actually a git repo with a remote.
git rev-parse --is-inside-work-tree >/dev/null 2>&1 || exit 0

DIRTY=$(git status --porcelain 2>/dev/null)
AHEAD=""
if git rev-parse --verify -q '@{u}' >/dev/null 2>&1; then
  AHEAD=$(git log '@{u}..HEAD' --oneline 2>/dev/null)
fi

if [ -z "$DIRTY" ] && [ -z "$AHEAD" ]; then
  exit 0
fi

echo "$NOW" > "$STATE_FILE"

reason='В проекте есть незакоммиченные и/или незапушенные изменения (проверь `git status`). Перед тем как закончить: спроси пользователя, закоммитить и запушить ли их на GitHub (origin/main) — не делай commit/push молча без подтверждения, это публикация в публичный репозиторий.'

printf '{"decision":"block","reason":"%s"}' "$reason"
