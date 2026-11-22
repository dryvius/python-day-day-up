"""FastAPI application and JSON/SSE chat endpoints."""

import asyncio
from collections.abc import AsyncIterator

from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse

from ai_chat.config import Settings, get_settings
from ai_chat.context import ContextPacker
from ai_chat.llm import FakeLLM, LLMClient, OpenAICompatibleLLM
from ai_chat.logging_setup import configure_logging
from ai_chat.schemas import ChatRequest, ChatResponse
from ai_chat.service import ChatService
from ai_chat.streaming import sse_event, sse_heartbeat


def create_app(
    *,
    settings: Settings | None = None,
    llm: LLMClient | None = None,
) -> FastAPI:
    """Build an application with explicit injectable dependencies."""

    resolved_settings = settings or get_settings()
    resolved_llm = llm
    if resolved_llm is None and resolved_settings.llm_mode == "fake":
        resolved_llm = FakeLLM(resolved_settings.model_name)
    elif resolved_llm is None and resolved_settings.llm_mode == "openai-compatible":
        if resolved_settings.llm_api_key is None:
            raise ValueError("LLM_API_KEY is required for openai-compatible mode")
        resolved_llm = OpenAICompatibleLLM(
            base_url=resolved_settings.llm_base_url,
            api_key=resolved_settings.llm_api_key.get_secret_value(),
            model=resolved_settings.model_name,
            timeout_seconds=resolved_settings.llm_timeout_seconds,
            max_retries=resolved_settings.llm_max_retries,
        )
    elif resolved_llm is None:
        raise ValueError(f"unsupported LLM_MODE: {resolved_settings.llm_mode}")

    configure_logging()
    application = FastAPI(title=resolved_settings.app_name, version="1.0.0")
    service = ChatService(
        llm=resolved_llm,
        packer=ContextPacker(
            budget_chars=resolved_settings.context_budget_chars,
            max_history_messages=resolved_settings.max_history_messages,
        ),
        system_prompt=resolved_settings.system_prompt,
        max_history_messages=resolved_settings.max_history_messages,
    )
    application.state.chat_service = service

    @application.get("/health", tags=["system"])
    async def health() -> dict[str, str]:
        return {"status": "ok", "model": service.model}

    @application.post("/v1/chat", response_model=ChatResponse, tags=["chat"])
    async def chat(payload: ChatRequest) -> ChatResponse:
        session_id, reply = await service.complete(payload.session_id, payload.message)
        return ChatResponse(session_id=session_id, reply=reply, model=service.model)

    @application.post("/v1/chat/stream", tags=["chat"])
    async def chat_stream(payload: ChatRequest, request: Request) -> StreamingResponse:
        async def events() -> AsyncIterator[bytes]:
            completion = asyncio.create_task(
                service.complete(payload.session_id, payload.message)
            )
            try:
                while not completion.done():
                    if await request.is_disconnected():
                        completion.cancel()
                        return
                    done, _ = await asyncio.wait(
                        {completion},
                        timeout=resolved_settings.heartbeat_seconds,
                    )
                    if not done:
                        yield sse_heartbeat()

                session_id, reply = completion.result()
                for index in range(0, len(reply), resolved_settings.stream_chunk_chars):
                    if await request.is_disconnected():
                        return
                    chunk = reply[index : index + resolved_settings.stream_chunk_chars]
                    yield sse_event("delta", {"content": chunk})
                    await asyncio.sleep(0)
                yield sse_event(
                    "done",
                    {"session_id": session_id, "model": service.model},
                )
            except asyncio.CancelledError:
                raise
            # SSE 已开始发送后不能改 HTTP 状态；此边界把未知 Provider 故障
            # 转成稳定的 error 事件，且不向客户端泄漏异常或凭证。
            except Exception:
                yield sse_event(
                    "error",
                    {"code": "stream_failed", "message": "stream interrupted"},
                )
            finally:
                if not completion.done():
                    completion.cancel()

        return StreamingResponse(
            events(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "X-Accel-Buffering": "no",
            },
        )

    return application


app = create_app()
