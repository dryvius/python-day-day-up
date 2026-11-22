"""LLM adapter contract and deterministic fake."""

import asyncio
from collections.abc import Mapping, Sequence
from typing import Protocol

import httpx

from ai_chat.types import ChatMessage


class LLMClient(Protocol):
    """Provider-independent completion contract."""

    model: str

    async def complete(
        self,
        messages: Sequence[ChatMessage],
        tools: Sequence[Mapping[str, object]] | None = None,
        **kwargs: object,
    ) -> ChatMessage:
        """Return one canonical assistant message."""


class FakeLLM:
    """Deterministic offline LLM used by local development and CI."""

    def __init__(self, model: str = "fake-chat-v1") -> None:
        self.model = model
        self.last_messages: list[ChatMessage] = []

    async def complete(
        self,
        messages: Sequence[ChatMessage],
        tools: Sequence[Mapping[str, object]] | None = None,
        **kwargs: object,
    ) -> ChatMessage:
        """Reply to the latest user message and retain input for assertions."""

        del tools, kwargs
        self.last_messages = list(messages)
        user_messages = [
            message["content"] for message in messages if message["role"] == "user"
        ]
        latest = user_messages[-1] if user_messages else ""
        previous_turns = max(0, len(user_messages) - 1)
        suffix = f"（已参考 {previous_turns} 轮历史）" if previous_turns else ""
        return {"role": "assistant", "content": f"FakeLLM 回复：{latest}{suffix}"}


class OpenAICompatibleLLM:
    """Minimal OpenAI-compatible HTTP adapter with bounded retries."""

    def __init__(
        self,
        *,
        base_url: str,
        api_key: str,
        model: str,
        timeout_seconds: float,
        max_retries: int,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        self.model = model
        self._endpoint = f"{base_url.rstrip('/')}/chat/completions"
        self._api_key = api_key
        self._timeout = httpx.Timeout(timeout_seconds)
        self._max_retries = max_retries
        self._client = client

    async def complete(
        self,
        messages: Sequence[ChatMessage],
        tools: Sequence[Mapping[str, object]] | None = None,
        **kwargs: object,
    ) -> ChatMessage:
        payload: dict[str, object] = {
            "model": self.model,
            "messages": list(messages),
            **kwargs,
        }
        if tools is not None:
            payload["tools"] = list(tools)

        response = await self._post_with_retry(payload)
        body: object = response.json()
        if not isinstance(body, dict):
            raise TypeError("provider response must be an object")
        choices = body.get("choices")
        if not isinstance(choices, list) or not choices:
            raise ValueError("provider response has no choices")
        first_choice = choices[0]
        if not isinstance(first_choice, dict):
            raise TypeError("provider choice must be an object")
        message = first_choice.get("message")
        if not isinstance(message, dict):
            raise TypeError("provider choice has no message")
        content = message.get("content")
        if not isinstance(content, str) or not content:
            raise ValueError("provider message content must be non-empty")
        return {"role": "assistant", "content": content}

    async def _post_with_retry(self, payload: dict[str, object]) -> httpx.Response:
        owned_client = self._client is None
        client = self._client or httpx.AsyncClient()
        try:
            for attempt in range(self._max_retries + 1):
                try:
                    response = await client.post(
                        self._endpoint,
                        headers={
                            "Authorization": f"Bearer {self._api_key}",
                            "Content-Type": "application/json",
                        },
                        json=payload,
                        timeout=self._timeout,
                    )
                    if response.status_code != 429 and response.status_code < 500:
                        response.raise_for_status()
                        return response
                except (httpx.TimeoutException, httpx.NetworkError):
                    if attempt >= self._max_retries:
                        raise
                else:
                    if attempt >= self._max_retries:
                        response.raise_for_status()
                await asyncio.sleep(0.25 * (2**attempt))
        finally:
            if owned_client:
                await client.aclose()
        raise RuntimeError("provider retry loop exhausted")
