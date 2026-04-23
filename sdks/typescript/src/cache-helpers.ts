/**
 * Drop-in helpers for piping gotcontext `cache_breakpoints` into the
 * Anthropic SDK `messages.create` payload. Zero dependencies.
 *
 * The gotcontext `/v1/compress` response includes a `cache_breakpoints`
 * array describing where Anthropic's prompt cache should be anchored so
 * the static prefix of a prompt is billed once and reused on subsequent
 * calls. This helper stamps the appropriate `cache_control` marker on
 * the last content block of the cached prefix.
 *
 * @example
 * ```ts
 * import { GotContext, applyAnthropicBreakpoints } from '@gotcontext/sdk';
 *
 * const gc = new GotContext({ apiKey: process.env.GOTCONTEXT_API_KEY! });
 * const compressed = await gc.compress({ text: longDoc, fidelity: 'balanced' });
 *
 * const messages = applyAnthropicBreakpoints({
 *   messages: [
 *     { role: 'user', content: [{ type: 'text', text: compressed.compressed_text }] },
 *     { role: 'user', content: [{ type: 'text', text: userQuestion }] },
 *   ],
 *   breakpoints: compressed.cache_breakpoints,
 * });
 *
 * // Pass ``messages`` straight into the Anthropic SDK.
 * await anthropic.messages.create({ model: 'claude-opus-4-5', messages, ... });
 * ```
 *
 * Only breakpoints with `target === 'anthropic'` are honored. OpenAI /
 * Gemini breakpoints are ignored; this helper is deliberately narrow so
 * it ships with zero SDK surface area in v1.1.
 */

/** A breakpoint entry as returned by `/v1/compress`. */
export type CacheBreakpoint = {
  target: string;
  position_tokens: number;
  ttl: string;
} & Record<string, unknown>;

/** An Anthropic content block (text, image, tool-use, etc.). */
export type AnthropicContentBlock = {
  type: string;
  cache_control?: { type: 'ephemeral'; ttl?: string };
} & Record<string, unknown>;

/** An Anthropic-style message. */
export type AnthropicMessage = {
  role: string;
  content: AnthropicContentBlock[];
} & Record<string, unknown>;

/**
 * Return a new `messages` list with Anthropic `cache_control` stamped on
 * the last content block of the first message.
 *
 * The input is **not** mutated; callers can safely pass the same
 * messages to multiple providers. When no Anthropic breakpoint is
 * present, or when `messages` is empty, the input is returned unchanged.
 *
 * - `ttl === '1h'` adds `"ttl": "1h"` to the `cache_control` dict.
 * - `ttl === '5m'` (Anthropic default) omits the `ttl` key entirely.
 */
export function applyAnthropicBreakpoints(opts: {
  messages: AnthropicMessage[];
  breakpoints: CacheBreakpoint[];
}): AnthropicMessage[] {
  const { messages, breakpoints } = opts;
  const relevant = breakpoints.filter((bp) => bp.target === 'anthropic');
  const lastRelevant = relevant[relevant.length - 1];
  if (!lastRelevant || messages.length === 0) {
    return messages;
  }

  const ttl = lastRelevant.ttl ?? '5m';
  const cacheControl: { type: 'ephemeral'; ttl?: string } = { type: 'ephemeral' };
  if (ttl === '1h') {
    cacheControl.ttl = '1h';
  }

  // Structured clone so the caller's shared state is never mutated.
  const cloned: AnthropicMessage[] =
    typeof structuredClone === 'function'
      ? structuredClone(messages)
      : JSON.parse(JSON.stringify(messages));

  const first = cloned[0];
  if (first && Array.isArray(first.content) && first.content.length > 0) {
    const lastBlock = first.content[first.content.length - 1];
    if (lastBlock) {
      lastBlock.cache_control = cacheControl;
    }
  }
  return cloned;
}
