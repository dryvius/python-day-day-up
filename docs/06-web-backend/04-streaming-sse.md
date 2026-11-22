# StreamingResponse 与 SSE

> 所属模块：`06-web-backend` · 对应练习：[`exercises/06-web-backend/04-streaming-sse.md`](../../exercises/06-web-backend/04-streaming-sse.md)

## 学习目标

1. 用 FastAPI `StreamingResponse` 输出异步字节流。
2. 正确实现 SSE framing、心跳、错误事件与断连取消。
3. 能在 SSE 与 Job 轮询之间按任务语义选型。

## 1. StreamingResponse 是传输容器

`StreamingResponse` 接受同步或异步迭代器，每次 `yield` 的字节可逐步写给客户端。它不负责定义事件协议，也不自动取消你启动的后台任务。

```python
from collections.abc import AsyncIterator

from fastapi.responses import StreamingResponse


async def chunks() -> AsyncIterator[bytes]:
    yield b"first\n"
    yield b"second\n"


response = StreamingResponse(chunks(), media_type="text/plain")
```

不要在异步生成器中调用阻塞 SDK；使用异步客户端，或明确移入线程池。

## 2. SSE framing 契约

SSE 响应使用 `Content-Type: text/event-stream`。一个事件由字段行组成，并以**两个换行**结束：

```text
id: 42
event: delta
data: {"content":"你"}

event: done
data: {"model":"fake-chat-v1"}

```

关键规则：

- 每行 `data:` 属于同一事件；事件以空行结束。
- `event:` 给事件命名；客户端可区分 `delta`、`done`、`error`。
- 以 `:` 开头的是注释，适合心跳：`: heartbeat\n\n`。
- JSON 只放在 `data:` 后；不要把整段流当一次 JSON 响应解析。
- 建议设置 `Cache-Control: no-cache`、`X-Accel-Buffering: no`，并确认代理没有缓冲。

## 3. 心跳、错误与断连

### 心跳

上游长时间无 token 时，定期发送注释心跳，避免代理把空闲连接回收。心跳间隔必须小于链路中最短的空闲超时，但不能高频制造无意义流量。

### 错误

HTTP 头发出后不能再可靠地改成 `500`。因此：

- 建流前的校验失败：返回正常 HTTP 4xx/5xx。
- 建流后的运行失败：发送 `event: error`，包含稳定 `code` 和可公开的 `message`，随后结束流。
- 不把 traceback、API Key 或上游原始敏感响应发给客户端。

### 断连与取消

每次等待上游或发 chunk 前检查 `await request.is_disconnected()`；若另起 `asyncio.Task`，断连时 `task.cancel()`，并让 `CancelledError` 继续传播。否则浏览器已关闭，服务端仍可能继续付费生成。

```python
async def events(request: Request) -> AsyncIterator[bytes]:
    task = asyncio.create_task(run_llm())
    try:
        while not task.done():
            if await request.is_disconnected():
                task.cancel()
                return
            done, _ = await asyncio.wait({task}, timeout=15)
            if not done:
                yield b": heartbeat\n\n"
        reply = task.result()
        yield encode_sse("delta", {"content": reply})
        yield encode_sse("done", {})
    except asyncio.CancelledError:
        raise
    finally:
        if not task.done():
            task.cancel()
```

## 4. SSE 与 Job 轮询

| 场景 | SSE | Job + 轮询 |
|------|-----|------------|
| 秒级连续 token/进度 | 优先 | 交互较迟钝 |
| 分钟级、需断线后继续 | 连接脆弱 | 优先，状态可持久化 |
| 服务端单向推送 | 合适 | 可用但请求较多 |
| 需要暂停、恢复、重试审计 | 需额外协议 | 天然适配状态机 |

不要把二者误当互斥：长任务可先 `POST /jobs` 返回 `job_id`，客户端轮询最终状态，同时用 SSE 订阅实时进度。SSE 是传输通道，不是持久任务队列。

## 5. 与 LLM 上游流的边界

本章只负责 Web 层 framing、生命周期和取消。Provider 的 `choices[].delta`、流式 `tool_calls` 参数拼装应在 LLM 适配层完成，canonical 见 [LLM API 实战](../09-ai-llm/02-llm-api.md)。不要在路由和客户端各复制一套 delta 拼装状态机。

可运行参考：[Project 3 AI Chat](../../playground/projects/03-ai-chat/README.md)。

## 自检

- [ ] 每个 SSE 事件以空行结束，`data:` 是合法 JSON
- [ ] 有心跳、稳定错误事件、代理禁缓冲配置
- [ ] 客户端断开会取消仍在运行的生成任务
- [ ] 能解释为何分钟级可恢复任务应优先 Job 轮询
- [ ] Web 层不重复 Provider delta/tool-call 拼装

## 导航

- 返回模块：[README](./README.md)
- 上一章：[认证与授权](./03-auth.md)
- 练习：[04-streaming-sse.md](../../exercises/06-web-backend/04-streaming-sse.md)
