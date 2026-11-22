# 实战项目线

项目线与文档主线并行：学完相关模块后立刻做项目，用项目反哺「为什么要学」。

约定见 [`../CONVENTIONS.md`](../CONVENTIONS.md)（Python ≥ 3.11、FakeLLM、刻意简化清单）。

## 这一线是什么（也是什么不是）

| | 项目线（本目录） | 主线 `docs/` | 练习 `exercises/` |
|---|---|---|---|
| **产出** | 可安装/可演示的小系统 | 讲透知识点 | 验收题与答案思路 |
| **写法** | 规格：目标、目录、里程碑、验收、起步/易错 | 辅导：为什么→怎么写→跑一下→易错点 | 题目驱动 |
| **不要** | 把整章知识点再讲一遍 | 代替项目验收清单 | 代替端到端项目 |

细则回对应模块章节；本目录只保证「做什么、做到什么算过」。

## 项目列表

| # | 项目 | 建议时机 | 仓库状态 |
|---|------|----------|----------|
| 1 | [Python CLI 工具](./01-cli-tool.md) | 模块 01～03 后 | 实战说明 + 参考实现已齐 |
| 2 | [FastAPI Todo](./02-fastapi-todo.md) | 模块 05～07 核心后 | 实战说明 + 参考实现已齐 |
| 3 | [AI Chat](./03-ai-chat.md) | 模块 09 后 | 实战说明 + 参考实现已齐 |
| 4 | [RAG 知识库](./04-rag-kb.md) | 模块 10 后 | 实战说明 + 参考实现已齐 |
| 5 | [Tool Agent](./05-tool-agent.md) | 11 Tool/手写 Agent + 摘读 12 Eval/Security 后 | 实战说明 + 参考实现已齐 |
| 6 | [Research Agent](./06-research-agent.md) | 模块 11～12 后 | 实战说明 + 参考实现已齐 |

**六个参考实现均已存在**于 `playground/projects/`，各自独立 `pyproject.toml` 与 pytest（P4～P6 另含 eval）：

- [Project 1 CLI](../../playground/projects/01-cli-tool/)
- [Project 2 FastAPI Todo](../../playground/projects/02-fastapi-todo/)
- [Project 3 AI Chat](../../playground/projects/03-ai-chat/)
- [Project 4 RAG KB](../../playground/projects/04-rag-kb/)
- [Project 5 Tool Agent](../../playground/projects/05-tool-agent/)
- [Project 6 Research Agent](../../playground/projects/06-research-agent/)

两种「完成」不要混：

| 标记 | 含义 |
|------|------|
| 上表「仓库状态」 | 本仓库文档规格与参考实现是否齐备 |
| 各项目文档里的 `[ ]` 里程碑 / 验收 | **学习者自检清单**：完成自己的实现后再勾选；仓库已有参考实现也不代替勾选 |

「建议目录」是从零搭建的脚手架示例；学习者包名（常为 `app/`）可与参考实现包名（如 `cli_scanner` / `todo_api` / `ai_chat` / `rag_kb` / `tool_agent` / `research_agent`）不同，以各项目「参考实现」链接为准。

其他可跑入口： [Memory Store](../../playground/11-agent-core/memory/) · [Eval harness](../../playground/12-agent-production/evaluation/) · [专题总览](../topics/README.md)

## 建议节奏

```text
文档小章节 → 练习题 →（阶段性）项目里程碑
```

不要等「全部学完」再做项目。Project 6 刻意集成评测、观测与安全，作为主线收官。

每个项目文档结构统一为：目标 → 能力映射 → 需求 → 目录 → **起步建议** → 里程碑 → 验收 → **常见易错** → 延伸。

## 导航

- 返回总览：[../../README.md](../../README.md)
- 课程约定：[../CONVENTIONS.md](../CONVENTIONS.md)
