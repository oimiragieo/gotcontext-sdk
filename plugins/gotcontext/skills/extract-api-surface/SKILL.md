---
name: extract-api-surface
description: Extracts the public API of a codebase — class names, function signatures, exported types, module docstrings — without loading every file. Use this skill whenever the user asks to understand, explore, navigate, or describe a codebase, library, repository, or package at the overview level. Trigger phrases include "help me understand this codebase", "what does this library do", "what's the API of X", "how is this project structured", "give me an overview of Y", "explain this repo". Calls gotcontext's AST-aware skeleton extraction so you read the shape of the code, not the implementation bodies.
version: 1.1.0
---

# extract-api-surface

## When this skill is the preferred path

The user wants to get oriented in a codebase quickly — they need to
know what's there, not how each function is implemented. Reading every
file just to answer "what does this library do" wastes context and
misses the forest for the trees.

## How to use it

1. Identify the target: a local directory (`./src`), a repo root, or a
   GitHub URL the user linked to.
2. Call `read_skeleton` (free-tier MCP tool) on the target path. You'll
   get function/class signatures, type definitions, module-level
   docstrings, and import maps — bodies stripped. For cross-file
   understanding across a larger tree, `compress_codebase` (Pro+)
   returns the same AST-aware digest for every file in the corpus at
   once.
3. If the skeleton is still too large (rare, large monorepos), pipe it
   through `ingest_context` at `fidelity=balanced`.
4. Present a structured overview:
   - Top-level exports grouped by module
   - Key types / interfaces
   - Entry points (CLI, main, server)
   - One-sentence purpose per module
   - Total signature count (so the user knows the coverage)

## When the raw read is actually fine

- You're actively editing a specific file — you need the body.
- You're debugging a specific function — skeleton hides it.
- Configs, data fixtures, generated code — skeleton isn't meaningful;
  either skip or run `ingest_context` on them.

## Language support

AST-native: Python, JavaScript, TypeScript. Line-based fallback: Java,
Go, Rust, C++. Other languages fall back to regex slicing — surface
that caveat to the user if you hit a non-native language.

See `references/overview-template.md` for the reporting format.
