# Project 5：Tool Agent

> 状态：`实战说明 + 参考实现已齐`（仓库参考实现：[`playground/projects/05-tool-agent/`](../../playground/projects/05-tool-agent/)）
> 建议时机：完成模块 11 的 Tool Calling + 手写 Agent，并摘读模块 12 的 Evaluation / Security「必掌握」后
> 建议工时：12～20 小时
> 推荐目录：`playground/projects/05-tool-agent/`
> 运行环境：Python ≥ 3.11 · FakeLLM 契约见 [`../CONVENTIONS.md`](../CONVENTIONS.md)
> 说明：下文里程碑 / 验收中的 `[ ]` 是**学习者自检清单**，不因仓库已有参考实现而预先勾选。

## 项目目标

手写 tool-loop Agent（ReAct 思想）：工具注册、执行回传、`max_steps`、错误回传、ACL；FakeLLM 可单测。

## 你将练习到的能力

| 模块 | 知识点 |
|------|--------|
| 11 | Tool schema、执行环、终止条件、手写 Agent |
| 09 | Structured args / Pydantic 校验 |
| 06/12 | API 封装、工具权限（名称 + 参数） |

## 需求概述

### 功能

1. 至少 3 个工具，例如：`calculator`、`get_time`、`search_memory`（内存字典假检索）
2. Agent：`run(user_input) -> final_answer`；内部保留 `messages` 与 `trace: list[dict]`
3. `max_steps` 触顶有明确结束语/错误状态
4. 未知工具名、非法 JSON 参数 → 结构化错误回传给模型或中止
5. 可选：`POST /v1/agent/run`
6. 副作用工具使用稳定 idempotency key；同 key 重放返回同一结果，不重复写入
7. 进程内 MCP 风格 bridge 提供 `list_tools` / `call_tool`，调用仍走同一 Registry 与 ACL

### 非功能

- FakeLLM：按用户句中关键词决定是否发 `tool_calls`；**`complete` → assistant dict**（非 `str`）
- 工具执行前 ACL：**工具名 + 参数级**（至少对假想危险路径/URL 做拒绝样例，即使默认不注册 shell）
- `search_memory` 走写入过滤（可复用 [`playground/11-agent-core/memory/`](../../playground/11-agent-core/memory/)）
- 单测不依赖外网；建议接上最小 eval（对齐模块 12 harness 字段）
- Memory Store 在项目内自包含，按租户隔离并拒绝提示注入/密钥类污染写入

## 建议目录

```text
playground/projects/05-tool-agent/
├── src/tool_agent/
│   ├── __init__.py
│   └── core.py              # runtime / registry / ACL / memory / MCP bridge
├── eval/                    # 可从 playground/12-.../evaluation 改编
│   ├── cases.jsonl
│   ├── baseline.json
│   └── run_eval.py
├── tests/test_tool_agent.py
├── pyproject.toml
└── README.md
```

## 起步建议（第一天）

1. 抄/对照模块 11 最小 Agent：`FakeLLM` 三条路径（要工具 / 不要工具 / 工具后收尾）
2. 先只挂 `calculator`，pytest 绿后再加多工具与 `max_steps`
3. `authorize(role, tool, args)` 插在 `registry[name](**args)` **之前**；再接 eval

### 分段实施，避免前置倒挂

1. 完成模块 11 的 Tool Calling + 手写 Agent 后，先做 **M1～M2**。
2. 摘读 Evaluation 的最小 harness 与 Security 的参数级 ACL 后，再做 **M3～M4**。
3. 不要求先学完整模块 12；Observability 与系统设计留给 Project 6 收官。

必读章节：

- [Tool Calling](../11-agent-core/01-tool-calling.md)
- [手写 Agent](../11-agent-core/02-handwritten-agent.md)
- [Agent Security · 参数级 ACL](../12-agent-production/03-security.md)
- [Evaluation · harness](../12-agent-production/01-evaluation.md)

## 里程碑

- [x] **M1**：单工具环跑通（算数题）
- [x] **M2**：多工具 + max_steps + 非法参数恢复
- [x] **M3**：ACL（名 + 参）测试；轨迹可打印；MCP bridge 不绕过 ACL
- [x] **M4**：`eval/run_eval.py` Fake 全绿；含 safety；记忆污染不得写入

## 验收标准

- [x] Fake 路径下 pytest 全绿；`complete` 返回 assistant dict
- [x] 触顶步数有测试
- [x] 工具参数经 Pydantic 校验；ACL 拒绝有测试
- [x] 副作用幂等与 MCP bridge 有测试
- [x] 评测可一键跑并与 baseline 比较
- [x] README 给出示范问题与期望行为

## 参考实现运行

```bash
cd playground/projects/05-tool-agent
python -m venv .venv
.venv/bin/python -m pip install -e '.[dev]'
.venv/bin/pytest
.venv/bin/python eval/run_eval.py
```

## 常见易错

| 坑 | 正确做法 |
|----|----------|
| FakeLLM 返回 `str` | assistant dict + 可选 `tool_calls` |
| 只白名单工具名 | 再审 `args`（路径 / URL / 租户） |
| ACL 写在执行之后 | 副作用已发生；必须在 registry 前 |
| 工具错误直接抛崩 | 结构化错误回传 messages，让模型改参 |
| `trace` 与 `messages` 混用 | 事件流单独存，便于 `check_trace` |
| 无 safety case | eval 至少 1 条禁工具 / 注入样例 |

## 延伸挑战

- 并行 tool_calls + Semaphore
- 把 Project 4 的检索挂成 `search_kb` 工具
- 简单 `trace_id` 贯穿日志（对接观测章字段允许列表）

## 导航

- 返回项目列表：[./README.md](./README.md)
- 相关文档：[Tool Calling](../11-agent-core/01-tool-calling.md) · [手写 Agent](../11-agent-core/02-handwritten-agent.md) · [Memory](../11-agent-core/05-agent-memory.md) · [Evaluation](../12-agent-production/01-evaluation.md) · [Security](../12-agent-production/03-security.md)
- 下一项目：[Research Agent](./06-research-agent.md)
- 返回总览：[../../README.md](../../README.md)
