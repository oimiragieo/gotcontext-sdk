"""Nightly live-prod smoke for the published gotcontext Python SDK.

Installs the latest released ``gotcontext`` from PyPI (or uses the
locally-editable install in CI) and calls production with a real
``gc_`` test key. Skipped unless ``PROD_SMOKE_GC_API_KEY`` is set —
the nightly GitHub Actions workflow injects it.

The point of this test is to catch breakage that only surfaces when
a published wheel talks to the live API: changed response shapes,
default base URL drift, outdated dependency pins. Unit-level coverage
lives in ``test_cache_helpers.py`` / ``test_mcp_helpers.py``.
"""

from __future__ import annotations

import os

import pytest


@pytest.mark.live
def test_compress_via_published_sdk() -> None:
    gc_mod = pytest.importorskip("gotcontext")
    key = os.environ.get("PROD_SMOKE_GC_API_KEY")
    if not key:
        pytest.skip("PROD_SMOKE_GC_API_KEY not set")

    client = gc_mod.GotContext(api_key=key)
    result = client.compress(text="smoke " * 20, fidelity="balanced")

    # Response shape check — either a dict or a Pydantic model.
    if hasattr(result, "model_dump"):
        payload = result.model_dump()
    else:
        payload = dict(result) if not isinstance(result, dict) else result
    assert "compressed" in payload or "stats" in payload, payload
