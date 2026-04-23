"""v1.5.0 — ``compress_code_structural`` SDK helpers (sync + async).

Offline: underlying httpx.Client/AsyncClient is MagicMocked.
"""

from __future__ import annotations

from unittest.mock import MagicMock

from gotcontext import GotContext
from gotcontext.async_client import AsyncGotContext
from gotcontext.models import StructuralCompressResponse


def _happy_body() -> dict:
    return {
        "ranked_context": [
            {
                "path": "src/a.py",
                "score": 0.031,
                "rank": 1,
                "contributing_signals": ["bm25", "graph_distance"],
            },
            {
                "path": "src/b.py",
                "score": 0.019,
                "rank": 2,
                "contributing_signals": ["graph_distance"],
            },
        ],
        "stats": {
            "files_in": 3,
            "files_ranked": 2,
            "symbols_in": 7,
            "degraded": False,
        },
        "message": None,
    }


def _make_sync_client() -> tuple[GotContext, MagicMock]:
    client = GotContext(api_key="gc_test", base_url="https://api.example.com")
    mock = MagicMock()
    mock.request = MagicMock(
        return_value=MagicMock(status_code=200, json=MagicMock(return_value=_happy_body()), headers={})
    )
    client._client = mock  # type: ignore[attr-defined]
    return client, mock


def test_sync_compress_code_structural_posts_and_parses():
    client, mock = _make_sync_client()
    out = client.compress_code_structural(
        files=[
            {"path": "src/a.py", "content": "def foo(): pass"},
            {"path": "src/b.py", "content": "def bar(): pass"},
            {"path": "src/c.py", "content": "def baz(): pass"},
        ],
        focus_symbol="foo",
        query="foo",
        top_k=10,
    )
    assert isinstance(out, StructuralCompressResponse)
    assert out.stats.files_in == 3
    assert out.ranked_context[0].path == "src/a.py"
    assert out.ranked_context[0].contributing_signals == ["bm25", "graph_distance"]
    # Request shape.
    call = mock.request.call_args
    assert call.args == ("POST", "/v1/compress-code/structural")
    body = call.kwargs["json"]
    assert body["focus_symbol"] == "foo"
    assert body["query"] == "foo"
    assert body["top_k"] == 10
    assert len(body["files"]) == 3


def test_sync_omits_optional_fields_when_defaults():
    client, mock = _make_sync_client()
    client.compress_code_structural(files=[{"path": "a.py", "content": "pass"}])
    body = mock.request.call_args.kwargs["json"]
    assert "focus_symbol" not in body
    assert "query" not in body
    assert body["top_k"] == 50


def test_async_compress_code_structural() -> None:
    import asyncio
    from unittest.mock import AsyncMock

    client = AsyncGotContext(api_key="gc_test", base_url="https://api.example.com")
    mock = AsyncMock()
    mock.request = AsyncMock(
        return_value=MagicMock(status_code=200, json=MagicMock(return_value=_happy_body()), headers={})
    )
    client._client = mock  # type: ignore[attr-defined]

    async def run():
        out = await client.compress_code_structural(
            files=[{"path": "a.py", "content": "pass"}],
            focus_symbol="foo",
        )
        assert out.stats.files_ranked == 2
        await client.close()

    asyncio.run(run())
