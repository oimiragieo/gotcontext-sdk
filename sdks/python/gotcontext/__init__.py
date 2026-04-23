"""gotcontext -- Python SDK for the gotcontext.ai semantic compression API."""

from .async_client import AsyncGotContext
from .cache_helpers import apply_anthropic_breakpoints
from .client import GotContext
from .mcp_helpers import meta_for_call
from .exceptions import (
    AuthError,
    GotContextError,
    RateLimitError,
    ServerError,
    ValidationError,
)
from .models import (
    BatchCompressResponse,
    BatchItem,
    BatchSummary,
    CompressCodeResponse,
    CompressCodeStats,
    CompressResponse,
    CompressStats,
    CompressionEvent,
    UsageEventsResponse,
    UsageResponse,
)

__all__ = [
    # Clients
    "GotContext",
    "AsyncGotContext",
    # Exceptions
    "GotContextError",
    "AuthError",
    "RateLimitError",
    "ValidationError",
    "ServerError",
    # Models
    "CompressResponse",
    "CompressStats",
    "CompressCodeResponse",
    "CompressCodeStats",
    "BatchCompressResponse",
    "BatchItem",
    "BatchSummary",
    "UsageResponse",
    "UsageEventsResponse",
    "CompressionEvent",
    # MCP helpers
    "meta_for_call",
    # Cache helpers
    "apply_anthropic_breakpoints",
]

__version__ = "0.3.0"
