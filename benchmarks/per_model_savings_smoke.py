"""Per-model compression savings smoke — drives ``compress_meta_tokens``
against the production MCP gateway once per ``_meta.model`` value, then
queries ``GET /v1/usage/by-model`` to confirm the server-side rollup
matches our local measurements.

Usage:
    GC_API_KEY=gc_... python benchmarks/per_model_savings_smoke.py
"""

from __future__ import annotations

import json
import os
import sys
import time

import httpx

MCP = "https://api.gotcontext.ai/mcp"
USAGE = "https://api.gotcontext.ai/v1/usage/by-model"
MODELS_URL = "https://api.gotcontext.ai/v1/models"
API_KEY = os.environ["GC_API_KEY"]

# Fixed corpus — same text for every model so the only thing that
# changes is the tokenizer and per-1k price. ~500 words of realistic
# technical prose with embedded repetition so compression has something
# to work with.
CORPUS = (
    "The FastAPI application initializes Sentry in _init_sentry(), wires Clerk "
    "authentication in AuthMiddleware, and exposes a Streamable HTTP MCP gateway "
    "at /mcp. On lifespan startup, assert_env_sanity() validates POLAR_ACCESS_TOKEN "
    "and POLAR_SERVER for config drift. The release_command runs alembic upgrade head. "
    "Circuit breakers in api/app/services/resilience.py guard Redis, Postgres, and "
    "Polar. When a breaker opens, DegradationHeaderMiddleware adds X-Degraded. "
    "The MCP gateway is at /mcp and validates gc_ API keys via verify_api_key. "
    "Plan gating lives in api/app/services/plan_gating.py — is_tool_allowed filters "
    "tools/list per plan. The Claude Code plugin at plugins/gotcontext/ ships five "
    "outcome-shaped skills pre-wired to this MCP server. "
) * 3


def _headers(session_id: str | None = None, accept_gzip: bool = False) -> dict[str, str]:
    h = {
        "Authorization": f"Bearer {API_KEY}",
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


def _init_session(model: str) -> str:
    resp = httpx.post(
        MCP,
        headers=_headers(),
        json={
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2025-03-26",
                "capabilities": {},
                "clientInfo": {"name": f"bench-{model}", "version": "1.0"},
            },
        },
        timeout=30,
    )
    resp.raise_for_status()
    sid = resp.headers.get("mcp-session-id", "")
    httpx.post(
        MCP,
        headers=_headers(sid),
        json={"jsonrpc": "2.0", "method": "notifications/initialized"},
        timeout=15,
    )
    return sid


def _compress_for_model(model: str) -> tuple[int, int]:
    """One compress_meta_tokens call with ``_meta.model`` set. Returns (tokens_in, tokens_out)."""
    sid = _init_session(model)
    resp = httpx.post(
        MCP,
        headers=_headers(sid),
        json={
            "jsonrpc": "2.0",
            "id": 10,
            "method": "tools/call",
            "params": {
                "name": "compress_meta_tokens",
                "arguments": {"text": CORPUS},
                # _meta.model is the attribution signal the gateway reads
                "_meta": {"model": model},
            },
        },
        timeout=60,
    )
    resp.raise_for_status()
    body = _parse_response(resp.text).get("result", {})
    if body.get("isError"):
        first = (body.get("content") or [{}])[0]
        print(f"  ERROR: {first.get('text', '?')[:160]}")
        return (0, 0)
    content = body.get("content") or []
    if content and content[0].get("type") == "text":
        try:
            parsed = json.loads(content[0]["text"])
            return (int(parsed.get("original_tokens", 0)), int(parsed.get("compressed_tokens", 0)))
        except (json.JSONDecodeError, ValueError):
            return (0, 0)
    return (0, 0)


def main() -> int:
    print(f"per-model compression smoke against {MCP}")
    print(f"key tail: ...{API_KEY[-8:]}")
    print(f"corpus: {len(CORPUS)} chars (~{len(CORPUS.split())} words)")
    print("-" * 76)

    resp = httpx.get(MODELS_URL, timeout=10)
    resp.raise_for_status()
    models = [m["model"] for m in resp.json()["models"]]
    print(f"registered models ({len(models)}): {', '.join(models)}")
    print("-" * 76)

    # 3 calls per model so the aggregate rollup has enough rows to see
    local: dict[str, dict] = {}
    for model in models:
        tins, touts = 0, 0
        for i in range(3):
            tin, tout = _compress_for_model(model)
            tins += tin
            touts += tout
            time.sleep(0.3)
        saved = max(0, tins - touts)
        pct = round(saved / tins * 100, 1) if tins else 0.0
        local[model] = {"in": tins, "out": touts, "saved": saved, "pct": pct}
        print(
            f"  {model:30s} in={tins:6d}  out={touts:6d}  "
            f"saved={saved:6d}  pct={pct:5.1f}%"
        )

    print("-" * 76)
    print("waiting 3s for usage_events to flush...")
    time.sleep(3)

    # Server rollup
    resp = httpx.get(
        f"{USAGE}?days=1",
        headers={"Authorization": f"Bearer {API_KEY}"},
        timeout=15,
    )
    print(f"\nGET {USAGE}?days=1  status={resp.status_code}")
    server = resp.json()
    print(json.dumps(server, indent=2))

    print("-" * 76)
    print("cross-check (local vs server):")
    server_by_model = {it.get("model"): it for it in server.get("items", [])}
    for model, row in local.items():
        srv = server_by_model.get(model)
        if srv is None:
            print(f"  [MISS] {model}: not present in server rollup")
            continue
        # Compare counts (±1 for rounding)
        match = abs(srv.get("tokens_in", 0) - row["in"]) <= 3
        marker = "ok  " if match else "warn"
        print(
            f"  [{marker}] {model}: local_in={row['in']} srv_in={srv.get('tokens_in')} "
            f"srv_saved={srv.get('tokens_saved')} srv_cost=${srv.get('cost_saved_usd', '?')}"
        )

    return 0


if __name__ == "__main__":
    sys.exit(main())
