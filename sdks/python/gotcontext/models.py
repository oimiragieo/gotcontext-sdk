"""Pydantic response models for the gotcontext API."""

from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel

# --------------------------------------------------------------------------- #
# POST /v1/compress
# --------------------------------------------------------------------------- #


class CompressStats(BaseModel):
    """Token statistics returned by /v1/compress."""

    original_tokens: int
    compressed_tokens: int
    savings_pct: float
    compression_ratio: float
    estimated_cost_saved: Optional[float] = None


class CompressResponse(BaseModel):
    """Response from POST /v1/compress."""

    compressed: str
    stats: CompressStats
    # v1.4.0 F1 — populated when the request set style="terse".
    system_prompt_suffix: Optional[str] = None
    style_suffix_version: Optional[str] = None

    # Convenience accessors so callers can write result.tokens_saved etc.
    @property
    def tokens_saved(self) -> int:
        return self.stats.original_tokens - self.stats.compressed_tokens

    @property
    def savings_pct(self) -> float:
        return self.stats.savings_pct


# --------------------------------------------------------------------------- #
# v1.4.0 — settings: per-tenant semantic-cache threshold
# --------------------------------------------------------------------------- #


class SemanticCacheThresholdResponse(BaseModel):
    """Response from GET/PUT /v1/settings/semantic-cache-threshold."""

    threshold: float
    source: str  # "user" | "global"


# --------------------------------------------------------------------------- #
# v1.4.0 — hit-source breakdown on /v1/usage/by-cache
# --------------------------------------------------------------------------- #


class HitSourceBreakdown(BaseModel):
    """Exact vs semantic hit counts alongside the semantic_cache rollup."""

    exact_hits: int
    semantic_hits: int
    misses: int


# --------------------------------------------------------------------------- #
# v1.5.0+ — structural code-context (/v1/compress-code/structural)
# --------------------------------------------------------------------------- #


class StructuralFile(BaseModel):
    path: str
    content: str


class RankedContextItem(BaseModel):
    path: str
    score: float
    rank: int
    contributing_signals: list[str]


class StructuralCompressStats(BaseModel):
    files_in: int
    files_ranked: int
    symbols_in: int
    degraded: bool


class StructuralCompressResponse(BaseModel):
    ranked_context: list[RankedContextItem]
    stats: StructuralCompressStats
    message: Optional[str] = None


# --------------------------------------------------------------------------- #
# POST /v1/compress-code
# --------------------------------------------------------------------------- #


class CompressCodeStats(BaseModel):
    """Token statistics returned by /v1/compress-code."""

    original_tokens: int
    compressed_tokens: int
    savings_pct: float
    language_detected: Optional[str] = None


class CompressCodeResponse(BaseModel):
    """Response from POST /v1/compress-code."""

    compressed: str
    stats: CompressCodeStats

    @property
    def tokens_saved(self) -> int:
        return self.stats.original_tokens - self.stats.compressed_tokens

    @property
    def savings_pct(self) -> float:
        return self.stats.savings_pct


# --------------------------------------------------------------------------- #
# POST /v1/batch-compress
# --------------------------------------------------------------------------- #


class BatchItem(BaseModel):
    """A single result inside a batch response."""

    compressed: Optional[str] = None
    original_tokens: int = 0
    compressed_tokens: int = 0
    savings_pct: float = 0.0
    compression_ratio: float = 0.0
    error: Optional[str] = None


class BatchSummary(BaseModel):
    """Aggregate statistics for a batch compression."""

    total_documents: int
    successful: int
    failed: int
    total_tokens_in: int
    total_tokens_saved: int
    avg_savings_pct: float
    avg_compression_ratio: float


class BatchCompressResponse(BaseModel):
    """Response from POST /v1/batch-compress."""

    results: List[BatchItem]
    summary: BatchSummary


# --------------------------------------------------------------------------- #
# GET /v1/usage
# --------------------------------------------------------------------------- #


class UsageResponse(BaseModel):
    """Response from GET /v1/usage."""

    period: str
    compressions_used: int
    compressions_limit: int
    pct_used: float
    tokens_in: int
    tokens_saved: int
    resets_at: str


# --------------------------------------------------------------------------- #
# GET /v1/usage/events
# --------------------------------------------------------------------------- #


class CompressionEvent(BaseModel):
    """A single compression event in the history."""

    id: str
    tokens_in: int
    tokens_out: int
    tokens_saved: int
    savings_pct: float
    fidelity: str
    method: Optional[str] = None
    latency_ms: Optional[int] = None
    input_preview: Optional[str] = None
    tool_name: Optional[str] = None
    profile_name: Optional[str] = None
    created_at: datetime


class UsageEventsResponse(BaseModel):
    """Paginated response from GET /v1/usage/events."""

    events: List[CompressionEvent]
    total: int
    page: int
    page_size: int
    has_more: bool
