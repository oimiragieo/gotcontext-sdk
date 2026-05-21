---
name: pre-flight
description: Pre-flight check before sending an expensive LLM prompt. Returns a verdict (send_as_is, send_compressed, warn_context_limit, clear_first), the compressed prompt body inline, a cost preview against on-demand list pricing, and a cache hit likelihood. Use this skill whenever an agent is about to submit a prompt above ~1000 tokens or when context fill is unknown. Trigger phrases include "estimate cost before sending", "should I compress this prompt", "am I about to run out of context", "preview compression savings".
version: 1.0.0
---

# pre-flight

## When this skill is the preferred path

The user (or the agent itself) is about to send a prompt that might be
expensive, redundant, or context-window-exhausting. Instead of sending
blindly and finding out only when the bill arrives or the conversation
hits 200k tokens, the agent calls `gc_pre_flight` first to get a
structured answer.

This skill is the gotcontext SKU. **One MCP call replaces context
warnings, compression decisions, and cost previews.**

## How to use it

Call `gc_pre_flight` with the proposed prompt body. Optionally pass:

- `hint` — what the agent is trying to do ("refactor", "debug", "plan").
  Guides the compression strategy.
- `target_model` — the LLM that will receive this prompt
  ("gpt-4o", "claude-opus-4-7", etc.). Drives cost preview accuracy.
- `current_context_used_pct` — agent's estimate of its own context fill
  (0-100). Drives the `warn_context_limit` and `clear_first` verdicts.

## What you get back

A structured response (JSON) with these fields:

- `verdict`: one of `send_as_is`, `send_compressed`, `warn_context_limit`, `clear_first`
- `compressed_prompt`: the actual compressed body (when verdict is `send_compressed`); null otherwise
- `tokens_in_original` / `tokens_in_compressed`: token counts
- `compression_ratio`: 0.0-1.0
- `estimated_cost_original_usd` / `estimated_cost_compressed_usd` / `estimated_savings_usd`
- `cache_hit_likelihood`: 0.0-1.0 — probability that the prompt's prefix is in the gotcontext semantic cache
- `context_warning`: null OR an object describing the projected context fill if the agent sends as-is
- `recommendation`: human-readable action

## How to act on the verdict

| Verdict | Action |
|---|---|
| `send_as_is` | Send the original prompt. Compression wouldn't beat 30% savings. |
| `send_compressed` | Use the `compressed_prompt` field as the prompt body. Costs less, fits more. |
| `warn_context_limit` | The original prompt would push context fill to 90%+. Send compressed body OR run "gc_session_summary" (v1.21.1) first. |
| `clear_first` | Context is critical. Run "gc_session_summary" (v1.21.1), then `/clear`, then re-inject the summary, then send. |

## Why this skill exists

- Anthropic GH#25798 closed as duplicate, unfixed for 2 months: agents have
  no proactive context-window warnings. `gc_pre_flight`'s
  `warn_context_limit` and `clear_first` verdicts close that gap.
- Cursor and Claude Code users routinely complain about 4M-token bursts on
  trivial tasks. `gc_pre_flight`'s cost preview shows the bill BEFORE
  you commit to it.
- LLMLingua and similar compressors require a separate compression call,
  then a separate cost-estimation call, then the agent needs context
  awareness from somewhere else. `gc_pre_flight` is one call that does
  all three.

## Plan availability

Available on every plan including Free. Volume is governed by your
existing per-month compression quota — not by allowlist exclusion.
This is the conversion driver: Free users see real cost previews and
real verdicts; Pro+ users get unlimited calls.

## Before writing code — use the agent-prep tools (Pro+)

`gc_pre_flight` answers "should I compress?" before sending a prompt.
For the paired question — "what should I actually change?" — two
complementary tools are available on Pro+ plans:

- `gc_agent_capsule`: returns an actionable context capsule
  (primary targets, snippets, validation commands, rollback metadata,
  confidence score) before any non-trivial code change.  Wraps
  `tg agent`. Use this as the first call whenever an agent is about to
  touch multiple files or a non-obvious symbol.

- `gc_edit_plan`: returns a machine-readable edit plan (which files
  to modify, what to add/remove, validation_commands to verify the
  result).  Wraps `tg edit-plan`. Use this instead of free-form "let
  me think about this" planning loops — the plan comes back structured
  and executable.

Typical pre-code agent sequence:
1. `gc_pre_flight` — is the prompt cost-efficient?
2. `gc_agent_capsule` — what do I need to look at?
3. `gc_edit_plan` — exactly what do I change?
4. Make the edits, run the validation_commands from the plan output.
