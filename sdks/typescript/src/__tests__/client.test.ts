import { beforeEach, describe, expect, it, vi } from 'vitest';
import { ApiError, GotContext, VERSION } from '../index.js';

const mockFetch = vi.fn();

beforeEach(() => {
  mockFetch.mockReset();
});

function jsonResponse(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { 'content-type': 'application/json' },
  });
}

describe('GotContext', () => {
  it('throws without an API key', () => {
    expect(() => new GotContext({ apiKey: '' })).toThrow(/apiKey/i);
  });

  it('exposes the SDK version constant', () => {
    expect(VERSION).toBe('0.5.2');
  });

  it('compresses text and sends Bearer auth + UA header', async () => {
    // v1.5.2 — server returns `compressed` (not `compressed_text`).
    // The SDK deserialises to both fields for the one-minor
    // deprecation window; the test asserts the new correct field.
    mockFetch.mockResolvedValueOnce(
      jsonResponse({
        compressed: 'short',
        fidelity: 'balanced',
        stats: {
          original_tokens: 100,
          compressed_tokens: 20,
          compression_ratio: 0.2,
          tokens_saved: 80,
        },
      }),
    );

    const gc = new GotContext({ apiKey: 'gc_test', fetchFn: mockFetch });
    const out = await gc.compress({ text: '…long…', fidelity: 'balanced' });

    expect(out.compressed).toBe('short');
    expect(out.stats.tokens_saved).toBe(80);

    const [url, init] = mockFetch.mock.calls[0] as [string, RequestInit];
    expect(url).toBe('https://api.gotcontext.ai/v1/compress');
    expect(init.method).toBe('POST');
    const headers = init.headers as Record<string, string>;
    expect(headers.Authorization).toBe('Bearer gc_test');
    expect(headers['User-Agent']).toContain('@gotcontext/sdk/');
  });

  it('compresses code with language hint', async () => {
    // v1.5.2 — server returns `compressed` on /v1/compress-code.
    mockFetch.mockResolvedValueOnce(
      jsonResponse({
        compressed: 'def f(): ...',
        language: 'python',
        fidelity: 'balanced',
        stats: {
          original_tokens: 50,
          compressed_tokens: 10,
          compression_ratio: 0.2,
          tokens_saved: 40,
        },
      }),
    );

    const gc = new GotContext({ apiKey: 'gc_test', fetchFn: mockFetch });
    const out = await gc.compressCode({ code: 'def f():\n  pass', language: 'python' });

    expect(out.language).toBe('python');
    expect(mockFetch.mock.calls[0]?.[0]).toBe('https://api.gotcontext.ai/v1/compress-code');
  });

  it('batch-compresses a list of documents', async () => {
    // v1.5.2 — server returns `compressed` on each batch item.
    mockFetch.mockResolvedValueOnce(
      jsonResponse({
        items: [{ id: 'a', compressed: 'x' }, { id: 'b', compressed: 'y' }],
        summary: { total: 2, succeeded: 2, failed: 0, total_tokens_saved: 42 },
      }),
    );

    const gc = new GotContext({ apiKey: 'gc_test', fetchFn: mockFetch });
    const out = await gc.batchCompress([
      { id: 'a', text: 'doc-a' },
      { id: 'b', text: 'doc-b' },
    ]);

    expect(out.summary.total).toBe(2);
  });

  it('surfaces 4xx as ApiError with status + message', async () => {
    mockFetch.mockResolvedValueOnce(
      jsonResponse({ detail: 'invalid fidelity' }, 422),
    );

    const gc = new GotContext({ apiKey: 'gc_test', fetchFn: mockFetch });
    let caught: unknown = null;
    try {
      await gc.compress({ text: 'x', fidelity: 'bogus' as never });
    } catch (err) {
      caught = err;
    }
    expect(caught).toBeInstanceOf(ApiError);
    const apiErr = caught as ApiError;
    expect(apiErr.status).toBe(422);
    expect(apiErr.message).toContain('invalid fidelity');
    expect(apiErr.isValidation).toBe(true);
    expect(apiErr.isAuth).toBe(false);
  });

  it('classifies 401 as auth error', async () => {
    mockFetch.mockResolvedValueOnce(jsonResponse({ detail: 'bad key' }, 401));
    const gc = new GotContext({ apiKey: 'gc_test', fetchFn: mockFetch });
    await expect(gc.usage()).rejects.toMatchObject({ status: 401, isAuth: true });
  });

  it('retries twice on 5xx then succeeds on the third attempt', async () => {
    mockFetch
      .mockResolvedValueOnce(new Response('', { status: 503 }))
      .mockResolvedValueOnce(new Response('', { status: 502 }))
      .mockResolvedValueOnce(
        jsonResponse({
          plan: 'pro',
          period_start: '2026-04-01',
          period_end: '2026-04-30',
          compressions_used: 1,
          compressions_limit: 50000,
          tokens_saved: 99,
        }),
      );

    const gc = new GotContext({ apiKey: 'gc_test', maxRetries: 2, fetchFn: mockFetch });
    const out = await gc.usage();
    expect(out.plan).toBe('pro');
    expect(mockFetch).toHaveBeenCalledTimes(3);
  }, 10_000);

  it('retries on 429 with Retry-After and succeeds on the follow-up', async () => {
    // v0.5.2 — 429 is now retried alongside 5xx. Server advertises a
    // 1-second Retry-After; SDK honours it (capped at 30s).
    const retryableResponse = new Response('{"detail":"rate limit"}', {
      status: 429,
      headers: { 'Content-Type': 'application/json', 'Retry-After': '1' },
    });
    mockFetch
      .mockResolvedValueOnce(retryableResponse)
      .mockResolvedValueOnce(
        jsonResponse({
          plan: 'pro',
          period_start: '2026-04-01',
          period_end: '2026-04-30',
          compressions_used: 1,
          compressions_limit: 50000,
          tokens_saved: 99,
        }),
      );

    const gc = new GotContext({ apiKey: 'gc_test', maxRetries: 2, fetchFn: mockFetch });
    const out = await gc.usage();
    expect(out.plan).toBe('pro');
    expect(mockFetch).toHaveBeenCalledTimes(2);
  }, 10_000);

  it('surfaces 429 as ApiError once retries are exhausted', async () => {
    mockFetch
      .mockResolvedValueOnce(new Response('{"detail":"rate limit"}', { status: 429 }))
      .mockResolvedValueOnce(new Response('{"detail":"rate limit"}', { status: 429 }))
      .mockResolvedValueOnce(new Response('{"detail":"rate limit"}', { status: 429 }));

    const gc = new GotContext({ apiKey: 'gc_test', maxRetries: 2, fetchFn: mockFetch });
    await expect(gc.usage()).rejects.toMatchObject({ status: 429 });
    expect(mockFetch).toHaveBeenCalledTimes(3);
  }, 10_000);

  it('allows custom baseUrl for self-hosted deployments', async () => {
    mockFetch.mockResolvedValueOnce(jsonResponse({}));
    const gc = new GotContext({
      apiKey: 'gc_test',
      baseUrl: 'http://localhost:8080',
      fetchFn: mockFetch,
    });
    try {
      await gc.usage();
    } catch {
      // ignore body shape — this test only checks the URL
    }
    expect(mockFetch.mock.calls[0]?.[0]).toBe('http://localhost:8080/v1/usage');
  });

  it('strips trailing slash from baseUrl', async () => {
    mockFetch.mockResolvedValueOnce(jsonResponse({}));
    const gc = new GotContext({
      apiKey: 'gc_test',
      baseUrl: 'http://localhost:8080/',
      fetchFn: mockFetch,
    });
    try {
      await gc.usage();
    } catch {
      // ignore body shape
    }
    expect(mockFetch.mock.calls[0]?.[0]).toBe('http://localhost:8080/v1/usage');
  });
});
