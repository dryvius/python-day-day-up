"""Canonical FakeLLM adapter returning an assistant message dictionary."""

from collections.abc import Mapping, Sequence

from rag_kb.types import AssistantMessage


class FakeLLM:
    model = "fake-rag-v1"

    async def complete(
        self,
        messages: Sequence[Mapping[str, str]],
        tools: Sequence[Mapping[str, object]] | None = None,
        **kwargs: object,
    ) -> AssistantMessage:
        del tools, kwargs
        context = next(
            (
                message["content"]
                for message in reversed(messages)
                if message.get("role") == "system"
            ),
            "",
        )
        first_line = next(
            (line.removeprefix("- ").strip() for line in context.splitlines() if line.startswith("- ")),
            "未找到可用资料。",
        )
        return {
            "role": "assistant",
            "content": f"根据知识库：{first_line}",
        }
