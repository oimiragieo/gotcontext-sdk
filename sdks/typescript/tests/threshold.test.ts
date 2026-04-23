/**
 * v1.4.0 F4 — `/v1/settings/semantic-cache-threshold` SDK helpers.
 *
 * Unit tests use a mocked `fetch` so the suite stays fully offline.
 */
import type { Mock } from 'vitest';
import { describe, expect, it, vi } from 'vitest';

import { GotContext } from '../src/client.js';

function makeMockFetch(body: unknown, status = 200): Mock {
  return vi.fn(async () =>
    new Response(JSON.stringify(body), {
      status,
      headers: { 'Content-Type': 'application/json' },
    }),
  );
}

function makeClient(mockFetch: Mock) {
  return new GotContext({
    apiKey: 'gc_test_key',
    baseUrl: 'https://api.example.com',
    maxRetries: 0,
    fetchFn: mockFetch as unknown as typeof fetch,
  });
}

describe('getSemanticCacheThreshold', () => {
  it('returns the server body unchanged', async () => {
    const mockFetch = makeMockFetch({ threshold: 0.95, source: 'global' });
    const gc = makeClient(mockFetch);
    const out = await gc.getSemanticCacheThreshold();
    expect(out).toEqual({ threshold: 0.95, source: 'global' });
    expect(mockFetch).toHaveBeenCalledOnce();
    const call = mockFetch.mock.calls[0] as [string, RequestInit];
    expect(call[0]).toBe('https://api.example.com/v1/settings/semantic-cache-threshold');
    expect(call[1].method).toBe('GET');
    const headers = call[1].headers as Record<string, string>;
    expect(headers.Authorization).toBe('Bearer gc_test_key');
  });
});

describe('setSemanticCacheThreshold', () => {
  it('PUTs the value and returns the echoed body', async () => {
    const mockFetch = makeMockFetch({ threshold: 0.92, source: 'user' });
    const gc = makeClient(mockFetch);
    const out = await gc.setSemanticCacheThreshold(0.92);
    expect(out).toEqual({ threshold: 0.92, source: 'user' });
    const call = mockFetch.mock.calls[0] as [string, RequestInit];
    expect(call[1].method).toBe('PUT');
    expect(call[1].body).toBe(JSON.stringify({ threshold: 0.92 }));
  });

  it('accepts null to reset to the server default', async () => {
    const mockFetch = makeMockFetch({ threshold: 0.95, source: 'global' });
    const gc = makeClient(mockFetch);
    const out = await gc.setSemanticCacheThreshold(null);
    expect(out.source).toBe('global');
    const call = mockFetch.mock.calls[0] as [string, RequestInit];
    expect(call[1].body).toBe(JSON.stringify({ threshold: null }));
  });
});
