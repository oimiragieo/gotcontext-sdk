"""Tests for ``gotcontext.cache_helpers.apply_anthropic_breakpoints``."""

from __future__ import annotations

import copy

from gotcontext.cache_helpers import apply_anthropic_breakpoints


def test_inserts_cache_control_on_last_block_of_prefix() -> None:
    messages = [
        {"role": "user", "content": [{"type": "text", "text": "STATIC PREFIX"}]},
        {"role": "user", "content": [{"type": "text", "text": "dynamic question"}]},
    ]
    result = apply_anthropic_breakpoints(
        messages=messages,
        breakpoints=[{"target": "anthropic", "position_tokens": 42, "ttl": "5m"}],
    )
    assert result[0]["content"][0]["cache_control"] == {"type": "ephemeral"}


def test_no_op_when_target_is_not_anthropic() -> None:
    messages = [{"role": "user", "content": [{"type": "text", "text": "x"}]}]
    result = apply_anthropic_breakpoints(
        messages=messages,
        breakpoints=[{"target": "openai", "position_tokens": 10, "ttl": "24h"}],
    )
    assert "cache_control" not in result[0]["content"][0]


def test_ttl_1h_adds_ttl_field() -> None:
    messages = [{"role": "user", "content": [{"type": "text", "text": "prefix"}]}]
    result = apply_anthropic_breakpoints(
        messages=messages,
        breakpoints=[{"target": "anthropic", "position_tokens": 100, "ttl": "1h"}],
    )
    assert result[0]["content"][0]["cache_control"] == {
        "type": "ephemeral",
        "ttl": "1h",
    }


def test_ttl_5m_omits_ttl_field() -> None:
    # 5m is the Anthropic default; omit the ``ttl`` key entirely.
    messages = [{"role": "user", "content": [{"type": "text", "text": "prefix"}]}]
    result = apply_anthropic_breakpoints(
        messages=messages,
        breakpoints=[{"target": "anthropic", "position_tokens": 100, "ttl": "5m"}],
    )
    assert result[0]["content"][0]["cache_control"] == {"type": "ephemeral"}
    assert "ttl" not in result[0]["content"][0]["cache_control"]


def test_does_not_mutate_caller_messages() -> None:
    # Callers often pass the same messages to multiple providers. The helper
    # must not leak ``cache_control`` into the caller's shared state.
    messages = [
        {"role": "user", "content": [{"type": "text", "text": "prefix"}]},
    ]
    snapshot = copy.deepcopy(messages)
    apply_anthropic_breakpoints(
        messages=messages,
        breakpoints=[{"target": "anthropic", "position_tokens": 42, "ttl": "5m"}],
    )
    assert messages == snapshot


def test_empty_breakpoints_returns_messages_unchanged() -> None:
    messages = [{"role": "user", "content": [{"type": "text", "text": "hi"}]}]
    result = apply_anthropic_breakpoints(messages=messages, breakpoints=[])
    assert "cache_control" not in result[0]["content"][0]


def test_empty_messages_returns_empty_list() -> None:
    result = apply_anthropic_breakpoints(
        messages=[],
        breakpoints=[{"target": "anthropic", "position_tokens": 42, "ttl": "5m"}],
    )
    assert result == []


def test_mixed_targets_still_stamps_anthropic() -> None:
    messages = [{"role": "user", "content": [{"type": "text", "text": "prefix"}]}]
    result = apply_anthropic_breakpoints(
        messages=messages,
        breakpoints=[
            {"target": "openai", "position_tokens": 10, "ttl": "24h"},
            {"target": "anthropic", "position_tokens": 42, "ttl": "1h"},
        ],
    )
    assert result[0]["content"][0]["cache_control"] == {
        "type": "ephemeral",
        "ttl": "1h",
    }
