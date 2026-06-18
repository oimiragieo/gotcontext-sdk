# @gotcontext/sdk

Official TypeScript SDK for [gotcontext.ai](https://gotcontext.ai) — the
semantic compression REST API that cuts LLM token usage via graph-based
PageRank compression.

## Install

```bash
npm install @gotcontext/sdk
```

Zero runtime dependencies. Uses the native `fetch` API. Works in Node.js 18+,
Bun, Deno, Cloudflare Workers, and modern browsers.

## Quickstart

```ts
import { GotContext } from '@gotcontext/sdk';

const gc = new GotContext({ apiKey: process.env.GOTCONTEXT_API_KEY! });

const result = await gc.compress({
  text: '…your long document…',
  fidelity: 'balanced',
});

console.log(result.compressed_text);
console.log(`Saved ${result.stats.tokens_saved} tokens`);
```

## API

### `new GotContext(options)`

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `apiKey` | `string` | — | **Required.** `gc_…` API key. |
| `baseUrl` | `string` | `https://api.gotcontext.ai` | Override for self-hosted. |
| `maxRetries` | `number` | `2` | Retries on 5xx. Exponential backoff. |
| `timeoutMs` | `number` | `30000` | Per-request timeout. |
| `fetchFn` | `typeof fetch` | `globalThis.fetch` | Inject a custom fetch (tests, Undici, etc.). |

### Methods

- **`compress(body)`** — `POST /v1/compress`
- **`compressCode(body)`** — `POST /v1/compress-code` (AST-aware)
- **`batchCompress(documents)`** — `POST /v1/batch-compress` (up to 50)
- **`usage()`** — `GET /v1/usage`

Every method returns a `Promise<T>` where `T` is the fully typed response shape.

### Fidelity presets

```ts
type Fidelity = 'abstract' | 'outline' | 'balanced' | 'detailed' | 'raw';
```

### Passing model attribution (MCP)

When calling the gotcontext MCP gateway via
[`@modelcontextprotocol/sdk`](https://github.com/modelcontextprotocol/typescript-sdk),
pass your caller model name in `_meta.model` so the billing dashboard
attributes per-model cost savings. The `metaForCall` helper builds that
payload for you and filters out `undefined` / `null` fields:

```ts
import { metaForCall } from '@gotcontext/sdk';

await session.callTool({
  name: 'ingest_context',
  arguments: { text: doc, file_id: 'doc-1' },
  _meta: metaForCall({ model: 'claude-opus-4.6' }),
});
```

When the server does not recognize `model`, it falls back to the resolver
chain (`api_key.default_model` -> plan heuristic). See
[`docs/model-attribution.md`](https://gotcontext.ai/docs).

### Anthropic prompt cache (cache_breakpoints)

The `/v1/compress` response includes a `cache_breakpoints` array describing
where Anthropic's prompt cache should be anchored. The
`applyAnthropicBreakpoints` helper stamps the right `cache_control` marker
on the Anthropic messages payload — zero dependencies, non-mutating:

```ts
import { GotContext, applyAnthropicBreakpoints } from '@gotcontext/sdk';

const gc = new GotContext({ apiKey: process.env.GOTCONTEXT_API_KEY! });
const compressed = await gc.compress({ text: longDoc, fidelity: 'balanced' });

const messages = applyAnthropicBreakpoints({
  messages: [
    { role: 'user', content: [{ type: 'text', text: compressed.compressed_text }] },
    { role: 'user', content: [{ type: 'text', text: userQuestion }] },
  ],
  breakpoints: compressed.cache_breakpoints,
});

await anthropic.messages.create({ model: 'claude-opus-4-5', messages, /* ... */ });
```

Only breakpoints with `target === 'anthropic'` are honored in v1.1.

### Error handling

All non-2xx responses throw `ApiError`:

```ts
import { ApiError } from '@gotcontext/sdk';

try {
  await gc.compress({ text: '…' });
} catch (err) {
  if (err instanceof ApiError) {
    if (err.isAuth) console.error('Bad API key');
    else if (err.isRateLimited) console.error('Rate limited');
    else if (err.isValidation) console.error('Bad request:', err.detail);
    else console.error(`HTTP ${err.status}: ${err.message}`);
  }
}
```

## Docs

- Full API reference: <https://gotcontext.ai/docs>
- Machine-readable Markdown: <https://gotcontext.ai/docs.md>
- OpenAPI schema: <https://api.gotcontext.ai/api/openapi.json>

## License

MIT © gotcontext.ai
