/**
 * Fidelity presets — compression aggressiveness from heaviest to
 * lightest.  Defaults to `"balanced"`.
 */
export type Fidelity = 'abstract' | 'outline' | 'balanced' | 'detailed' | 'raw';

export interface CompressRequest {
  text: string;
  fidelity?: Fidelity;
  query?: string;
  cost_model?: string;
  team_id?: string;
  profile_id?: number;
  /**
   * v1.4.0 — output-style hint. When `"terse"`, the response's
   * `system_prompt_suffix` carries a short rule block to inject into
   * the downstream LLM's system prompt (~63% output-token reduction
   * on April 2026 benchmarks).
   */
  style?: 'terse' | 'normal' | 'verbose';
}

export interface CompressStats {
  original_tokens: number;
  compressed_tokens: number;
  compression_ratio: number;
  tokens_saved: number;
  cost_saved_usd?: number;
}

export interface CompressResponse {
  /**
   * v1.5.2 — compressed skeleton text. Matches the server field name
   * returned by `POST /v1/compress` (`compressed: str`).
   */
  compressed: string;
  /**
   * @deprecated Since v0.5.1 — was never populated at runtime; server
   * returns `compressed`, not `compressed_text`. Use `compressed`.
   * Scheduled for removal in v0.6.0.
   */
  compressed_text?: string;
  fidelity: Fidelity;
  stats: CompressStats;
  /** v1.4.0 — non-null only when the request set style="terse". */
  system_prompt_suffix?: string | null;
  /** v1.4.0 — version tag of the returned suffix (currently "v1"). */
  style_suffix_version?: string | null;
}

/**
 * v1.4.0 — exact vs semantic hit breakdown emitted by
 * `GET /v1/usage/by-cache` alongside the existing
 * `semantic_cache` rollup. `exact_hits + semantic_hits ==
 * semantic_cache.hits`.
 */
export interface HitSourceBreakdown {
  exact_hits: number;
  semantic_hits: number;
  misses: number;
}

/**
 * v1.4.0 — returned by `GET/PUT /v1/settings/semantic-cache-threshold`.
 * `threshold` is cosine similarity in `[0.80, 0.99]`.
 */
export interface SemanticCacheThresholdResponse {
  threshold: number;
  source: 'user' | 'global';
}

// ---------------------------------------------------------------------------
// v1.5.0+ — structural code-context (/v1/compress-code/structural)
// ---------------------------------------------------------------------------

export interface StructuralFile {
  path: string;
  content: string;
}

export interface StructuralCompressRequest {
  files: StructuralFile[];
  focus_symbol?: string;
  query?: string;
  top_k?: number;
}

export interface RankedContextItem {
  path: string;
  score: number;
  rank: number;
  contributing_signals: string[];
}

export interface StructuralCompressStats {
  files_in: number;
  files_ranked: number;
  symbols_in: number;
  degraded: boolean;
}

export interface StructuralCompressResponse {
  ranked_context: RankedContextItem[];
  stats: StructuralCompressStats;
  message?: string | null;
}

export interface CompressCodeRequest {
  code: string;
  language?: string;
  fidelity?: Fidelity;
}

export interface CompressCodeResponse {
  /**
   * v1.5.2 — compressed skeleton code. Matches the server field name
   * returned by `POST /v1/compress-code` (`compressed: str`).
   */
  compressed: string;
  /**
   * @deprecated Since v0.5.1 — was never populated at runtime; server
   * returns `compressed`. Use `compressed`. Scheduled for removal in
   * v0.6.0.
   */
  compressed_code?: string;
  language: string;
  fidelity: Fidelity;
  stats: CompressStats;
}

export interface BatchDocument {
  text: string;
  fidelity?: Fidelity;
  query?: string;
  id?: string;
}

export interface BatchItemResult {
  id?: string;
  /**
   * v1.5.2 — compressed skeleton text for this batch item. Matches
   * the server field name returned inside `BatchResultItem`.
   */
  compressed?: string;
  /**
   * @deprecated Since v0.5.1 — was never populated at runtime; server
   * returns `compressed`. Use `compressed`. Scheduled for removal in
   * v0.6.0.
   */
  compressed_text?: string;
  stats?: CompressStats;
  error?: string;
}

export interface BatchCompressResponse {
  items: BatchItemResult[];
  summary: {
    total: number;
    succeeded: number;
    failed: number;
    total_tokens_saved: number;
  };
}

export interface UsageResponse {
  plan: string;
  period_start: string;
  period_end: string;
  compressions_used: number;
  compressions_limit: number;
  tokens_saved: number;
}
