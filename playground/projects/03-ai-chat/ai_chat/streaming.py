"""SSE framing helpers.

This transport layer emits already-completed assistant text. Provider-specific
delta and tool-call assembly belongs in the provider adapter, not here.
"""

import json


def sse_event(event: str, data: object, *, event_id: str | None = None) -> bytes:
    """Encode one standards-compatible SSE event."""

    lines: list[str] = []
    if event_id is not None:
        lines.append(f"id: {event_id}")
    lines.append(f"event: {event}")
    payload = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
    lines.extend(f"data: {line}" for line in payload.splitlines() or [""])
    return ("\n".join(lines) + "\n\n").encode()


def sse_heartbeat() -> bytes:
    """Encode a comment heartbeat ignored by EventSource clients."""

    return b": heartbeat\n\n"
