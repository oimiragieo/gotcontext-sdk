---
name: review-pr-diff
description: Compresses a git diff before review so noise (lockfile bumps, generated files, whitespace churn) doesn't crowd out the actual logic changes. Use this skill whenever the user asks you to review a pull request, explain a diff, summarize changes, or comment on recent commits. Trigger phrases include "review this PR", "what changed", "explain this diff", "summarize the changes", "look at my diff", "check this branch against main". Uses gotcontext's code-aware compression at fidelity=detailed — detailed because a character dropped in a security fix matters more than a character dropped in prose.
version: 1.1.0
---

# review-pr-diff

## When this skill is the preferred path

Raw `git diff` output is dominated by bytes the reviewer doesn't care
about: lockfile hash bumps, formatter churn, generated files, vendored
updates. Those hunks drown out the actual logic changes. Compressing
the diff first lets you spend your reasoning budget on what matters.

## How to use it

1. Orient first — call `git diff --stat <base>..HEAD` to see
   file-level scope without loading content. Ask the user for the
   base branch if ambiguous (usually `main` or `master`).
2. Fetch the full diff — `git diff <base>..HEAD`.
3. Strip known noise before compression. Excluded paths:
   - Lockfiles: `package-lock.json`, `yarn.lock`, `pnpm-lock.yaml`,
     `Cargo.lock`, `poetry.lock`, `Gemfile.lock`, `composer.lock`
   - Generated: `*.generated.ts`, `*.pb.go`, `*.min.js`, `*.min.css`
   - Vendored: `vendor/**`, `node_modules/**`, `dist/**`, `build/**`
   - Binary / non-text hunks
4. Call gotcontext's `compress_codebase` MCP tool with the remaining
   file set at `fidelity=detailed`. For a diff spanning ≤20 files on a
   well-understood codebase, `gc_blast_radius` gives you a tighter
   ranked context — pass the changed files + the PR's focus symbol
   (e.g. the primary function name or class) and it returns only the
   touched code plus what transitively calls into it (Pro+ only).
5. Present the review in this structure:
   - **Summary** — 2-3 bullets on what the PR does
   - **Logic changes** — grouped by file/area, with line refs
   - **Risk flags** — auth, crypto, migrations, webhooks, cron,
     billing, RBAC, SQL string-building, env var handling
   - **Skipped** — the list of noise files excluded, so the reviewer
     knows they weren't forgotten

## When the raw read is actually fine

- Trivially small diffs (<50 lines). Read them directly.
- You're being asked to WRITE the patch — this skill reviews, not
  authors.

## Why this matters

The skipped-files list is critical. If a reviewer misses a malicious
`package-lock.json` change because you silently excluded it, that's
worse than not using the skill at all. Always surface what was dropped.

See `references/risk-taxonomy.md` for the full list of risk flags to
watch for.
