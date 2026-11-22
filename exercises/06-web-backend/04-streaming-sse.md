# 练习：StreamingResponse 与 SSE

对应正文：[`docs/06-web-backend/04-streaming-sse.md`](../../docs/06-web-backend/04-streaming-sse.md)

## 基础

1. 写 `encode_sse(event, data, event_id=None) -> bytes`，确保事件以 `\n\n` 结束，中文 JSON 不转义。
2. 用 `StreamingResponse` 暴露 `/events`，依次发送两个 `delta` 和一个 `done`。
3. 写测试断言 `Content-Type` 为 `text/event-stream`，两个 delta 可拼回原文。

## 进阶

4. 用 `asyncio.wait(..., timeout=...)` 在慢任务期间发送 `: heartbeat\n\n`。
5. 模拟生成器抛错：建流后发送 `event: error`，不得泄露 traceback。
6. 模拟客户端断开，断言上游 task 收到取消；`CancelledError` 不得被吞掉。

## 设计题

分别为以下需求选择 SSE、Job 轮询或二者组合，并说明恢复语义：

- 20 秒 LLM token 输出
- 30 分钟文档索引
- 可能刷新页面但仍要查看最终结果的研究任务

## 验收

- [ ] framing、中文 JSON、空行终止均有测试
- [ ] 心跳不会成为业务事件
- [ ] 错误使用稳定 code，不返回敏感内部信息
- [ ] 断连停止计算或付费调用
- [ ] 未在 Web 层重写 Provider delta/tool-call 拼装
