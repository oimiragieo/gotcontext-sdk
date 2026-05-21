---
name: session-summary
description: Compress a session's conversation history into a portable summary that can be re-injected after /clear. Use this skill when context is filling up and the agent needs to recover state after clearing. Works even when Claude Code's own auto-compact has failed because gotcontext runs the summarization on its own infra. Trigger phrases include "summarize this session", "I need to clear context but keep what we built", "compact failed help me recover", "save this conversation before reset".
version: 1.0.0
---

# session-summary

## When this skill is the preferred path

Context fill is high (90%+ of the window) and `/compact` is failing or
about to fail. The agent needs to clear and resume without losing the
work it has done so far. `gc_session_summary` produces a portable
summary the agent can re-inject after `/clear`.

This skill is the natural pair to `gc_pre_flight`. When pre_flight
returns the `clear_first` verdict, the workflow is:

1. Call `gc_session_summary` with the conversation history.
2. Use `/clear` (Claude Code's built-in).
3. Send the returned `restoration_instructions` as your first user
   message in the cleared session.
4. Call `gc_pre_flight` again with the next prompt — context fill is
   now low, you'll get `send_compressed` or `send_as_is`.

## How to use it

Call `gc_session_summary` with one of:

- `messages` — structured conversation history as a list of
  `{role, content}` dicts. Roles: `user`, `assistant`, `system`,
  `tool`. Preferred when available.
- `text` — concatenated conversation as a plain string. Use when
  structured messages aren't available.

If both are passed, `messages` wins.

Optional:

- `keep_facts` — facts the summary MUST preserve verbatim (file
  paths, decisions, blockers, identifiers). Each item is prepended
  to the summary as a bullet point and not compressed.
- `target_tokens` — max size for the summary. Default 4000.

## What you get back

```json
{
  "summary": "<compressed-summary-string>",
  "key_facts": ["...", "..."],
  "tokens_in_original": 184000,
  "tokens_in_summary": 4200,
  "compression_ratio": 0.023,
  "restoration_instructions": "After /clear, send this as your first user message...",
  "recommendation": "Summary 97.7% smaller than original. Run /clear, then send..."
}
```

The `restoration_instructions` field is canonical — copy it into your
next user message verbatim and the agent resumes with the compressed
context attached.

## Why this skill exists

- Anthropic GH#42647 (open): "severe token inefficiency (50K-300K+
  tokens per event) due to repeated full-context resubmissions ...
  Autocompact triggers at ~187K tokens and submits the entire bloated
  context for summarization." Our summarization runs OUTSIDE the
  exhausted Claude context — it works when Claude Code's own
  auto-compact would fail.
- Anthropic GH#7910 (closed, not_planned): "Claude Code frequently
  becomes unable to compact because it uses almost all of the 200k
  token context window, and there isn't enough context left for
  compaction." This skill is the recovery path that issue asked for.
- LocalLLaMA pattern: "Treat the context window like RAM and the
  scratchpad like disk." This skill IS the scratchpad.

## Failure-mode contract

Never raises to the agent. If the compression service is degraded,
the response returns the truncated head of the conversation as a
fallback summary plus a `recommendation` field flagging the
degradation. The agent always gets a structured response it can
re-inject.

## Plan availability

Available on every plan including Free. Volume is governed by your
existing per-month compression quota — same posture as
`gc_pre_flight`.
