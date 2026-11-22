"""Priority-aware context packing."""

from dataclasses import dataclass

from ai_chat.types import ChatMessage


@dataclass(frozen=True, slots=True)
class ContextSources:
    """Inputs grouped by trust and lifecycle."""

    system: list[ChatMessage]
    hard_constraints: list[ChatMessage]
    history: list[ChatMessage]
    memory: list[ChatMessage]
    rag: list[ChatMessage]
    tool_results: list[ChatMessage]


class ContextPacker:
    """Pack context under a character budget without dropping hard constraints.

    Priority is system/hard constraints, recent history, memory, RAG, then tool
    results. Lower-priority groups are admitted only after higher-priority ones.
    Within history, newest messages win while final output remains chronological.
    """

    def __init__(self, *, budget_chars: int, max_history_messages: int) -> None:
        if budget_chars <= 0 or max_history_messages <= 0:
            raise ValueError("budgets must be positive")
        self._budget_chars = budget_chars
        self._max_history_messages = max_history_messages

    def pack(self, sources: ContextSources) -> list[ChatMessage]:
        """Return packed messages in semantic order."""

        required = [*sources.system, *sources.hard_constraints]
        required_cost = self._cost(required)
        if required_cost > self._budget_chars:
            raise ValueError("system and hard constraints exceed context budget")

        remaining = self._budget_chars - required_cost
        history = self._take_recent(
            sources.history[-self._max_history_messages :],
            remaining,
        )
        remaining -= self._cost(history)

        optional: list[ChatMessage] = []
        for group in (sources.memory, sources.rag, sources.tool_results):
            admitted = self._take_prefix(group, remaining)
            optional.extend(admitted)
            remaining -= self._cost(admitted)

        return [*required, *optional, *history]

    @staticmethod
    def _message_cost(message: ChatMessage) -> int:
        return len(message["role"]) + len(message["content"]) + 8

    def _cost(self, messages: list[ChatMessage]) -> int:
        return sum(self._message_cost(message) for message in messages)

    def _take_recent(
        self,
        messages: list[ChatMessage],
        budget: int,
    ) -> list[ChatMessage]:
        selected: list[ChatMessage] = []
        used = 0
        for message in reversed(messages):
            cost = self._message_cost(message)
            if used + cost > budget:
                break
            selected.append(message)
            used += cost
        selected.reverse()
        return selected

    def _take_prefix(
        self,
        messages: list[ChatMessage],
        budget: int,
    ) -> list[ChatMessage]:
        selected: list[ChatMessage] = []
        used = 0
        for message in messages:
            cost = self._message_cost(message)
            if used + cost > budget:
                break
            selected.append(message)
            used += cost
        return selected
