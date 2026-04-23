/**
 * v1.5.0 — ``compressCodeStructural`` SDK helper.
 *
 * Fully offline: fetch is mocked. Exercises URL, method, body shape,
 * and response parsing.
 */
import type { Mock } from 'vitest';
import { describe, expect, it, vi } from 'vitest';

import { GotContext } from '../src/client.js';
import type { StructuralCompressResponse } from '../src/types.js';

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
    apiKey: 'gc_test',
    baseUrl: 'https://api.example.com',
    maxRetries: 0,
    fetchFn: mockFetch as unknown as typeof fetch,
  });
}

function happyResponse(): StructuralCompressResponse {
  return {
    ranked_context: [
      { path: 'src/a.py', score: 0.03, rank: 1, contributing_signals: ['bm25', 'graph_distance'] },
      { path: 'src/b.py', score: 0.02, rank: 2, contributing_signals: ['graph_distance'] },
    ],
    stats: { files_in: 3, files_ranked: 2, symbols_in: 5, degraded: false },
    message: null,
  };
}

describe('compressCodeStructural', () => {
  it('POSTs to /v1/compress-code/structural and returns the parsed body', async () => {
    const mockFetch = makeMockFetch(happyResponse());
    const gc = makeClient(mockFetch);
    const out = await gc.compressCodeStructural({
      files: [
        { path: 'src/a.py', content: 'def foo(): pass' },
        { path: 'src/b.py', content: 'def bar(): pass' },
      ],
      focus_symbol: 'foo',
      query: 'foo',
      top_k: 10,
    });
    expect(out.ranked_context.length).toBe(2);
    expect(out.ranked_context[0].path).toBe('src/a.py');
    expect(out.stats.degraded).toBe(false);
    expect(mockFetch).toHaveBeenCalledOnce();
    const call = mockFetch.mock.calls[0] as [string, RequestInit];
    expect(call[0]).toBe('https://api.example.com/v1/compress-code/structural');
    expect(call[1].method).toBe('POST');
    const headers = call[1].headers as Record<string, string>;
    expect(headers.Authorization).toBe('Bearer gc_test');
    expect(headers['Content-Type']).toBe('application/json');
    const parsedBody = JSON.parse(call[1].body as string);
    expect(parsedBody.files).toHaveLength(2);
    expect(parsedBody.focus_symbol).toBe('foo');
    expect(parsedBody.top_k).toBe(10);
  });

  it('passes through degraded responses unchanged', async () => {
    const degradedBody: StructuralCompressResponse = {
      ranked_context: [],
      stats: { files_in: 1, files_ranked: 0, symbols_in: 0, degraded: true },
      message: "tensor-grep CLI 'tg' not found on PATH; ...",
    };
    const mockFetch = makeMockFetch(degradedBody);
    const gc = makeClient(mockFetch);
    const out = await gc.compressCodeStructural({
      files: [{ path: 'x.py', content: 'pass' }],
    });
    expect(out.stats.degraded).toBe(true);
    expect(out.message).toMatch(/not found/);
  });

  it('surfaces 4xx errors via ApiError', async () => {
    const mockFetch = vi.fn(async () =>
      new Response(
        JSON.stringify({
          detail: {
            error_code: 'sensitive_content',
            marker_class: 'aws_access_key',
            message: 'refusing',
          },
        }),
        { status: 400, headers: { 'Content-Type': 'application/json' } },
      ),
    );
    const gc = makeClient(mockFetch as unknown as Mock);
    await expect(
      gc.compressCodeStructural({ files: [{ path: 'x', content: 'AKIAIOSFODNN7EXAMPLE' }] }),
    ).rejects.toMatchObject({ status: 400 });
  });
});
