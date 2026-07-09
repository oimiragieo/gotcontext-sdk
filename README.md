# gotcontext-sdk

Public SDKs, the Claude Code plugin, and reproducible benchmarks for [gotcontext.ai](https://gotcontext.ai) — the AI context compression platform that shrinks your LLM input tokens by **~35%** across Claude, GPT, and Gemini.

> **Main product:** [gotcontext.ai](https://gotcontext.ai) · **Docs:** [gotcontext.ai/docs](https://gotcontext.ai/docs) · **Live data:** [gotcontext.ai/savings-by-model](https://gotcontext.ai/savings-by-model)

This repo ships the four things customers install or run locally. The platform itself (API, dashboard, compressor internals) lives in a separate private repo.

**Also on the platform (Pro):** AI-native **security scanning** over the same MCP endpoint — `gc_scan` runs 128 AST security rules over an uploaded code bundle (findings by rule / severity / file / line), and `gc_skill_scan` inspects a `SKILL.md` or MCP tool-manifest for AI-native threats (tool-poisoning, prompt-injection, least-privilege, excessive-agency) and returns a `safe_to_install` verdict. Scan a skill or MCP server *before* your agent trusts it. Both are Pro-tier and live under the `?profile=full` endpoint (see quickstart).

## What's in here

| Path | What |
|------|------|
| [`plugins/gotcontext/`](./plugins/gotcontext/) | Claude Code plugin — outcome-shaped skills pre-wired to the MCP server. Install with `/plugin marketplace add oimiragieo/gotcontext-sdk` then `/plugin install gotcontext`. |
| [`sdks/python/`](./sdks/python/) | Python SDK. `pip install gotcontext`. |
| [`sdks/typescript/`](./sdks/typescript/) | TypeScript / Node SDK source. |
| [`sdks/vscode-extension/`](./sdks/vscode-extension/) | VS Code extension source for one-click gotcontext MCP setup. |
| [`benchmarks/real_llm_cross_provider_smoke.py`](./benchmarks/real_llm_cross_provider_smoke.py) | Reproduces the "35% billed savings" headline on [`/savings-by-model`](https://gotcontext.ai/savings-by-model). Hits live Anthropic / OpenAI / Google APIs with compressed + uncompressed prompts and reads back the `input_tokens` each provider bills. Requires your own provider keys. |
| [`benchmarks/per_model_savings_smoke.py`](./benchmarks/per_model_savings_smoke.py) | Drives `compress_meta_tokens` once per registered model and cross-checks against `/v1/usage/by-model`. |

## 30-second quickstart

1. Get a free API key at [gotcontext.ai/sign-up](https://gotcontext.ai/sign-up) (1,000 compressions/month free, no card required).
2. Add one block to your AI tool's MCP config:

```json
{
  "mcpServers": {
    "gotcontext": {
      "type": "http",
      "url": "https://api.gotcontext.ai/mcp?profile=core",
      "headers": { "Authorization": "Bearer gc_your_key" }
    }
  }
}
```

The `core` profile exposes the seven lightweight compression tools for lower tool-list overhead. Use `https://api.gotcontext.ai/mcp?profile=full` when you need the full catalogue or platform tools such as `gc_pre_flight` (Pro+), the code-navigation suite (`gc_blast_radius`, `gc_callers`, …), and the security scanners (`gc_scan`, `gc_skill_scan`).

3. From Claude Code / Cursor / Windsurf, call the tools naturally:

```
> ingest_context(file_id="api.md", text="...")
> read_skeleton(file_id="api.md", ratio=0.15)
```

Full tool catalogue: [gotcontext.ai/docs](https://gotcontext.ai/docs).

## Reproduce our numbers

The headline claim on [`/savings-by-model`](https://gotcontext.ai/savings-by-model) — "up to 38% off your flagship LLM bill, measured on Opus 4.7 / GPT-5.4 / Gemini 3.1 Pro" — is reproducible:

```bash
git clone https://github.com/oimiragieo/gotcontext-sdk
cd gotcontext-sdk

# Set your API keys (all four required)
export GC_API_KEY=gc_...
export ANTHROPIC_API_KEY=sk-ant-...
export OPENAI_API_KEY=sk-...
export GEMINI_API_KEY=...

python benchmarks/real_llm_cross_provider_smoke.py
```

Output (2026-04-23 run):

```
Step 1 -- compress via gotcontext MCP...
  gotcontext: 279 -> 168 tokens (39.8% reduction)

Step 2 -- sending to each provider...
  anthropic    claude-opus-4-7             992      612     38.3%
  openai       gpt-5.4                     515      333     35.3%
  google       gemini-3.1-pro-preview      566      370     34.6%

VERDICT: all three providers successfully billed compressed input.
```

## License

MIT on all code in this repo unless a subdirectory's `LICENSE` says otherwise. See the individual `LICENSE` files under `plugins/gotcontext/`, `sdks/python/`, and `sdks/typescript/`.

## Support

- Docs: [gotcontext.ai/docs](https://gotcontext.ai/docs)
- Status: [gotcontext.ai/status](https://gotcontext.ai/status)
- Email: [support@gotcontext.ai](mailto:support@gotcontext.ai)
- Discord: [discord.gg/gotcontext](https://discord.gg/gotcontext)

Issues here are welcome for the SDKs, plugin, and benchmarks. For platform / API issues, use email or Discord.
