# Skill trigger-reliability evals

Each `<skill>/eval_set.json` contains 20 queries (15 should-trigger
+ 5 decoys) that exercise whether the skill description is pulling its
weight. A skill whose trigger rate falls below ~80% on its
should-trigger set is a description-tuning target, not a wiring bug.

## Run one skill

```bash
docker run --rm \
  -e ANTHROPIC_API_KEY=sk-ant-... \
  -e GOTCONTEXT_API_KEY=gc_... \
  -e MODE=plugin \
  gotcontext-plugin-test:latest \
  bin/run-skill-eval.sh shrink-for-claude
```

Budget check: each query is a `claude -p` call capped at 60s with
`--max-turns 5`. 20 queries ≈ 20 min wall-clock, ~$1 in Anthropic
tokens (Sonnet).

## Run all five

```bash
docker run --rm \
  -e ANTHROPIC_API_KEY=sk-ant-... \
  -e GOTCONTEXT_API_KEY=gc_... \
  -e MODE=plugin \
  gotcontext-plugin-test:latest \
  bin/run-skill-eval.sh all
```

100 queries, ~90 min, ~$5.

## Output shape

Per skill, prints:
- Per-query PASS/FAIL with expected vs observed trigger
- Aggregate: accuracy, recall (should-fire cases that fired),
  precision (fires that were correct), false-positive / false-negative
  counts
- NDJSON transcript at `/workspace/out/eval-<skill>.jsonl` inside the
  container

## What a "trigger" counts as

The runner greps the `claude -p --output-format stream-json` transcript
for any `tool_use` event with a name containing
`mcp__plugin_gotcontext_gotcontext__`. If any such event appears, the
skill triggered on that query. That's a coarse signal — it doesn't
check whether Claude picked the *right* tool — but it's the signal
that matters for "did the plugin get used at all."

## Iterating on a failing skill

1. Read the failing queries in `/workspace/out/eval-<skill>.jsonl`.
2. Pattern-match why each one failed:
   - **False negatives** (should have fired, didn't): Claude didn't see
     itself in the skill description. Add specific trigger phrases and
     tighten the "when to use" block.
   - **False positives** (shouldn't have fired, did): description too
     broad or steals from an adjacent skill. Add a `when-NOT-to-use`
     section naming the adjacent skill.
3. Edit the skill's `SKILL.md` frontmatter description.
4. Rebuild the image (the plugin is baked in at build time).
5. Re-run the eval. Compare.

Anthropic's skill-creator has an automated loop for this; our eval
harness is the building block.

## Known limits

- Runs are single-shot (`runs_per_query=1`). Real skill-creator uses
  3× for variance; we can bump this via a runner flag once the base
  harness is validated.
- Our fixture set references `/workspace/fixtures/large-doc.md` (the
  distributed systems primer) so the queries are groundable inside
  the container.
- Gateway-side tool discovery (138 deferred tools) currently eats
  turns; capability masking in a future sprint will shrink that
  surface and raise trigger rates further.
