"""Drop-in helpers for piping gotcontext ``cache_breakpoints`` into the
Anthropic SDK ``messages.create`` payload. Zero dependencies, stdlib only.

The gotcontext ``/v1/compress`` response includes a ``cache_breakpoints``
array describing where Anthropic's prompt cache should be anchored so the
static prefix of a prompt is billed once and reused on subsequent calls.
This helper stamps the appropriate ``cache_control`` marker on the last
content block of the cached prefix.

Example:

    from gotcontext import GotContext, apply_anthropic_breakpoints

    gc = GotContext(api_key="gc_live_...")
    compressed = gc.compress(long_doc, fidelity="balanced")

    messages = [
        {"role": "user", "content": [{"type": "text", "text": compressed.compressed}]},
        {"role": "user", "content": [{"type": "text", "text": user_question}]},
    ]
    messages = apply_anthropic_breakpoints(
        messages=messages,
        breakpoints=compressed.cache_breakpoints,
    )

    # The Anthropic SDK now sees ``cache_control`` on the prefix block.
    anthropic_client.messages.create(model="claude-opus-4-5", messages=messages, ...)

Only breakpoints with ``target == "anthropic"`` are honored. OpenAI /
Gemini breakpoints are ignored; this helper is deliberately narrow so it
ships with zero SDK surface area in v1.1.
"""

from __future__ import annotations

import copy
from typing import Any


def apply_anthropic_breakpoints(
    messages: list[dict[str, Any]],
    breakpoints: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Return a new ``messages`` list with Anthropic ``cache_control`` stamped.

    Parameters
    ----------
    messages:
        An Anthropic-style messages list — each entry is
        ``{"role": ..., "content": [{"type": "text", "text": ...}, ...]}``.
        The input is **not** mutated; callers can safely pass the same
        messages to multiple providers.
    breakpoints:
        The ``cache_breakpoints`` array returned by ``/v1/compress``. Each
        entry is a dict with at least ``target`` and ``ttl``. Only entries
        whose ``target`` equals ``"anthropic"`` contribute to the output.

    Returns
    -------
    list
        A deep copy of ``messages`` with ``cache_control`` added to the
        last content block of the first message when an Anthropic
        breakpoint is present. When no Anthropic breakpoint is present,
        or when ``messages`` is empty, the input is returned unchanged.

    Notes
    -----
    - ``ttl == "1h"`` adds ``"ttl": "1h"`` to the ``cache_control`` dict.
    - ``ttl == "5m"`` (Anthropic's default) omits the ``ttl`` key entirely
      per the Anthropic API contract.
    """
    relevant = [bp for bp in breakpoints if bp.get("target") == "anthropic"]
    if not relevant or not messages:
        return messages

    ttl = relevant[-1].get("ttl", "5m")
    cache_control: dict[str, Any] = {"type": "ephemeral"}
    if ttl == "1h":
        cache_control["ttl"] = "1h"

    # Deep copy so the caller's shared state is never mutated.
    result = copy.deepcopy(messages)
    first = result[0]
    content = first.get("content")
    if isinstance(content, list) and content:
        content[-1]["cache_control"] = cache_control
    return result
