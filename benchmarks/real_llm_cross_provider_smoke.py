"""Real-LLM cross-provider E2E -- sends the same prompt (uncompressed
+ compressed variants) to Claude, Gemini, and GPT, and measures
**actual billed input tokens** each provider reports back.

This is the definitive version of the compression-savings story:
instead of estimating "333 tokens saved" via our semantic tokenizer,
we ask each provider what it actually charged us for the compressed
vs uncompressed input.

Outputs a markdown table summarising per-provider savings.

Usage:
    # requires ANTHROPIC_API_KEY, OPENAI_API_KEY, GEMINI_API_KEY
    # (loaded from .env.local if present, else environment)
    python benchmarks/real_llm_cross_provider_smoke.py
"""

from __future__ import annotations

import json
import os
import sys
import time
from dataclasses import dataclass
from pathlib import Path

import httpx

# ---------------------------------------------------------------------------
# Env bootstrap -- read .env.local if present, fall back to os.environ.
# ---------------------------------------------------------------------------


def _load_env_local() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    env_path = repo_root / ".env.local"
    if not env_path.exists():
        return
    for raw in env_path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


_load_env_local()

ANTHROPIC_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
OPENAI_KEY = os.environ.get("OPENAI_API_KEY", "")
GEMINI_KEY = os.environ.get("GEMINI_API_KEY", "")

MCP_ENDPOINT = os.environ.get("MCP_ENDPOINT", "https://api.gotcontext.ai/mcp")
GC_API_KEY = os.environ.get("GC_API_KEY", "")

# ---------------------------------------------------------------------------
# Corpus -- same 500-word technical prose used on /savings-by-model.
# ---------------------------------------------------------------------------

CORPUS = (
    "The FastAPI application initializes Sentry in _init_sentry(), wires Clerk "
    "authentication in AuthMiddleware, and exposes a Streamable HTTP MCP gateway "
    "at /mcp. On lifespan startup, assert_env_sanity() validates POLAR_ACCESS_TOKEN "
    "and POLAR_SERVER for config drift. The release_command runs alembic upgrade head. "
    "Circuit breakers in api/app/services/resilience.py guard Redis, Postgres, and "
    "Polar. When a breaker opens, DegradationHeaderMiddleware adds X-Degraded. "
    "The MCP gateway is at /mcp and validates gc_ API keys via verify_api_key. "
    "Plan gating lives in api/app/services/plan_gating.py -- is_tool_allowed filters "
    "tools/list per plan. The Claude Code plugin at plugins/gotcontext/ ships five "
    "outcome-shaped skills pre-wired to this MCP server. "
) * 3

INSTRUCTION = (
    "Given the following technical documentation, extract the three most important "
    "concepts as bullet points. Keep the response to under 100 words."
)

# ---------------------------------------------------------------------------
# Step 1 -- compress the corpus via gotcontext MCP.
# ---------------------------------------------------------------------------


def _mcp_headers(session_id: str | None = None) -> dict[str, str]:
    h = {
        "Authorization": f"Bearer {GC_API_KEY}",
        "Content-Type": "application/json",
        "Accept": "application/json, text/event-stream",
    }
    if session_id:
        h["Mcp-Session-Id"] = session_id
    return h


def _parse_response(text: str) -> dict:
    stripped = text.strip()
    if stripped.startswith("{"):
        try:
            return json.loads(stripped)
        except json.JSONDecodeError:
            pass
    for line in text.splitlines():
        if line.startswith("data:"):
            try:
                return json.loads(line[5:].strip())
            except json.JSONDecodeError:
                continue
    return {}


