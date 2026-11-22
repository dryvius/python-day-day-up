"""End-to-end and unit tests for Project 3."""

import asyncio
import json

import httpx
from ai_chat.config import Settings
from ai_chat.context import ContextPacker, ContextSources
from ai_chat.llm import FakeLLM, OpenAICompatibleLLM
from ai_chat.main import create_app
from ai_chat.types import ChatMessage
from fastapi.testclient import TestClient


def test_fake_llm_returns_assistant_dict() -> None:
    client = TestClient(create_app(settings=Settings()))
    response = client.post("/v1/chat", json={"message": "你好"})

    assert response.status_code == 200
    payload = response.json()
    assert payload["reply"] == "FakeLLM 回复：你好"
    assert payload["model"] == "fake-chat-v1"
    assert payload["session_id"]


def test_openai_compatible_adapter_retries_429_without_real_network() -> None:
    attempts = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal attempts
        attempts += 1
        assert request.headers["authorization"] == "Bearer test-secret"
        if attempts == 1:
            return httpx.Response(429, request=request)
        return httpx.Response(
            200,
            request=request,
            json={"choices": [{"message": {"role": "assistant", "content": "ok"}}]},
        )

    async def run() -> ChatMessage:
        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
            adapter = OpenAICompatibleLLM(
                base_url="https://provider.invalid/v1",
                api_key="test-secret",
                model="test-model",
                timeout_seconds=1,
                max_retries=1,
                client=client,
            )
            return await adapter.complete([{"role": "user", "content": "hello"}])

    assert asyncio.run(run()) == {"role": "assistant", "content": "ok"}
    assert attempts == 2


def test_multiturn_history_is_used_and_truncated() -> None:
    settings = Settings(max_history_messages=4)
    app = create_app(settings=settings)
    client = TestClient(app)

    session_id = "history-case"
    for index in range(4):
        response = client.post(
            "/v1/chat",
            json={"session_id": session_id, "message": f"turn-{index}"},
        )
        assert response.status_code == 200

    assert "已参考 1 轮历史" in response.json()["reply"]
    history = app.state.chat_service.history(session_id)
    assert len(history) == 4
    assert history[0]["content"] == "turn-2"


def test_context_packer_preserves_required_and_recent_history() -> None:
    system: ChatMessage = {"role": "system", "content": "system"}
    hard: ChatMessage = {"role": "system", "content": "hard"}
    history = [
        {"role": "user", "content": "old" * 20},
        {"role": "assistant", "content": "recent-answer"},
        {"role": "user", "content": "recent-question"},
    ]
    packer = ContextPacker(budget_chars=100, max_history_messages=3)

    packed = packer.pack(
        ContextSources(
            system=[system],
            hard_constraints=[hard],
            history=history,
            memory=[{"role": "system", "content": "memory" * 20}],
            rag=[],
            tool_results=[],
        )
    )

    assert packed[:2] == [system, hard]
    assert packed[-1]["content"] == "recent-question"
    assert all(message["content"] != "old" * 20 for message in packed)


def test_sse_deltas_reconstruct_non_streaming_reply() -> None:
    settings = Settings(stream_chunk_chars=3)
    fake = FakeLLM()
    app = create_app(settings=settings, llm=fake)
    client = TestClient(app)

    plain = client.post("/v1/chat", json={"session_id": "plain", "message": "重建"})
    stream = client.post(
        "/v1/chat/stream",
        json={"session_id": "stream", "message": "重建"},
    )

    assert stream.status_code == 200
    assert stream.headers["content-type"].startswith("text/event-stream")
    deltas: list[str] = []
    events = stream.text.strip().split("\n\n")
    for event in events:
        if "event: delta" not in event:
            continue
        data_line = next(line for line in event.splitlines() if line.startswith("data: "))
        deltas.append(json.loads(data_line.removeprefix("data: "))["content"])

    assert "".join(deltas) == plain.json()["reply"]
    assert any("event: done" in event for event in events)
