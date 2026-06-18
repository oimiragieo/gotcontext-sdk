# gotcontext

Python SDK for the [gotcontext.ai](https://gotcontext.ai) semantic compression API.

Reduce LLM token usage by compressing text and code before sending it to language models.

## Installation

```bash
pip install gotcontext
```

## Quick start

```python
from gotcontext import GotContext

gc = GotContext(api_key="gc_live_...")

# Compress text
result = gc.compress("Your long document text here...", fidelity="balanced")
print(result.compressed)
print(f"Saved {result.tokens_saved} tokens ({result.savings_pct}%)")
```

## Text compression

```python
result = gc.compress(
    "Your long text here...",
    fidelity="balanced",       # abstract | outline | balanced | detailed | raw
    query="key findings",      # optional: prioritise sections relevant to query
    cost_model="claude-sonnet-4-6",  # optional: estimate cost savings
)

print(result.compressed)                # compressed text
print(result.stats.original_tokens)     # original token count
print(result.stats.compressed_tokens)   # compressed token count
print(result.stats.savings_pct)         # percentage saved
print(result.stats.compression_ratio)   # compression ratio
```

## Code compression

```python
result = gc.compress_code(
    code="def hello():\n    print('Hello, world!')\n",
    language="python",   # optional: auto-detected when omitted
    fidelity="balanced",
)

print(result.compressed)
print(result.stats.language_detected)
```

## Batch compression

Compress up to 50 documents in a single call:

```python
result = gc.batch_compress([
    {"text": "First document...", "fidelity": "balanced"},
    {"text": "Second document...", "fidelity": "outline", "query": "key metrics"},
    {"text": "Third document...", "fidelity": "abstract"},
])

for item in result.results:
    if item.error:
        print(f"Failed: {item.error}")
    else:
        print(f"Saved {item.savings_pct}%")

print(f"Total saved: {result.summary.total_tokens_saved} tokens")
```

## Usage stats

```python
usage = gc.get_usage()
print(f"{usage.compressions_used}/{usage.compressions_limit} compressions used")
print(f"{usage.tokens_saved:,} tokens saved this month")
```

## Compression history

```python
events = gc.get_usage_events(page=1, page_size=10)
for event in events.events:
    print(f"{event.created_at}: {event.tokens_saved} tokens saved ({event.fidelity})")
```

## Passing model attribution (MCP)

When calling the gotcontext MCP gateway via the official
[MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk),
pass your caller model name in `_meta.model` so the billing dashboard
can attribute per-model cost savings. The `meta_for_call` helper builds
that payload for you:

```python
from gotcontext.mcp_helpers import meta_for_call

result = await session.call_tool(
    "ingest_context",
    {"text": doc, "file_id": "doc-1"},
    meta=meta_for_call(model="claude-opus-4.6"),
)
```

When `model` is unknown to the server, it falls back to the resolver
chain (`api_key.default_model` -> plan heuristic). See
[`docs/model-attribution.md`](https://gotcontext.ai/docs)
for the full resolution chain.

## Anthropic prompt cache (cache_breakpoints)

The `/v1/compress` response includes a `cache_breakpoints` array describing
where Anthropic's prompt cache should be anchored. The `apply_anthropic_breakpoints`
helper stamps the right `cache_control` marker on the Anthropic messages
payload for you -- zero dependencies, non-mutating:

```python
from gotcontext import GotContext, apply_anthropic_breakpoints

gc = GotContext(api_key="gc_live_...")
compressed = gc.compress(long_doc, fidelity="balanced")

messages = [
    {"role": "user", "content": [{"type": "text", "text": compressed.compressed}]},
    {"role": "user", "content": [{"type": "text", "text": user_question}]},
]
messages = apply_anthropic_breakpoints(
    messages=messages,
    breakpoints=compressed.cache_breakpoints,
)
# Pass ``messages`` straight into ``anthropic_client.messages.create(...)``.
```

## Async client

```python
import asyncio
from gotcontext import AsyncGotContext

async def main():
    async with AsyncGotContext(api_key="gc_live_...") as gc:
        result = await gc.compress("Your long text here...")
        print(f"Saved {result.tokens_saved} tokens")

asyncio.run(main())
```

## Error handling

```python
from gotcontext import GotContext, AuthError, RateLimitError, ValidationError

gc = GotContext(api_key="gc_live_...")

try:
    result = gc.compress("Hello")
except AuthError:
    print("Invalid API key")
except RateLimitError as e:
    print(f"Rate limited. Retry after {e.retry_after}s")
except ValidationError as e:
    print(f"Invalid request: {e}")
```

All errors include the `request_id` from response headers for support debugging:

```python
except GotContextError as e:
    print(f"Error: {e}")
    print(f"Status: {e.status_code}")
    print(f"Request ID: {e.request_id}")
```

## Configuration

```python
gc = GotContext(
    api_key="gc_live_...",
    base_url="https://api.gotcontext.ai",  # default
    timeout=30.0,                           # request timeout in seconds
    max_retries=3,                          # retries for 429/5xx errors
)
```

The client automatically retries on rate-limit (429) and server errors (5xx) with exponential backoff. The `Retry-After` header is respected when present.

## Context manager

Both clients support context managers for clean resource cleanup:

```python
with GotContext(api_key="gc_live_...") as gc:
    result = gc.compress("text")
# Connection pool closed automatically
```

## Fidelity levels

| Level | Compression | Use case |
|-------|------------|----------|
| `abstract` | ~95% | Maximum compression, key points only |
| `outline` | ~90% | High compression, structure preserved |
| `balanced` | ~85% | Default -- good balance of detail and savings |
| `detailed` | ~60% | Light compression, most detail preserved |
| `raw` | 0% | No compression, pass-through |
