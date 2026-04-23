"""Asynchronous gotcontext API client."""

from __future__ import annotations

import asyncio
from typing import Any, Dict, List, Optional

import httpx

from .exceptions import (
    AuthError,
    GotContextError,
    RateLimitError,
    ServerError,
    ValidationError,
)
from .models import (
    BatchCompressResponse,
    CompressCodeResponse,
    CompressResponse,
    SemanticCacheThresholdResponse,
    StructuralCompressResponse,
    UsageEventsResponse,
    UsageResponse,
)

_DEFAULT_BASE_URL = "https://api.gotcontext.ai"
_DEFAULT_TIMEOUT = 30.0
_MAX_RETRIES = 3
_INITIAL_BACKOFF = 0.5  # seconds


class AsyncGotContext:
    """Asynchronous client for the gotcontext.ai API.

    Example::

        import asyncio
        from gotcontext import AsyncGotContext

        async def main():
            async with AsyncGotContext(api_key="gc_live_...") as gc:
                result = await gc.compress("Your long text here")
                print(f"Saved {result.tokens_saved} tokens")

        asyncio.run(main())
    """

    def __init__(
        self,
        api_key: str,
        *,
        base_url: str = _DEFAULT_BASE_URL,
        timeout: float = _DEFAULT_TIMEOUT,
        max_retries: int = _MAX_RETRIES,
    ) -> None:
        if not api_key:
            raise ValueError("api_key is required")
        self._api_key = api_key
        self._base_url = base_url.rstrip("/")
        self._max_retries = max_retries
        self._client = httpx.AsyncClient(
            base_url=self._base_url,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
                "User-Agent": "gotcontext-python/0.1.0",
            },
            timeout=timeout,
        )

    # --------------------------------------------------------------------- #
    # Core compression
    # --------------------------------------------------------------------- #

    async def compress(
        self,
        text: str,
        *,
        fidelity: str = "balanced",
        query: Optional[str] = None,
        cost_model: Optional[str] = None,
        team_id: Optional[str] = None,
        profile_id: Optional[int] = None,
        style: str = "normal",
    ) -> CompressResponse:
        """Compress text using semantic compression.

        Args:
            text: The text to compress.
            fidelity: Compression level -- ``"abstract"``, ``"outline"``,
                ``"balanced"`` (default), ``"detailed"``, or ``"raw"``.
            query: Optional query string for query-guided compression.
            cost_model: Model name for cost estimation (e.g. ``"claude-sonnet-4-6"``).
            team_id: Attribute the compression to a team workspace.
            profile_id: Apply a saved fidelity profile (overrides fidelity).
            style: v1.4.0 output-style hint -- ``"normal"`` (default),
                ``"terse"``, or ``"verbose"``.

        Returns:
            A :class:`CompressResponse` with compressed text and token stats.
        """
        body: Dict[str, Any] = {"text": text, "fidelity": fidelity}
        if query is not None:
            body["query"] = query
        if cost_model is not None:
            body["cost_model"] = cost_model
        if team_id is not None:
            body["team_id"] = team_id
        if profile_id is not None:
            body["profile_id"] = profile_id
        if style != "normal":
            body["style"] = style

        data = await self._request("POST", "/v1/compress", json=body)
        return CompressResponse.model_validate(data)

    # ----------------------------------------------------------------------
    # v1.4.0 — per-tenant semantic-cache threshold settings
    # ----------------------------------------------------------------------

    async def get_semantic_cache_threshold(self) -> SemanticCacheThresholdResponse:
        """Read the caller's per-tenant semantic-cache similarity cutoff."""
        data = await self._request("GET", "/v1/settings/semantic-cache-threshold")
        return SemanticCacheThresholdResponse.model_validate(data)

    async def set_semantic_cache_threshold(
        self, threshold: Optional[float]
    ) -> SemanticCacheThresholdResponse:
        """Set or clear the caller's per-tenant threshold override.

        Pass ``None`` to reset to the server-wide default.
        """
        body = {"threshold": threshold}
        data = await self._request("PUT", "/v1/settings/semantic-cache-threshold", json=body)
        return SemanticCacheThresholdResponse.model_validate(data)

    async def compress_code_structural(
        self,
        *,
        files: List[Dict[str, Any]],
        focus_symbol: Optional[str] = None,
        query: Optional[str] = None,
        top_k: int = 50,
    ) -> StructuralCompressResponse:
        """v1.5.0 — structural code-context compression (async)."""
        body: Dict[str, Any] = {"files": files, "top_k": top_k}
        if focus_symbol is not None:
            body["focus_symbol"] = focus_symbol
        if query is not None:
            body["query"] = query
        data = await self._request("POST", "/v1/compress-code/structural", json=body)
        return StructuralCompressResponse.model_validate(data)

    async def compress_code(
        self,
        code: str,
        *,
        language: Optional[str] = None,
        fidelity: str = "balanced",
    ) -> CompressCodeResponse:
        """Compress source code with AST-aware compression.

        Args:
            code: The source code to compress.
            language: Language hint (e.g. ``"python"``, ``"typescript"``).
                Auto-detected when omitted.
            fidelity: Compression level (default ``"balanced"``).

        Returns:
            A :class:`CompressCodeResponse` with compressed code and stats.
        """
        body: Dict[str, Any] = {"code": code, "fidelity": fidelity}
        if language is not None:
            body["language"] = language

        data = await self._request("POST", "/v1/compress-code", json=body)
        return CompressCodeResponse.model_validate(data)

    async def batch_compress(
        self,
        documents: List[Dict[str, Any]],
    ) -> BatchCompressResponse:
        """Compress up to 50 documents in a single call.

        Args:
            documents: List of dicts, each with ``"text"`` (required) and
                optional ``"fidelity"`` and ``"query"`` keys.

        Returns:
            A :class:`BatchCompressResponse` with per-document results and
            an aggregate summary.
        """
        data = await self._request("POST", "/v1/batch-compress", json={"documents": documents})
        return BatchCompressResponse.model_validate(data)

    # --------------------------------------------------------------------- #
    # Usage / analytics
    # --------------------------------------------------------------------- #

    async def get_usage(self) -> UsageResponse:
        """Retrieve monthly usage statistics.

        Returns:
            A :class:`UsageResponse` with compression counts and token totals.
        """
        data = await self._request("GET", "/v1/usage")
        return UsageResponse.model_validate(data)

    async def get_usage_events(
        self,
        *,
        page: int = 1,
        page_size: int = 20,
        fidelity: Optional[str] = None,
        method: Optional[str] = None,
    ) -> UsageEventsResponse:
        """Retrieve paginated compression history.

        Args:
            page: 1-based page number (default 1).
            page_size: Results per page, 1-100 (default 20).
            fidelity: Filter by fidelity level.
            method: Filter by method (e.g. ``"REST"``, ``"MCP"``, ``"batch"``).

        Returns:
            A :class:`UsageEventsResponse` with events and pagination info.
        """
        params: Dict[str, Any] = {"page": page, "page_size": page_size}
        if fidelity is not None:
            params["fidelity"] = fidelity
        if method is not None:
            params["method"] = method

        data = await self._request("GET", "/v1/usage/events", params=params)
        return UsageEventsResponse.model_validate(data)

    # --------------------------------------------------------------------- #
    # Lifecycle
    # --------------------------------------------------------------------- #

    async def close(self) -> None:
        """Close the underlying HTTP connection pool."""
        await self._client.aclose()

    async def __aenter__(self) -> "AsyncGotContext":
        return self

    async def __aexit__(self, *_: Any) -> None:
        await self.close()

    # --------------------------------------------------------------------- #
    # Internal helpers
    # --------------------------------------------------------------------- #

    async def _request(
        self,
        method: str,
        path: str,
        *,
        json: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
    ) -> Any:
        """Execute an HTTP request with retry and error mapping."""
        last_exc: Exception | None = None

        for attempt in range(self._max_retries + 1):
            try:
                response = await self._client.request(method, path, json=json, params=params)
            except httpx.HTTPError as exc:
                last_exc = GotContextError(
                    f"HTTP transport error: {exc}",
                    status_code=None,
                    request_id=None,
                )
                if attempt < self._max_retries:
                    await asyncio.sleep(_INITIAL_BACKOFF * (2**attempt))
                    continue
                raise last_exc from exc

            request_id = response.headers.get("x-request-id")

            if response.status_code < 400:
                return response.json()

            # Parse error body best-effort
            try:
                body = response.json()
            except Exception:
                body = {"error": response.text}

            message = body.get("error") or body.get("detail") or response.text

            # Retryable: 429 and 5xx
            if response.status_code in (429, 500, 502, 503, 504):
                if response.status_code == 429:
                    retry_after = _parse_retry_after(response)
                    last_exc = RateLimitError(
                        message,
                        status_code=429,
                        request_id=request_id,
                        body=body,
                        retry_after=retry_after,
                    )
                    if attempt < self._max_retries:
                        wait = retry_after if retry_after else _INITIAL_BACKOFF * (2**attempt)
                        await asyncio.sleep(wait)
                        continue
                else:
                    last_exc = ServerError(
                        message,
                        status_code=response.status_code,
                        request_id=request_id,
                        body=body,
                    )
                    if attempt < self._max_retries:
                        await asyncio.sleep(_INITIAL_BACKOFF * (2**attempt))
                        continue

                raise last_exc

            # Non-retryable errors
            if response.status_code == 401:
                raise AuthError(
                    message,
                    status_code=401,
                    request_id=request_id,
                    body=body,
                )
            if response.status_code == 422:
                raise ValidationError(
                    message,
                    status_code=422,
                    request_id=request_id,
                    body=body,
                )

            raise GotContextError(
                message,
                status_code=response.status_code,
                request_id=request_id,
                body=body,
            )

        # Should not reach here, but just in case
        raise last_exc or GotContextError("Request failed after retries")


def _parse_retry_after(response: httpx.Response) -> float | None:
    """Extract Retry-After header as seconds, or None."""
    value = response.headers.get("retry-after")
    if value is None:
        return None
    try:
        return float(value)
    except (ValueError, TypeError):
        return None
