#!/usr/bin/env bash
# gotcontext SessionStart hook — emit live plan-gated tool list into the session.
# v1.16.2 — closes the v1.5.1 gc_blast_radius drift class at runtime.
#
# Output goes to stdout; Claude Code surfaces it as session-context.
# Falls back silently when the API is unreachable so the hook never
# blocks a session start. CLAUDE_PLUGIN_ROOT is injected by Claude Code.

set -u

URL="${GOTCONTEXT_API_URL:-https://api.gotcontext.ai}/v1/mcp/prime"
TIMEOUT_SECS=3

if command -v curl >/dev/null 2>&1; then
  # -m: max time, -s: silent transport, -f: fail on HTTP errors.
  curl -m "$TIMEOUT_SECS" -s -f "$URL" 2>/dev/null || exit 0
  exit 0
fi

# No curl available — exit silently. The plugin still works without enrichment.
exit 0