def compress_via_mcp(text: str) -> tuple[str, int, int]:
    """Returns (compressed_text, original_tokens, compressed_tokens)."""
    init = httpx.post(
        MCP_ENDPOINT,
        headers=_mcp_headers(),
        json={
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2025-03-26",
                "capabilities": {},
                "clientInfo": {"name": "real-llm-smoke", "version": "1.0"},
            },
        },
        timeout=30,
    )
    init.raise_for_status()
    sid = init.headers.get("mcp-session-id", "")
    httpx.post(
        MCP_ENDPOINT,
        headers=_mcp_headers(sid),
        json={"jsonrpc": "2.0", "method": "notifications/initialized"},
        timeout=15,
    )
    resp = httpx.post(
        MCP_ENDPOINT,
        headers=_mcp_headers(sid),
        json={
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/call",
            "params": {"name": "compress_meta_tokens", "arguments": {"text": text}},
        },
        timeout=60,
    )
    resp.raise_for_status()
    body = _parse_response(resp.text).get("result", {})
    if body.get("isError"):
        raise RuntimeError(f"compress_meta_tokens error: {body.get('content')}")
    content = body["content"][0]["text"]
    parsed = json.loads(content)
    return (
        parsed["compressed_text"],
        int(parsed["original_tokens"]),
        int(parsed["compressed_tokens"]),
    )


# ---------------------------------------------------------------------------
# Step 2 -- call each provider with uncompressed + compressed prompts,
#           record the input_tokens they report back.
# ---------------------------------------------------------------------------


@dataclass
class ProviderResult:
    provider: str
    model: str
    uncompressed_input_tokens: int
    compressed_input_tokens: int
    uncompressed_output_tokens: int
    compressed_output_tokens: int
    error: str | None = None

    @property
    def savings_pct(self) -> float:
        if not self.uncompressed_input_tokens:
            return 0.0
        saved = self.uncompressed_input_tokens - self.compressed_input_tokens
        return round(saved / self.uncompressed_input_tokens * 100, 1)


def call_anthropic(model: str, prompt: str) -> tuple[int, int]:
    """Returns (input_tokens, output_tokens). Raises on non-200."""
    r = httpx.post(
        "https://api.anthropic.com/v1/messages",
        headers={
            "x-api-key": ANTHROPIC_KEY,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        },
        json={
            "model": model,
            "max_tokens": 300,
            "messages": [{"role": "user", "content": prompt}],
        },
        timeout=60,
    )
    r.raise_for_status()
    body = r.json()
    usage = body.get("usage", {})
    return (int(usage.get("input_tokens", 0)), int(usage.get("output_tokens", 0)))


def call_openai(model: str, prompt: str) -> tuple[int, int]:
    # GPT-5.x reasoning models require ``max_completion_tokens``; older chat
    # models accept ``max_tokens``. Use the new name universally and fall
    # back if a legacy model rejects it.
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "max_completion_tokens": 500,
    }
    r = httpx.post(
        "https://api.openai.com/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {OPENAI_KEY}",
            "Content-Type": "application/json",
        },
        json=payload,
        timeout=90,
    )
    if r.status_code == 400 and "max_completion_tokens" in r.text:
        payload["max_tokens"] = payload.pop("max_completion_tokens")
        r = httpx.post(
            "https://api.openai.com/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {OPENAI_KEY}",
                "Content-Type": "application/json",
            },
            json=payload,
            timeout=90,
        )
    r.raise_for_status()
    body = r.json()
    usage = body.get("usage", {})
    return (int(usage.get("prompt_tokens", 0)), int(usage.get("completion_tokens", 0)))


def call_gemini(model: str, prompt: str) -> tuple[int, int]:
    r = httpx.post(
        f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent",
        params={"key": GEMINI_KEY},
        headers={"Content-Type": "application/json"},
        json={
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"maxOutputTokens": 300},
        },
        timeout=60,
    )
    r.raise_for_status()
    body = r.json()
    usage = body.get("usageMetadata", {})
    return (
        int(usage.get("promptTokenCount", 0)),
        int(usage.get("candidatesTokenCount", 0)),
    )


# ---------------------------------------------------------------------------
# Models to test -- one representative per family.
# ---------------------------------------------------------------------------

PROVIDERS = [
    ("anthropic", "claude-opus-4-7", call_anthropic),       # Anthropic flagship
    ("openai", "gpt-5.4", call_openai),                     # OpenAI flagship
    ("google", "gemini-3.1-pro-preview", call_gemini),      # Google flagship
]


