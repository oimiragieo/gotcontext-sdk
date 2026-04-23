/**
 * Helpers for passing model attribution on MCP `tools/call` requests.
 *
 * gotcontext.ai reads `_meta.model` per call and stamps it on every
 * UsageEvent so the billing dashboard shows per-model cost savings.
 * When the model name is unknown to the server, it falls back to the
 * resolver chain (api_key.default_model -> plan heuristic).
 *
 * @example
 * ```ts
 * import { metaForCall } from '@gotcontext/sdk';
 *
 * await session.callTool({
 *   name: 'ingest_context',
 *   arguments: { text: doc, file_id: 'doc-1' },
 *   _meta: metaForCall({ model: 'claude-opus-4.6' }),
 * });
 * ```
 *
 * See docs/model-attribution.md for the full resolution chain.
 */
export type ToolMeta = { model?: string } & Record<string, unknown>;

/**
 * Build a `_meta` payload for an MCP `tools/call` request.
 *
 * `null` and `undefined` values are filtered out so callers can pass
 * optional fields through without producing noisy `null` entries.
 * Returns an empty object when nothing is provided.
 */
export function metaForCall(
  opts: { model?: string } & Record<string, unknown> = {},
): ToolMeta {
  const out: ToolMeta = {};
  for (const [k, v] of Object.entries(opts)) {
    if (v !== undefined && v !== null) {
      out[k] = v;
    }
  }
  return out;
}
