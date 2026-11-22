# 课程约定（Conventions）

学习与写练习时默认遵守本页，避免版本/语义打架。

## 1. Python 版本

- **推荐：Python ≥ 3.11**（与 `pyproject` 示例、`TaskGroup`、`ExceptionGroup`、`TimeoutError` 别名一致）
- 可用 3.12（Dockerfile 示例用 `python:3.12-slim`）
- 注解写法默认 `list[str]`、`str | None`（勿再教 `List`/`Optional` 为唯一写法）

## 2. FakeLLM / LLMClient 约定

无 API Key 时：

- 用规则/关键词驱动的 FakeLLM 跑通工具环与评测
- **统一契约**（模块 09 起、项目线强制）：

```text
async def complete(
    messages: list[dict],
    tools: list[dict] | None = None,
    **kwargs,
) -> dict:  # assistant_message：至少含 role；常有 content / tool_calls
```

- 纯文本场景取 `message["content"]`，不要让 `complete` 直接返回 `str`
- 早期语言章可用 `EchoLLM.complete(prompt) -> str` 教学，**勿命名为 FakeLLM**
- 手写 Agent 教学可用同步 `def complete`；项目与生产偏好 `async`
- 单测与 CI **必须**可在 FakeLLM 下绿；真模型作为可选升级

## 3. 重点分级

| 标记 | 含义 |
|------|------|
| **必掌握** | 写透、必练、模块自检要会 |
| **建议掌握** | 明显提升质量，时间紧可后补 |
| **了解即可** | 建立地图，防止过载 |

## 4. 文档三线分工

| 路径 | 角色 | 默认读法 |
|------|------|----------|
| `docs/01～12` | 辅导正文（为什么 → 怎么写 → 跑一下 → 易错点） | 主线必读 |
| `docs/projects/` | 规格与验收（目标 / 里程碑 / 起步 / 易错） | 阶段性动手 |
| `docs/topics/` | 决策地图（何时上/不上进阶） | 主线门槛过了再读 |

细则在正文；项目线不重讲整章知识点；专题不代替 Memory / Eval 主线章。

### 工程主题 canonical 归属

为避免同一规范在多章漂移，工程主题以以下章节为准；其他章节只保留场景化摘要与链接：

| 主题 | Canonical 章节 |
|------|----------------|
| pytest 断言、fixture、Fake 单测 | [`03-engineering/03-testing.md`](./03-engineering/03-testing.md) |
| logging 配置、字段与脱敏 | [`03-engineering/04-logging.md`](./03-engineering/04-logging.md) |
| CLI 入口、退出码、参数解析 | [`03-engineering/05-cli-entrypoints.md`](./03-engineering/05-cli-entrypoints.md) |
| Git 分支/提交/回退、`.gitignore`、GitHub Actions 门禁 | [`03-engineering/06-git-ci.md`](./03-engineering/06-git-ci.md) |
| traceback、pdb/IDE、异步与 FastAPI 定位 | [`03-engineering/07-debugging.md`](./03-engineering/07-debugging.md) |
| FastAPI StreamingResponse、SSE framing、心跳/错误/断连 | [`06-web-backend/04-streaming-sse.md`](./06-web-backend/04-streaming-sse.md) |
| 会话/消息/job/日志/memory/vector 的保留、导出、软删、TTL、purge 与索引同步 | [`07-data-persistence/06-data-lifecycle.md`](./07-data-persistence/06-data-lifecycle.md) |
| 上下文优先级、预算与截断契约 | [`09-ai-llm/05-context-packer.md`](./09-ai-llm/05-context-packer.md) |
| Provider SSE delta / tool_calls 拼装 | [`09-ai-llm/02-llm-api.md`](./09-ai-llm/02-llm-api.md) |
| 工具副作用分级、幂等键、重试回放与补偿 | [`11-agent-core/01-tool-calling.md`](./11-agent-core/01-tool-calling.md) |
| MCP 发现/调用/transport、Registry 与供应链选型 | [`topics/mcp.md`](./topics/mcp.md) |

## 5. Agent 安全与观测硬约定

模块 11～12 与 Project 5/6 默认遵守：

- **工具执行前**调用 `authorize(role, tool, args)`（名称 + 参数级）；想调用 ≠ 允许执行；默认拒绝
- **观测字段允许列表**：默认不记录完整 `messages` / system prompt / API Key；`args` / 结果用摘要与截断
- **两种 harness 勿混**（详见 [`topics/agent-harness.md`](./topics/agent-harness.md)）：
  - **Eval harness**：题集 → 跑 Agent → 断言 → baseline（本课评测章默认指这个）
  - **Runtime harness**：tool-loop + ACL + 超时 + trace（业界口语常指这个）

## 6. 已知刻意简化（别当生产真理）

- Redis `LIST`+`BRPOP`：演示入队出队，**不是** at-least-once
- 提示分隔符：弱缓解，**不能**单独当注入防护
- LangGraph 玩具执行器：需用 reducer/append 语义；勿与库 API 一一对应
- FastAPI `BackgroundTasks`：轻量收尾，长任务请上队列
- 教学用 API Key `!=` 比较：生产应考虑恒定时间比较

更完整的知识点勘误会随修订直接改正文；本页只列「刻意简化」。

## 7. 仓库布局提醒

| 路径 | 用途 |
|------|------|
| `docs/` | 正文 |
| `docs/topics/` | 非主线专题（记忆工程进阶、Harness 总览等） |
| `exercises/` | 练习与验收 |
| `docs/projects/` | 阶段性项目 |
| `playground/` | 实验与可跑示例 |
| `playground/projects/` | Project 1～6 的完整参考实现（独立安装、测试） |

可跑入口：

- Memory：`playground/11-agent-core/memory/`
- Eval harness：`playground/12-agent-production/evaluation/`
- Project 1：`playground/projects/01-cli-tool/`
- Project 2：`playground/projects/02-fastapi-todo/`
- Project 3：`playground/projects/03-ai-chat/`
- Project 4：`playground/projects/04-rag-kb/`
- Project 5：`playground/projects/05-tool-agent/`
- Project 6：`playground/projects/06-research-agent/`

## 导航

- 返回总览：[../README.md](../README.md)
- 项目线：[projects/README.md](./projects/README.md)
- 专题：[topics/README.md](./topics/README.md)
