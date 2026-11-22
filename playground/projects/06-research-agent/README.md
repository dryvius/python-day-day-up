# Project 6：Research Agent

可离线运行的生产化收官项目：FastAPI 只负责 Job API，研究任务进入内存
`asyncio.Queue`，由生命周期内启动的独立 Worker 消费。FakeLLM、知识库和 URL
抓取均为确定性实现，适合测试与 CI；内存队列不承诺跨进程持久化或
at-least-once，生产环境应替换成带 ack/可见性超时的消息系统。

## 架构

```text
Client ──POST /v1/jobs──> JobStore ──> asyncio.Queue
  │                                      │
  └──GET /v1/jobs/{id} <──状态/报告── Worker
                                          │
                              Planner / FakeLLM
                                          │
                   ACL ──> search_kb / mock fetch_url
                           write_note / finalize_report
                                          │
                     Budget + HITL + Memory filter + audit log
```

`finalize_report` 标记为高风险动作。Worker 到达该断点后把 Job 置为
`pending_human`；`POST /approve` 仅批准当前游标，恢复入队后继续执行。
名称 ACL、namespace 参数和 URL scheme/host 同时校验。日志只允许
`event/trace_id/job_id/status/tool/reason/namespace`，不记录 topic、完整
messages 或密钥。

## 启动与验证

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[dev]'
pytest
python eval/run_eval.py
uvicorn research_agent.api:app --reload
```

评测包含 6 个 case（引用、队列主题、材料缺口、安全拒绝、参数 ACL、预算），
并与 `eval/baseline.json` 比较。仅在确认整体改善后执行
`python eval/run_eval.py --write-baseline`。

## curl 演示

```bash
curl -sS -X POST http://127.0.0.1:8000/v1/jobs \
  -H 'content-type: application/json' \
  -d '{
    "topic": "Python Agent 安全",
    "namespace": "demo",
    "idempotency_key": "demo-001",
    "budget": {"max_steps": 8, "max_tool_calls": 8, "max_units": 4000}
  }'

curl -sS 'http://127.0.0.1:8000/v1/jobs/JOB_ID?namespace=demo'

curl -sS -X POST http://127.0.0.1:8000/v1/jobs/JOB_ID/approve \
  -H 'content-type: application/json' \
  -d '{"namespace":"demo"}'

curl -sS -X POST http://127.0.0.1:8000/v1/jobs/JOB_ID/revoke \
  -H 'content-type: application/json' \
  -d '{"namespace":"demo"}'
```

重复提交相同 namespace、`idempotency_key` 和请求内容会返回原 Job；同键但
内容不同返回 `409`。Job 有 TTL；读取过期 Job 会得到 `expired`，命名空间
purge API 可删除过期数据。revoke 支持单 Job 和整个命名空间，命名空间撤销后
拒绝新建 Job，并清理其 Memory。

## 状态与边界

- 正常：`queued → running → pending_human → queued → running → succeeded`
- 硬预算：`budget_exceeded`，并在 `error` 标明 `max_steps`、
  `max_tool_calls` 或 `max_units`
- 生命周期：`expired` / `revoked`；所有读取和变更均要求 namespace 匹配
- 报告：有材料时必须含 `Citations`；无材料时必须含“材料缺口”
- Memory：命中 prompt injection、系统提示词、密码/API Key 特征时拒写

本实现不使用 `BackgroundTasks`，也不声称进程内队列具备生产消息队列的可靠性。
