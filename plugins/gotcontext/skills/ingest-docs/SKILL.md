---
name: ingest-docs
description: Query-guided compression of a documentation site, docs folder, README, wiki, or specification for Q&A. Use this skill whenever the user points you at multi-page reference material and wants to find something in it. Trigger phrases include "help me find X in these docs", "what does the Y docs say about Z", "search the Stripe/AWS/Anthropic docs for", "summarize this reference", "check the docs for". Passes the user's question as a query parameter so gotcontext weights relevant sections heavier and compresses off-topic sections more aggressively — keeps answers grounded without loading every page.
version: 1.0.0
---

# ingest-docs

## When this skill is the preferred path

A docs tree is the perfect target for query-guided compression:
sprawling, repetitive, and mostly irrelevant to any single question.
Loading the full tree exhausts context; loading one page misses
cross-references. Query-guided compression solves both by keeping
what's relevant to the user's question and shrinking what isn't.

## How to use it

1. Identify the source — local path (`./docs`), a docs URL, or a list
   of URLs. Ask the user if it's unclear.
2. Identify the question. If the user hasn't asked a specific
   question yet, ask before ingesting — query-guided mode needs a
   query. If they want a general overview, use `fidelity=balanced`
   without a query.
3. Call gotcontext's `ingest_context` MCP tool with:
   - `source` — path or URL(s)
   - `query` — the user's question (enables relevance-weighted
     compression; highly recommended)
   - `fidelity=balanced` — good Q&A accuracy, ~50% savings
4. Read the compressed blob. The response includes a one-line header
   with source, page count, and compression ratio.
5. Answer the user, citing sections/pages from the compressed output
   so they can verify.

## When the raw read is actually fine

- Single short README — just `Read` it.
- You're writing or editing documentation — you need the raw markdown.

## Good candidates for this skill

- Sphinx / MkDocs / Docusaurus trees
- GitBook, Notion, or Confluence exports
- Swagger / OpenAPI HTML renderings
- Any `/docs` directory in a repo
- Man page archives

## Cache behavior

Within one session, cache the compressed result of a tree after the
first call and query against the cached blob for follow-ups. Each
re-ingestion is a paid compression call — don't waste the user's
credits on the same tree twice.
