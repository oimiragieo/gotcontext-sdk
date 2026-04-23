"""Helpers for passing model attribution on MCP ``tools/call`` requests.

gotcontext.ai reads ``_meta.model`` per call and stamps it on every
``UsageEvent`` so the billing dashboard shows per-model cost savings.
When the model name is unknown to the server, it falls back to the
resolver chain (``api_key.default_model`` → plan heuristic).

Example:

    from gotcontext.mcp_helpers import meta_for_call

    result = await session.call_tool(
        "ingest_context",
        {"text": doc, "file_id": "doc-1"},
        meta=meta_for_call(model="claude-opus-4.6"),
    )

See ``docs/model-attribution.md`` for the full resolution chain.
"""

from __future__ import annotations

from typing import Any


def meta_for_call(*, model: str | None = None, **extra: Any) -> dict[str, Any]:
    """Build a ``_meta`` payload for a ``tools/call`` request.

    Parameters
    ----------
    model:
        Optional model identifier (e.g. ``"claude-opus-4.6"``). Included
        in the returned payload when truthy.
    **extra:
        Arbitrary additional ``_meta`` fields (e.g. ``trace_id``). Values
        that are ``None`` are filtered out so callers can pass optional
        kwargs through without producing noisy ``null`` entries.

    Returns
    -------
    dict
        A plain ``dict`` suitable for ``meta=`` on the MCP SDK's
        ``call_tool`` method. Empty when no fields are provided.
    """
    meta: dict[str, Any] = {k: v for k, v in extra.items() if v is not None}
    if model:
        meta["model"] = model
    return meta
