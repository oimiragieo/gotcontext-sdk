#!/usr/bin/env bash
# gotcontext Stop hook — fires on every turn end.
# v1.16.2 — opportunistic nudge every NUDGE_EVERY turns to look at savings.
# Counter persists under ~/.gotcontext-state so it survives compaction.
# Always exits 0; failure to write counter never blocks a turn.

set -u

STATE_DIR="${HOME}/.gotcontext-state"
COUNTER_FILE="${STATE_DIR}/stop-counter"
NUDGE_EVERY=10

mkdir -p "$STATE_DIR" 2>/dev/null || exit 0

COUNT=0
if [ -f "$COUNTER_FILE" ]; then
  COUNT=$(cat "$COUNTER_FILE" 2>/dev/null || echo 0)
fi
COUNT=$((COUNT + 1))
echo "$COUNT" > "$COUNTER_FILE" 2>/dev/null || true

if [ $((COUNT % NUDGE_EVERY)) -eq 0 ]; then
  echo "[gotcontext] $COUNT turns this session. Run \`gc_get_savings\` to see your token wins."
fi

exit 0
