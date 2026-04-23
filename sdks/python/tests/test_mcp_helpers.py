"""Tests for ``gotcontext.mcp_helpers.meta_for_call``."""

from gotcontext.mcp_helpers import meta_for_call


def test_model_included() -> None:
    assert meta_for_call(model="claude-opus-4.6") == {"model": "claude-opus-4.6"}


def test_model_absent_returns_empty() -> None:
    assert meta_for_call() == {}


def test_extra_kwargs_passthrough() -> None:
    assert meta_for_call(model="x", trace_id="abc") == {"model": "x", "trace_id": "abc"}


def test_none_values_are_filtered() -> None:
    # v0.2.0 convention: None-valued extras are dropped so callers can pass
    # optional kwargs through without producing noisy ``null`` entries.
    assert meta_for_call(model=None, trace_id=None) == {}
    assert meta_for_call(model="x", trace_id=None) == {"model": "x"}


def test_returns_plain_dict() -> None:
    result = meta_for_call(model="claude-opus-4.6", trace_id="abc")
    assert type(result) is dict
