import { ApiError } from './errors.js';
import type {
  BatchCompressResponse,
  BatchDocument,
  CompressCodeRequest,
  CompressCodeResponse,
  CompressRequest,
  CompressResponse,
  SemanticCacheThresholdResponse,
  StructuralCompressRequest,
  StructuralCompressResponse,
  UsageResponse,
} from './types.js';

export interface GotContextOptions {
  apiKey: string;
  baseUrl?: string;
  maxRetries?: number;
  timeoutMs?: number;
  fetchFn?: typeof fetch;
}

const DEFAULT_BASE = 'https://api.gotcontext.ai';
const SDK_VERSION = '0.5.2';

/**
 * Official TypeScript client for the gotcontext.ai semantic compression API.
 *
 * @example
 * ```ts
 * import { GotContext } from "@gotcontext/sdk";
 * const gc = new GotContext({ apiKey: process.env.GOTCONTEXT_API_KEY! });
 * const out = await gc.compress({ text: longDoc, fidelity: "balanced" });
 * ```
 */
export class GotContext {
  readonly baseUrl: string;
  private readonly apiKey: string;
  private readonly maxRetries: number;
  private readonly timeoutMs: number;
  private readonly fetchFn: typeof fetch;

  constructor(options: GotContextOptions) {
    if (!options?.apiKey) {
      throw new Error('GotContext: apiKey is required');
    }
    this.apiKey = options.apiKey;
    this.baseUrl = (options.baseUrl ?? DEFAULT_BASE).replace(/\/$/, '');
    this.maxRetries = options.maxRetries ?? 2;
    this.timeoutMs = options.timeoutMs ?? 30_000;
    this.fetchFn = options.fetchFn ?? globalThis.fetch;
  }

  /** Compress text using semantic compression. */
  compress(body: CompressRequest): Promise<CompressResponse> {
    return this.request<CompressResponse>('POST', '/v1/compress', body);
  }

  /** Compress source code with AST-aware compression. */
  compressCode(body: CompressCodeRequest): Promise<CompressCodeResponse> {
    return this.request<CompressCodeResponse>('POST', '/v1/compress-code', body);
  }

  /**
   * v1.5.0 — structural code-context compression. Submits a file
   * bundle, runs tensor-grep blast-radius + BM25 on the server, and
   * returns a ranked context list. Intended for PR-diff-scale code
   * payloads (≤1000 files, ≤5 MB total, ≤512 KB per file).
   *
   * @example
   * ```ts
   * const out = await gc.compressCodeStructural({
   *   files: [{ path: "src/app.py", content: "..." }, ...],
   *   focus_symbol: "handle_request",
   *   query: "error handling",
   *   top_k: 25,
   * });
   * out.ranked_context.forEach(item => console.log(item.rank, item.path, item.score));
   * ```
   */
  compressCodeStructural(body: StructuralCompressRequest): Promise<StructuralCompressResponse> {
    return this.request<StructuralCompressResponse>(
      'POST',
      '/v1/compress-code/structural',
      body,
    );
  }

  /** Compress up to 50 documents in a single call. */
  batchCompress(documents: BatchDocument[]): Promise<BatchCompressResponse> {
    return this.request<BatchCompressResponse>('POST', '/v1/batch-compress', { documents });
  }

  /** Retrieve monthly usage statistics. */
  usage(): Promise<UsageResponse> {
    return this.request<UsageResponse>('GET', '/v1/usage');
  }

  /**
   * v1.4.0 — read the caller's per-tenant semantic-cache cosine-similarity
   * cutoff. Returns `{threshold, source}` where `source` is `"user"` when
   * the caller has set their own override, or `"global"` for the
   * server-wide default.
   */
  getSemanticCacheThreshold(): Promise<SemanticCacheThresholdResponse> {
    return this.request<SemanticCacheThresholdResponse>(
      'GET',
      '/v1/settings/semantic-cache-threshold',
    );
  }

