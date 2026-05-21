#!/usr/bin/env bash
# gotcontext PreCompact hook — fires when Claude Code is about to compact.
# v1.16.2 — this is the literal product moment for gotcontext.ai.
#
# Hooks run out-of-band of the MCP session, so we can't directly invoke
# gc_compress here. Instead we print a structured suggestion that
# Claude Code surfaces to the user, prompting them to run gc_compress
# on the largest attached file (CLAUDE.md, design docs, transcripts)
# before allowing the compaction to discard tokens.
#
# Always exits 0 — never blocks compaction.

set -u

cat <<'EOF'
[gotcontext] PreCompact: consider calling `gc_compress` on the largest
attached file (CLAUDE.md, design docs, transcripts) BEFORE allowing
Claude Code to discard tokens. Compression typically reclaims 35-40%
of the to-be-discarded budget without losing semantic fidelity.
EOF

exit 0
