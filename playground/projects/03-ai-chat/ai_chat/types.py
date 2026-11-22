"""Shared message types."""

from typing import Literal, TypedDict


class ChatMessage(TypedDict):
    """Canonical chat message."""

    role: Literal["system", "user", "assistant", "tool"]
    content: str
