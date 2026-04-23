import { describe, expect, it } from 'vitest';
import { applyAnthropicBreakpoints } from '../cache-helpers.js';

describe('applyAnthropicBreakpoints', () => {
  it('inserts cache_control on the last block of the first message', () => {
    const messages = [
      { role: 'user', content: [{ type: 'text', text: 'STATIC PREFIX' }] },
      { role: 'user', content: [{ type: 'text', text: 'dynamic question' }] },
    ];
    const result = applyAnthropicBreakpoints({
      messages,
      breakpoints: [{ target: 'anthropic', position_tokens: 42, ttl: '5m' }],
    });
    expect(result[0]?.content[0]).toEqual({
      type: 'text',
      text: 'STATIC PREFIX',
      cache_control: { type: 'ephemeral' },
    });
  });

  it('is a no-op when target is not anthropic', () => {
    const messages = [{ role: 'user', content: [{ type: 'text', text: 'x' }] }];
    const result = applyAnthropicBreakpoints({
      messages,
      breakpoints: [{ target: 'openai', position_tokens: 10, ttl: '24h' }],
    });
    expect(result[0]?.content[0]).not.toHaveProperty('cache_control');
  });

  it('adds ttl="1h" when breakpoint ttl is 1h', () => {
    const messages = [{ role: 'user', content: [{ type: 'text', text: 'prefix' }] }];
    const result = applyAnthropicBreakpoints({
      messages,
      breakpoints: [{ target: 'anthropic', position_tokens: 100, ttl: '1h' }],
    });
    expect(result[0]?.content[0]?.cache_control).toEqual({
      type: 'ephemeral',
      ttl: '1h',
    });
  });

  it('omits ttl field when breakpoint ttl is 5m (Anthropic default)', () => {
    const messages = [{ role: 'user', content: [{ type: 'text', text: 'prefix' }] }];
    const result = applyAnthropicBreakpoints({
      messages,
      breakpoints: [{ target: 'anthropic', position_tokens: 100, ttl: '5m' }],
    });
    const block = result[0]?.content[0];
    expect(block?.cache_control).toEqual({ type: 'ephemeral' });
    expect(block?.cache_control).not.toHaveProperty('ttl');
  });

  it("does not mutate the caller's messages array", () => {
    const messages = [{ role: 'user', content: [{ type: 'text', text: 'prefix' }] }];
    const snapshot = JSON.parse(JSON.stringify(messages));
    applyAnthropicBreakpoints({
      messages,
      breakpoints: [{ target: 'anthropic', position_tokens: 42, ttl: '5m' }],
    });
    expect(messages).toEqual(snapshot);
  });

  it('returns messages unchanged when breakpoints array is empty', () => {
    const messages = [{ role: 'user', content: [{ type: 'text', text: 'hi' }] }];
    const result = applyAnthropicBreakpoints({ messages, breakpoints: [] });
    expect(result[0]?.content[0]).not.toHaveProperty('cache_control');
  });

  it('returns [] when messages is empty', () => {
    const result = applyAnthropicBreakpoints({
      messages: [],
      breakpoints: [{ target: 'anthropic', position_tokens: 42, ttl: '5m' }],
    });
    expect(result).toEqual([]);
  });

  it('uses the last anthropic breakpoint when multiple are present', () => {
    const messages = [{ role: 'user', content: [{ type: 'text', text: 'prefix' }] }];
    const result = applyAnthropicBreakpoints({
      messages,
      breakpoints: [
        { target: 'openai', position_tokens: 10, ttl: '24h' },
        { target: 'anthropic', position_tokens: 42, ttl: '1h' },
      ],
    });
    expect(result[0]?.content[0]?.cache_control).toEqual({
      type: 'ephemeral',
      ttl: '1h',
    });
  });
});