def run_provider(
    name: str,
    model: str,
    fn,
    uncompressed_prompt: str,
    compressed_prompt: str,
) -> ProviderResult:
    print(f"  [{name}] {model}: calling uncompressed...")
    try:
        un_in, un_out = fn(model, uncompressed_prompt)
        time.sleep(0.5)
        print(f"  [{name}] {model}: calling compressed...")
        cp_in, cp_out = fn(model, compressed_prompt)
    except httpx.HTTPStatusError as e:
        return ProviderResult(
            provider=name,
            model=model,
            uncompressed_input_tokens=0,
            compressed_input_tokens=0,
            uncompressed_output_tokens=0,
            compressed_output_tokens=0,
            error=f"HTTP {e.response.status_code}: {e.response.text[:200]}",
        )
    except Exception as e:
        return ProviderResult(
            provider=name,
            model=model,
            uncompressed_input_tokens=0,
            compressed_input_tokens=0,
            uncompressed_output_tokens=0,
            compressed_output_tokens=0,
            error=f"{type(e).__name__}: {e}",
        )
    return ProviderResult(
        provider=name,
        model=model,
        uncompressed_input_tokens=un_in,
        compressed_input_tokens=cp_in,
        uncompressed_output_tokens=un_out,
        compressed_output_tokens=cp_out,
    )


def main() -> int:
    print("Real-LLM cross-provider compression smoke")
    print("=" * 70)

    missing = []
    if not ANTHROPIC_KEY:
        missing.append("ANTHROPIC_API_KEY")
    if not OPENAI_KEY:
        missing.append("OPENAI_API_KEY")
    if not GEMINI_KEY:
        missing.append("GEMINI_API_KEY")
    if missing:
        print(f"MISSING: {', '.join(missing)}")
        return 1

    print(f"Corpus: {len(CORPUS)} chars (~{len(CORPUS.split())} words)")
    print()
    print("Step 1 -- compress via gotcontext MCP...")
    compressed_text, original_toks, compressed_toks = compress_via_mcp(CORPUS)
    gc_ratio = round((1 - compressed_toks / original_toks) * 100, 1)
    print(f"  gotcontext: {original_toks} -> {compressed_toks} tokens ({gc_ratio}% reduction)")
    print()

    uncompressed_prompt = f"{INSTRUCTION}\n\n{CORPUS}"
    compressed_prompt = f"{INSTRUCTION}\n\n{compressed_text}"

    print("Step 2 -- sending to each provider...")
    results: list[ProviderResult] = []
    for name, model, fn in PROVIDERS:
        r = run_provider(name, model, fn, uncompressed_prompt, compressed_prompt)
        results.append(r)
        if r.error:
            print(f"  [{name}] {model}: ERROR -- {r.error}")
        else:
            print(
                f"  [{name}] {model}: un={r.uncompressed_input_tokens} -> "
                f"cp={r.compressed_input_tokens} ({r.savings_pct}% savings)"
            )

    print()
    print("Summary (input tokens billed by each provider)")
    print("-" * 70)
    print(f"{'Provider':<12} {'Model':<22} {'Uncomp':>8} {'Comp':>8} {'Save %':>9}")
    print("-" * 70)
    for r in results:
        if r.error:
            print(f"{r.provider:<12} {r.model:<22}  -- ERROR -- {r.error[:30]}")
            continue
        print(
            f"{r.provider:<12} {r.model:<22} {r.uncompressed_input_tokens:>8} "
            f"{r.compressed_input_tokens:>8} {r.savings_pct:>8}%"
        )
    print("-" * 70)
    print(f"gotcontext compressor reported: {gc_ratio}% reduction")
    print()

    all_ok = all(r.error is None for r in results)
    if all_ok:
        print("VERDICT: all three providers successfully billed compressed input.")
    else:
        print("VERDICT: one or more providers errored -- see above.")
    return 0 if all_ok else 2


if __name__ == "__main__":
    sys.exit(main())
