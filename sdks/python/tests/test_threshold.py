"""v1.4.0 F4 — semantic-cache threshold SDK helpers (Python)."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from gotcontext import GotContext
from gotcontext.async_client import AsyncGotContext
from gotcontext.models import SemanticCacheThresholdResponse


def _make_sync_client(responses: list[dict]) -> tuple[GotContext, MagicMock]:
    client = GotContext(api_key="gc_test_key", base_url="https://api.example.com")
    # Swap the underlying httpx.Client for a MagicMock that returns scripted responses.
    mock = MagicMock()
    mock.request = MagicMock(
        side_effect=[
            MagicMock(status_code=200, json=MagicMock(return_value=r), headers={})
            for r in responses
        ]
    )
    client._client = mock  # type: ignore[attr-defined]
    return client, mock


def test_get_returns_global_default_when_no_override() -> None:
    client, mock = _make_sync_client([{"threshold": 0.95, "source": "global"}])
    out = client.get_semantic_cache_threshold()
    assert isinstance(out, SemanticCacheThresholdResponse)
    assert out.threshold == 0.95
    assert out.source == "global"
    # Verify the HTTP call shape.
    mock.request.assert_called_once_with(
        "GET",
        "/v1/settings/semantic-cache-threshold",
        json=None,
        params=None,
    )


def test_set_value_puts_and_echoes_user_source() -> None:
    client, mock = _make_sync_client([{"threshold": 0.92, "source": "user"}])
    out = client.set_semantic_cache_threshold(0.92)
    assert out.threshold == 0.92
    assert out.source == "user"
    mock.request.assert_called_once_with(
        "PUT",
        "/v1/settings/semantic-cache-threshold",
        json={"threshold": 0.92},
        params=None,
    )


def test_set_null_resets_to_global() -> None:
    client, mock = _make_sync_client([{"threshold": 0.95, "source": "global"}])
    out = client.set_semantic_cache_threshold(None)
    assert out.source == "global"
    mock.request.assert_called_once_with(
        "PUT",
        "/v1/settings/semantic-cache-threshold",
        json={"threshold": None},
        params=None,
    )


def test_compress_style_terse_is_sent_in_body() -> None:
    # v1.4.0 F1 — compress() with style="terse" must include the
    # field in the request body, and parse system_prompt_suffix
    # back out of the response.
    client, mock = _make_sync_client(
        [
            {
                "compressed": "terse output",
                "stats": {
                    "original_tokens": 10,
                    "compressed_tokens": 3,
                    "savings_pct": 70.0,
                    "compression_ratio": 3.33,
                },
                "system_prompt_suffix": "Be concise. No filler.",
                "style_suffix_version": "v1",
            }
        ]
    )
    out = client.compress("some long text " * 50, style="terse")
    assert out.system_prompt_suffix == "Be concise. No filler."
    assert out.style_suffix_version == "v1"
    call = mock.request.call_args
    body = call.kwargs["json"]
    assert body["style"] == "terse"


def test_compress_style_default_omits_field() -> None:
    # The default 'normal' should not pollute the request body.
    client, mock = _make_sync_client(
        [
            {
                "compressed": "x",
                "stats": {
                    "original_tokens": 5,
                    "compressed_tokens": 1,
                    "savings_pct": 80.0,
                    "compression_ratio": 5.0,
                },
            }
        ]
    )
    client.compress("hello world " * 50)
    body = mock.request.call_args.kwargs["json"]
    assert "style" not in body


# Async variant — a minimal smoke test via asyncio.run; same backend.


def test_async_threshold_round_trip() -> None:
    import asyncio
    from unittest.mock import AsyncMock

    client = AsyncGotContext(api_key="gc_test_key", base_url="https://api.example.com")
    mock = AsyncMock()
    mock.request = AsyncMock(
        return_value=MagicMock(
            status_code=200,
            json=MagicMock(return_value={"threshold": 0.88, "source": "user"}),
            headers={},
        )
    )
    client._client = mock  # type: ignore[attr-defined]

    async def run():
        out = await client.get_semantic_cache_threshold()
        assert out.threshold == 0.88
        assert out.source == "user"
        await client.close()

    asyncio.run(run())
