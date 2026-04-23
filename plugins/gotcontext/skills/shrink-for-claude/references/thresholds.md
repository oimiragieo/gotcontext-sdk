# Fidelity thresholds — when each level earns its keep

Reference material for `shrink-for-claude`. Claude reads this only when
it decides the decision is subtle enough to justify the lookup.

## Size bands

| Input size | Recommended fidelity | Typical savings | Why |
|------------|----------------------|-----------------|-----|
| <1k tokens | don't compress | — | Overhead beats savings |
| 1-3k tokens | `balanced` | ~40% | Marginal but ergonomic |
| 3-15k tokens | `balanced` | ~50-70% | Sweet spot |
| 15-100k tokens | `aggressive` then follow-up | ~85% | Full-doc Q&A at scale |
| >100k tokens | Batch-compress, index, retrieve | — | Use `batch-compress` skill |

## Content type overrides

- **Reference docs you'll cite verbatim** (RFCs, specs, contracts) →
  `detailed` even if small. Users will re-read the quotes.
- **Conversational threads / meeting notes** → `aggressive` — the
  "who said what about X" signal survives heavy compression.
- **Code** → `detailed` and prefer `review-pr-diff` or
  `extract-api-surface` skills, which use AST-aware compression.
- **Legal / compliance text** → `detailed` only. Sentence structure
  matters.

## What not to compress

- Any text the user plans to paste into another system verbatim.
- Error messages or stack traces — they're already compact; compress
  loses the exact line number.
- JSON the user wants to manipulate structurally — compression returns
  narrative prose, not valid JSON.
