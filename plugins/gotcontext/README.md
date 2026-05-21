# gotcontext — Claude Code plugin

**Shrink what Claude reads.** Outcome-oriented skills that call
[gotcontext.ai](https://gotcontext.ai)'s PageRank-based semantic compression API
so you can fit 3-5x more documentation, code, or diffs into a single context
window.

## Install

From inside Claude Code:

```
/plugin marketplace add oimiragieo/gotcontext-sdk
/plugin install gotcontext
```

First run prompts for a free API key. Get one at
<https://gotcontext.ai/dashboard/settings>.

## Skills bundled

| Skill | When to invoke |
|-------|----------------|
| `shrink-for-claude` | You have a file/directory/URL you want Claude to read, but it's too long for the context window. |
| `extract-api-surface` | You need Claude to understand a codebase but don't want to paste every file — extract just the public API. |
| `review-pr-diff` | A git diff is about to be reviewed and the context is bloated with noise (lockfile bumps, generated code). |
| `ingest-docs` | You're pointing Claude at a documentation tree for Q&A and want to compress before indexing. |
| `batch-compress` | You have a set of files to compress in bulk for later retrieval. |
| `pre-flight` | You are about to send a large prompt and want a verdict on compression, cost, and context pressure. |
| `session-summary` | You need to clear context but keep a portable summary for recovery. |
| `compress-mcp-manifest` | You need to shrink an MCP tools/list manifest before handing it to an agent. |

## What this plugin gives you over raw `gotcontext` MCP

The raw MCP server exposes a broad low-level tool catalogue (AST traversal,
skeleton reads, graph search, platform tools, and more). New installs default
to `https://api.gotcontext.ai/mcp?profile=core` for the lightweight compression
surface; switch the MCP server URL to `?profile=full` when a skill needs a
platform tool such as `gc_pre_flight`.

This plugin curates the MCP surface into **outcome-shaped skills** Claude can
reason about at the task level — matching the
[2026 Anthropic guidance](https://claude.com/docs/plugins/submit) that plugins
should "bundle related capabilities into a coherent package that solves a
specific job function end-to-end."

## Links

- Docs: <https://gotcontext.ai/docs>
- Machine-readable docs: <https://gotcontext.ai/docs.md>
- API reference: <https://api.gotcontext.ai/api/docs>
- Source: <https://github.com/oimiragieo/gotcontext-sdk/tree/main/plugins/gotcontext>

## License

MIT © gotcontext.ai
