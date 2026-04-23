"""Exceptions raised by the gotcontext SDK."""

from __future__ import annotations


class GotContextError(Exception):
    """Base exception for all gotcontext API errors."""

    def __init__(
        self,
        message: str,
        *,
        status_code: int | None = None,
        request_id: str | None = None,
        body: dict | None = None,
    ) -> None:
        self.status_code = status_code
        self.request_id = request_id
        self.body = body or {}
        parts = [message]
        if request_id:
            parts.append(f"(request_id={request_id})")
        super().__init__(" ".join(parts))


class AuthError(GotContextError):
    """Raised on HTTP 401 -- invalid or missing API key."""


class RateLimitError(GotContextError):
    """Raised on HTTP 429 -- rate or quota limit exceeded."""

    def __init__(
        self,
        message: str,
        *,
        status_code: int | None = 429,
        request_id: str | None = None,
        body: dict | None = None,
        retry_after: float | None = None,
    ) -> None:
        super().__init__(
            message,
            status_code=status_code,
            request_id=request_id,
            body=body,
        )
        self.retry_after = retry_after


class ValidationError(GotContextError):
    """Raised on HTTP 422 -- request body failed server-side validation."""


class ServerError(GotContextError):
    """Raised on HTTP 5xx -- unexpected server-side failure."""