  /**
   * v1.4.0 — set (or clear with `null`) the caller's per-tenant
   * semantic-cache similarity cutoff. Values must be in `[0.80, 0.99]`
   * or `null`. Clamping + validation happens server-side.
   */
  setSemanticCacheThreshold(threshold: number | null): Promise<SemanticCacheThresholdResponse> {
    return this.request<SemanticCacheThresholdResponse>(
      'PUT',
      '/v1/settings/semantic-cache-threshold',
      { threshold },
    );
  }

  private async request<T>(
    method: 'GET' | 'POST' | 'PUT',
    path: string,
    body?: unknown,
  ): Promise<T> {
    const url = `${this.baseUrl}${path}`;
    const headers: Record<string, string> = {
      Authorization: `Bearer ${this.apiKey}`,
      'User-Agent': `@gotcontext/sdk/${SDK_VERSION}`,
    };
    if (body !== undefined) {
      headers['Content-Type'] = 'application/json';
    }

    let attempt = 0;
    let lastErr: unknown = null;
    // One initial attempt + maxRetries further retries on transient 5xx.
    // v0.5.2 — also retries 429 with Retry-After when present.
    while (attempt <= this.maxRetries) {
      const controller = new AbortController();
      const timer = setTimeout(() => controller.abort(), this.timeoutMs);
      try {
        const response = await this.fetchFn(url, {
          method,
          headers,
          body: body !== undefined ? JSON.stringify(body) : undefined,
          signal: controller.signal,
        });
        clearTimeout(timer);

        const isRetryable
          = response.status >= 500 || response.status === 429;
        if (isRetryable && attempt < this.maxRetries) {
          attempt += 1;
          // Honour Retry-After on 429 if the server supplied it;
          // otherwise fall back to exponential backoff. Retry-After
          // is either seconds (integer) or an HTTP-date; we support
          // both.
          const retryAfter = response.headers?.get?.('Retry-After') ?? null;
          const waitMs = parseRetryAfterMs(retryAfter) ?? 250 * 2 ** attempt;
          await delay(waitMs);
          continue;
        }

        const text = await response.text();
        const parsed = text ? safeJson(text) : null;
        if (!response.ok) {
          const message = extractErrorMessage(parsed) ?? `HTTP ${response.status}`;
          throw new ApiError(response.status, message, parsed);
        }
        return parsed as T;
      } catch (err) {
        clearTimeout(timer);
        if (err instanceof ApiError) throw err;
        lastErr = err;
        if (attempt >= this.maxRetries) break;
        attempt += 1;
        await delay(250 * 2 ** attempt);
      }
    }
    throw lastErr ?? new Error('GotContext: request failed');
  }
}

function safeJson(text: string): unknown {
  try {
    return JSON.parse(text);
  } catch {
    return text;
  }
}

function extractErrorMessage(parsed: unknown): string | null {
  if (parsed && typeof parsed === 'object') {
    const detail = (parsed as { detail?: unknown }).detail;
    if (typeof detail === 'string') return detail;
    if (Array.isArray(detail) && detail[0] && typeof detail[0] === 'object') {
      return JSON.stringify(detail[0]);
    }
    const error = (parsed as { error?: unknown }).error;
    if (typeof error === 'string') return error;
  }
  return null;
}

function delay(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

/**
 * Parse an HTTP Retry-After header into milliseconds. Accepts integer
 * seconds (e.g. "120") or HTTP-date strings (e.g. "Wed, 21 Oct 2026
 * 07:28:00 GMT"). Returns null on invalid input so callers can fall
 * back to their own backoff strategy.
 *
 * Cap at 30s to avoid a hostile Retry-After from pausing the SDK
 * unreasonably long; let the caller's outer timeout dominate beyond that.
 */
function parseRetryAfterMs(raw: string | null): number | null {
  if (!raw) return null;
  const trimmed = raw.trim();
  const asInt = Number.parseInt(trimmed, 10);
  if (!Number.isNaN(asInt) && String(asInt) === trimmed) {
    return Math.min(asInt * 1000, 30_000);
  }
  const asDate = Date.parse(trimmed);
  if (!Number.isNaN(asDate)) {
    const ms = asDate - Date.now();
    if (ms > 0) return Math.min(ms, 30_000);
  }
  return null;
}
