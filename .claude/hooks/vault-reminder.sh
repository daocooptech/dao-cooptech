#!/usr/bin/env bash
# Stop hook: periodically reminds Claude to log new product-owner decisions
# and open questions into the Obsidian vault (seekstone MCP) before finishing.
# Cooldown-gated (not per-turn) to avoid nagging/looping on every response.

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
STATE_FILE="$SCRIPT_DIR/.vault-reminder-last"
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

echo "$NOW" > "$STATE_FILE"

reason='Перед тем как закончить: проверь, не появились ли в этой части разговора новые решения владельца продукта или новые открытые вопросы (экономика/архитектура/дизайн) по проекту ДАО КООПЕХ. Если да — запиши их через mcp__seekstone__* в vault: решения в «Журнал решений владельца.md», вопросы в «Открытые вопросы.md» (см. «Инструкции для Claude.md» за полными правилами). Если ничего нового не появилось — просто заверши ответ как обычно, никаких лишних действий не требуется.'

# Emit compact JSON (reason has no double quotes/backslashes to escape here).
printf '{"decision":"block","reason":"%s"}' "$reason"
