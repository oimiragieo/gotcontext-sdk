---
name: batch-compress
description: Bulk compression of a file corpus — up to 50 documents per call — for later queries rather than one-off reads. Use this skill whenever the user wants to pre-process a directory, a support-ticket dump, meeting notes, or any sizable corpus before Q&A. Trigger phrases include "compress all these files", "pre-process this corpus", "shrink everything in /path", "bulk-compress for Q&A", or when onboarding Claude to a large project that needs a lot of ingested context. Submits an async job to gotcontext's batch queue and returns a job id; the job processes in the background with per-item error reporting so one bad file doesn't block the batch. Pro, Team, or Enterprise plan required.
version: 1.1.0
---

# batch-compress

## When this skill is the preferred path

For corpus-scale pre-processing, batching amortizes network round-trips
and returns one aggregate savings report. A loop of `ingest_context`
calls is the slow and expensive path for the same work.

## How to use it

1. Enumerate the files. Respect `.gitignore`. Skip binaries, generated
   files, lockfiles, `node_modules`, `vendor`, `dist`, `build`.
2. Group into batches of up to 50 documents (the API cap). Larger
   corpora need multiple calls.
3. Call `batch_ingest_documents` (MCP tool; Pro+). Returns a
   `job_id` immediately.
4. Poll job status via `GET /v1/batch-queue/{id}` (REST) or subscribe
   to `GET /v1/batch-queue/stream` for SSE updates.
5. When complete, retrieve each compressed item by its item id.
6. Report to the user:
   - Total files processed
   - Aggregate tokens saved
   - Any failures (rate limit, invalid input, permissions) — the API
     returns per-item errors so failures don't block the batch

## When the raw read or a simpler skill fits better

- Single file or a small set (<3 files) — `shrink-for-claude`.
- Files the user is actively editing — stale snapshots will confuse.

## Plan gating

`batch_ingest_documents` returns HTTP 403 on Free with an upgrade
link. Surface that response faithfully — don't paper over it with a
fallback loop. The user wanted batch throughput; they should see the
upgrade path instead of a silent slow fallback.

## Warn before starting

If the batch will have >200 items, confirm before enqueuing.
Processing time scales linearly and the user may have wanted a smaller
slice.
