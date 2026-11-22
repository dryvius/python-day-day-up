# Project 3：AI Chat

独立 FastAPI 项目，默认使用确定性的 `FakeLLM`，包含多轮历史、优先级上下文装配、JSON 与 SSE 两种 Chat API。

规格文档里的学习者脚手架常用包名 `app/`；本参考实现包名为 `ai_chat`。已包含 OpenAI-compatible 适配层（timeout + 有限重试）与 `prompts/system.md`。刻意简化：SSE 在完整回复生成后再分片推送（含心跳与断连取消），不做 Provider 侧 token-by-token 上游流式拼装。

## 安装与运行

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[dev]'
uvicorn ai_chat.main:app --reload
```

默认 Fake 模式无需 API Key。参考实现同时提供 `LLMClient` Protocol 与 OpenAI-compatible HTTP adapter；真模型是可选运行路径，不会在测试或 CI 中调用。

## API

- `GET /health`
- `POST /v1/chat`：`{"session_id": "可选", "message": "你好"}`
- `POST /v1/chat/stream`：相同请求体，返回 `text/event-stream`

SSE 事件为 `delta`、`done`、`error`，空闲期发送 `: heartbeat` 注释。客户端断开时会取消尚未完成的任务。该层仅对已完成的 assistant 文本分片；上游 delta/tool-call 拼装必须留在 Provider 适配层。

```bash
curl -N -X POST http://127.0.0.1:8000/v1/chat/stream \
  -H 'content-type: application/json' \
  -d '{"session_id":"demo","message":"解释 SSE"}'
```

## 配置

默认 system prompt 位于 `prompts/system.md`。复制 `.env.example` 为 `.env` 后，可配置字符预算、历史条数、流式分片大小和心跳间隔。

如需连接兼容 OpenAI Chat Completions 的服务，设置 `LLM_MODE=openai-compatible`、`LLM_BASE_URL`、`MODEL_NAME` 与本地环境变量 `LLM_API_KEY`。适配器包含 timeout 和有限的 429/5xx 退避重试。不要提交 `.env`、真实 Key 或在日志中输出请求 Header；CI 固定使用 Fake 模式。

## 测试

```bash
pytest
```

测试覆盖 Fake 契约、无网络的 Provider adapter/retry、多轮历史截断、ContextPacker 预算，以及 SSE delta 可拼回非流式完整回复。
