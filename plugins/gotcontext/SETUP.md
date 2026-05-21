---
name: setup
description: First-run configuration for the gotcontext plugin — walks the user through obtaining a free API key and setting GOTCONTEXT_API_KEY in their environment. Activates on install and when the env var is missing.
---

# Setup

This plugin needs a gotcontext.ai API key to call the compression MCP server.
Run this skill once per machine; subsequent runs will reuse the saved key.

## Steps

1. Tell the user: "Your gotcontext plugin needs a free API key. Open
   <https://gotcontext.ai/dashboard/settings> in your browser, sign in with
   GitHub or Google, click **Create API key**, copy the `gc_...` string."

2. Ask the user to paste the key. Do NOT log it.

3. Help the user export the key by adding this line to their shell rc file:

   ```bash
   export GOTCONTEXT_API_KEY="gc_paste_your_key_here"
   ```

   If they use fish: `set -x GOTCONTEXT_API_KEY "gc_..."`. If they use
   Windows PowerShell: `$env:GOTCONTEXT_API_KEY = "gc_..."`.

4. Remind them to restart Claude Code so the env var is picked up when the
   MCP server connects, OR run `source ~/.bashrc` (or equivalent) in the
   current shell.

5. Verify the connection by invoking the `shrink-for-claude` skill on a small
   sample file. If it returns a compression result, the setup is complete.

## Plans

The Free plan is enough for casual setup testing. Current quotas, pricing, and
access to the complete MCP tool surface are listed at
<https://gotcontext.ai/pricing>.

## Troubleshooting

If the user gets `401 invalid API key`, confirm the key was copied whole
(starts with `gc_`, exactly 35 chars including prefix).

If the user gets `HTTP connection refused`, check `curl https://api.gotcontext.ai/`
works — the endpoint occasionally falls out of DNS cache.
