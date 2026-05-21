---
name: compress-mcp-manifest
description: >
  Compress an MCP tools/list manifest so downstream agents see shorter tool
  descriptions without losing inputSchema semantics. Use before forwarding
  a large tools/list to a secondary agent or storing it in context.
version: 1.0.0
---

# compress-mcp-manifest

## When to use this skill

Use this skill when you have retrieved a `tools/list` response from an MCP
server and want to reduce the token cost of forwarding it to another agent,
storing it in memory, or including it in a prompt.

This is especially useful when orchestrating multi-agent pipelines where each
sub-agent needs to know what tools are available but does not need the full
verbose description of every parameter.

## How to use it

1. Retrieve the `tools/list` response from the target MCP server.
2. Call `gc_compress_manifest` with the manifest as input:
   ```json
   {
     "manifest": {
       "tools": [{ "name": "...", "description": "...", "inputSchema": {} }]
     }
   }
   ```
3. The tool returns the manifest with compressed description fields and
   a stats block: `{"input_tokens": N, "output_tokens": M, "savings_pct": P}`.
4. Forward the compressed manifest to your downstream agent or store it in
   context using the token-saving path.

## What is guaranteed

- `inputSchema` is preserved **byte-for-byte** (JSON-equivalent). Schema
  validation in downstream agents will not break.
- Tool names are never modified.
- Only tool description text is compressed; schemas are untouched.

## Plan requirement

`gc_compress_manifest` is available on **Pro and above**. Free users will
receive an upgrade prompt.

## Why gotcontext over mcp-compressor

Atlassian's `mcp-compressor` compresses tool schemas. gotcontext compresses
tool **descriptions** while preserving schemas, and also provides full payload
compression, OAuth 2.1 auth, usage telemetry, and self-hosted licensing —
a superset of what `mcp-compressor` offers.
