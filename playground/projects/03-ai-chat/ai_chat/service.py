"""Chat orchestration and in-memory session history."""

import asyncio
import logging
import time
from uuid import uuid4

from ai_chat.context import ContextPacker, ContextSources
from ai_chat.llm import LLMClient
from ai_chat.types import ChatMessage

LOGGER = logging.getLogger(__name__)


class ChatService:
    """Coordinate history, packing and the LLM adapter."""

    def __init__(
        self,
        *,
        llm: LLMClient,
        packer: ContextPacker,
        system_prompt: str,
        max_history_messages: int,
    ) -> None:
        self._llm = llm
        self._packer = packer
        self._system_prompt = system_prompt
        self._max_history_messages = max_history_messages
        self._sessions: dict[str, list[ChatMessage]] = {}
        self._locks: dict[str, asyncio.Lock] = {}

    @property
    def model(self) -> str:
        """Expose the active model name."""

        return self._llm.model

    async def complete(self, session_id: str | None, message: str) -> tuple[str, str]:
        """Run one turn and atomically append user/assistant history."""

        resolved_id = session_id or uuid4().hex
        lock = self._locks.setdefault(resolved_id, asyncio.Lock())
        started = time.perf_counter()

        async with lock:
            history = self._sessions.setdefault(resolved_id, [])
            user_message: ChatMessage = {"role": "user", "content": message}
            prompt = self._packer.pack(
                ContextSources(
                    system=[{"role": "system", "content": self._system_prompt}],
                    hard_constraints=[],
                    history=[*history, user_message],
                    memory=[],
                    rag=[],
                    tool_results=[],
                )
            )
            assistant = await self._llm.complete(prompt)
            if assistant.get("role") != "assistant" or not assistant.get("content"):
                raise ValueError("LLM must return a non-empty assistant message")

            history.extend((user_message, assistant))
            del history[: max(0, len(history) - self._max_history_messages)]

        latency_ms = round((time.perf_counter() - started) * 1000, 2)
        LOGGER.info(
            "chat_completed session_id=%s model=%s latency_ms=%s",
            resolved_id,
            self.model,
            latency_ms,
        )
        return resolved_id, assistant["content"]

    def history(self, session_id: str) -> list[ChatMessage]:
        """Return a defensive history copy for diagnostics and tests."""

        return list(self._sessions.get(session_id, []))
