# 模块 11-agent-core：Agent 核心开发

> 状态：`六章正文与练习已全部完成` · 建议周期：4～6 周

## 模块目标

理解 Agent 本质，能手写并使用框架构建 Agent。

## 为什么现在学

这是课程主线的核心能力区：把 LLM、工具、记忆与编排收成可运行系统。先手写，再框架，避免只会调库。

## 章节目录

1. [Tool Calling](./01-tool-calling.md) · [练习](../../exercises/11-agent-core/01-tool-calling.md)
2. [手写一个 Agent](./02-handwritten-agent.md) · [练习](../../exercises/11-agent-core/02-handwritten-agent.md)
3. [Agent Memory](./05-agent-memory.md) · [练习](../../exercises/11-agent-core/05-agent-memory.md)
4. [Agent Framework 概览](./03-agent-frameworks.md) · [练习](../../exercises/11-agent-core/03-agent-frameworks.md)
5. [LangGraph 与工作流](./04-langgraph.md) · [练习](../../exercises/11-agent-core/04-langgraph.md)
6. [Multi-Agent](./06-multi-agent.md) · [练习](../../exercises/11-agent-core/06-multi-agent.md)

## 建议学习方式

1. 严格按上面的学习顺序：工具环 → 手写 Agent → 先补记忆边界 → 再谈框架与图。文件编号保持原样，避免既有链接失效
2. 全程可用 FakeLLM；有 Key 再换真模型
3. LangGraph 章抓思想，可用微型执行器代替库绑定
4. 多 Agent 默认克制，先证明单 Agent 不够再用；先自己写再对照文档
5. 完成 [Project 5 Tool Agent](../../playground/projects/05-tool-agent/README.md) 后，用
   [Project 6 Research Agent](../../playground/projects/06-research-agent/README.md)
   串起规划、工具、Memory 与人工审批

## 模块自检

- [ ] 能实现 tool calling、终止条件与副作用幂等重放
- [ ] 能手写 tool-loop Agent（ReAct 思想）并测 max_steps
- [ ] 能说明何时引入框架
- [ ] 能用图表达分支与循环
- [ ] 能设计短/长期记忆策略
- [ ] 能判断是否该上 Multi-Agent
- [ ] 能说明 MCP 何时只是 Registry 的 transport adapter（见 [决策地图](../topics/mcp.md)）

## 导航

- 返回总览：[../../README.md](../../README.md)
- 上一模块：[Embedding 与 RAG](../10-rag/README.md)
- 下一模块：[Agent 工程化与生产落地](../12-agent-production/README.md)
