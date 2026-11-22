# PythonDayDayUp

> 从 Python 扎实基本功，走到能独立开发 Agent，并对现阶段 AI 常用概念有较深入认知。

本仓库是一套**循序渐进的 Markdown 学习文档 + 独立练习题**，内容骨架基于
[Python → Agent 学习路线分享](https://chatgpt.com/share/6acf680e-f448-83ea-8d57-fd52d62e6aac)
整理与重组。

当前进度：**模块 01～12 正文与练习已齐；Project 1～6 的实战说明与可运行参考实现均已齐。** 建议先按项目规格独立完成，再对照参考实现，并用 FakeLLM + pytest/CI 保证可测。

**环境约定：Python ≥ 3.11**（详见 [`docs/CONVENTIONS.md`](docs/CONVENTIONS.md)）。

---

## 这个文件夹是干什么的？

| 路径 | 用途 |
|------|------|
| `README.md`（本文件） | 总览：目标、用法、目录、学成标准 |
| `docs/` | 学习正文（大模块 → 小章节） |
| `docs/CONVENTIONS.md` | 版本、FakeLLM、刻意简化等全局约定 |
| `docs/topics/` | 非主线专题（记忆工程、Agent Harness、MCP 决策地图） |
| `docs/projects/` | 阶段性实战项目说明 |
| `exercises/` | 每章课后练习（与正文分离） |
| `playground/` | 实验代码、可跑最小示例与六个项目参考实现 |
| `playground/projects/` | Project 1～6 的独立可运行参考实现 |
| `interview/` | 面试题与答题笔记（与正文/练习分离） |

---

## 最终学习成就

学完后，期望你具备的不是“会调某个框架 API”，而是：

```
Python                 ★★★★★
Software Engineering   ★★★★
Backend Engineering    ★★★★
Database               ★★★★
Network / OS           ★★★
LLM                    ★★★★
RAG                    ★★★★★
Agent                  ★★★★★
System Design          ★★★★
```

也就是说，你要成为：

> **具备完整服务端基础的 AI Full-Stack / Agent Engineer**

即使未来某个 Agent 框架消失，你仍然掌握：

> **Programming + Backend + System + AI Engineering**

---

## 学习目的（为什么这样设计）

1. **Python 精通**：语法 → 高级特性 → 工程化，而不是停留在脚本级。
2. **后端不再一知半解**：补齐异步、HTTP、数据库、缓存、部署与架构直觉。
3. **Agent 可独立开发**：Tool Calling → 手写 Agent → 工作流 → Multi-Agent → 生产化。
4. **AI 认知扎实**：对 Token、Context、RAG、Agent、Embedding 等名词有工程级理解。

刻意**不走**「NumPy → 深度学习 → 训练大模型」长线；主线是：

```
Python → 工程化 → 异步 → 后端 → 数据库
      → LLM API → RAG → Tool Calling → Agent → 生产化
```

---

## 怎么用（推荐节奏）

### 单章循环

```
读 docs 章节（先吃透「必掌握」）
        ↓
做 exercises 同名练习
        ↓
勾选自检清单
        ↓
进入下一章
```

### 三条并行线（很重要）

不要完全串行学完再做项目：

```
主线：工程开发（docs 01→12）
基础线：系统直觉（尤其模块 04、08）
项目线：实战（docs/projects）
```

- 文档解释项目里的「为什么」
- 项目解释文档里的「学了有什么用」

### 内容难度策略

本教程采用 **「重点优先的完整教程」**：

- **必掌握**：写透，必须练
- **建议掌握**：够用就学，能明显提升代码质量
- **了解即可**：建立地图，防止概念过载、影响兴趣

---

## 大模块总览

### 01-python-basics · Python 语言基础

- **目标**：能用 Python 写正常程序，而不是只会零散脚本。
- **周期**：2.5～3.5 周
- **导读**：[`docs/01-python-basics/README.md`](docs/01-python-basics/README.md)
- **章节**：
  - [语法与数据结构](docs/01-python-basics/01-syntax-basics.md) · [练习](exercises/01-python-basics/01-syntax-basics.md)
  - [函数与作用域](docs/01-python-basics/02-functions-scope.md) · [练习](exercises/01-python-basics/02-functions-scope.md)
  - [模块、包与导入系统](docs/01-python-basics/03-modules-packages.md) · [练习](exercises/01-python-basics/03-modules-packages.md)

### 02-advanced-python · Python 高级特性与类型系统

- **目标**：建立 Python 内功，能读现代框架源码里的抽象。
- **周期**：5～7 周
- **导读**：[`docs/02-advanced-python/README.md`](docs/02-advanced-python/README.md)
- **章节**：
  - [面向对象编程](docs/02-advanced-python/01-oop.md) · [练习](exercises/02-advanced-python/01-oop.md)
  - [Python 数据模型](docs/02-advanced-python/02-data-model.md) · [练习](exercises/02-advanced-python/02-data-model.md)
  - [异常系统](docs/02-advanced-python/06-exception-system.md) · [练习](exercises/02-advanced-python/06-exception-system.md)
  - [Iterator / Generator](docs/02-advanced-python/03-iterator-generator.md) · [练习](exercises/02-advanced-python/03-iterator-generator.md)
  - [装饰器](docs/02-advanced-python/04-decorator.md) · [练习](exercises/02-advanced-python/04-decorator.md)
  - [上下文管理器](docs/02-advanced-python/05-context-manager.md) · [练习](exercises/02-advanced-python/05-context-manager.md)
  - [类型系统](docs/02-advanced-python/07-typing-system.md) · [练习](exercises/02-advanced-python/07-typing-system.md)

### 03-engineering · Python 工程化

- **目标**：从“会写 Python”进入“会用 Python 做项目”。
- **周期**：3～4 周
- **导读**：[`docs/03-engineering/README.md`](docs/03-engineering/README.md)
- **章节**：
  - [项目结构](docs/03-engineering/01-project-structure.md) · [练习](exercises/03-engineering/01-project-structure.md)
  - [依赖与虚拟环境](docs/03-engineering/02-deps-venv.md) · [练习](exercises/03-engineering/02-deps-venv.md)
  - [测试（pytest）](docs/03-engineering/03-testing.md) · [练习](exercises/03-engineering/03-testing.md)
  - [Logging](docs/03-engineering/04-logging.md) · [练习](exercises/03-engineering/04-logging.md)
  - [CLI 入口与参数解析](docs/03-engineering/05-cli-entrypoints.md) · [练习](exercises/03-engineering/05-cli-entrypoints.md)
  - [Git 协作与 CI 门禁](docs/03-engineering/06-git-ci.md) · [练习](exercises/03-engineering/06-git-ci.md)
  - [调试与故障定位](docs/03-engineering/07-debugging.md) · [练习](exercises/03-engineering/07-debugging.md)

### 04-systems-basics · 计算机与服务端基础

- **目标**：补齐前端背景下的系统直觉，避免一知半解。
- **周期**：2.5～3.5 周
- **导读**：[`docs/04-systems-basics/README.md`](docs/04-systems-basics/README.md)
- **章节**：
  - [操作系统基础](docs/04-systems-basics/01-os-basics.md) · [练习](exercises/04-systems-basics/01-os-basics.md)
  - [网络与 HTTP](docs/04-systems-basics/02-network-http.md) · [练习](exercises/04-systems-basics/02-network-http.md)
  - [并发模型](docs/04-systems-basics/03-concurrency-models.md) · [练习](exercises/04-systems-basics/03-concurrency-models.md)
  - [数据结构与算法精要](docs/04-systems-basics/04-dsa-essentials.md) · [练习](exercises/04-systems-basics/04-dsa-essentials.md)

### 05-async-python · Python 异步编程

- **目标**：掌握 asyncio，跨过 Agent 开发分水岭。
- **周期**：1.5～2.5 周
- **导读**：[`docs/05-async-python/README.md`](docs/05-async-python/README.md)
- **章节**：
  - [asyncio 基础](docs/05-async-python/01-asyncio-fundamentals.md) · [练习](exercises/05-async-python/01-asyncio-fundamentals.md)
  - [asyncio 进阶实践](docs/05-async-python/02-asyncio-advanced.md) · [练习](exercises/05-async-python/02-asyncio-advanced.md)

### 06-web-backend · Web 后端

- **目标**：能独立搭建并理解后端 API 服务。
- **周期**：2～3 周
- **导读**：[`docs/06-web-backend/README.md`](docs/06-web-backend/README.md)
- **章节**：
  - [Web 框架原理](docs/06-web-backend/01-web-framework-principles.md) · [练习](exercises/06-web-backend/01-web-framework-principles.md)
  - [FastAPI + Pydantic](docs/06-web-backend/02-fastapi-pydantic.md) · [练习](exercises/06-web-backend/02-fastapi-pydantic.md)
  - [认证与授权](docs/06-web-backend/03-auth.md) · [练习](exercises/06-web-backend/03-auth.md)
  - [StreamingResponse 与 SSE](docs/06-web-backend/04-streaming-sse.md) · [练习](exercises/06-web-backend/04-streaming-sse.md)

### 07-data-persistence · 数据库与数据持久化

- **目标**：掌握 SQL/ORM/缓存/队列的工程用法与取舍。
- **周期**：3～4 周
- **导读**：[`docs/07-data-persistence/README.md`](docs/07-data-persistence/README.md)
- **章节**：
  - [SQL 基础](docs/07-data-persistence/01-sql.md) · [练习](exercises/07-data-persistence/01-sql.md)
  - [PostgreSQL](docs/07-data-persistence/02-postgresql.md) · [练习](exercises/07-data-persistence/02-postgresql.md)
  - [Python ORM](docs/07-data-persistence/03-orm.md) · [练习](exercises/07-data-persistence/03-orm.md)
  - [缓存与 Redis](docs/07-data-persistence/04-redis-cache.md) · [练习](exercises/07-data-persistence/04-redis-cache.md)
  - [消息队列基础](docs/07-data-persistence/05-message-queue.md) · [练习](exercises/07-data-persistence/05-message-queue.md)
  - [数据生命周期](docs/07-data-persistence/06-data-lifecycle.md) · [练习](exercises/07-data-persistence/06-data-lifecycle.md)

### 08-devops-architecture · 部署、运维与软件架构

- **目标**：具备把服务跑起来、拆清楚边界的能力。
- **周期**：2～3 周
- **导读**：[`docs/08-devops-architecture/README.md`](docs/08-devops-architecture/README.md)
- **章节**：
  - [Linux 基础](docs/08-devops-architecture/01-linux-basics.md) · [练习](exercises/08-devops-architecture/01-linux-basics.md)
  - [Docker 与部署](docs/08-devops-architecture/02-docker-deploy.md) · [练习](exercises/08-devops-architecture/02-docker-deploy.md)
  - [软件架构基础](docs/08-devops-architecture/03-software-architecture.md) · [练习](exercises/08-devops-architecture/03-software-architecture.md)

### 09-ai-llm · AI / LLM 基础与认知地图

- **目标**：对现阶段 AI 发展与常用名词建立较深入认知，并能调用 LLM。
- **周期**：2.5～3.5 周
- **导读**：[`docs/09-ai-llm/README.md`](docs/09-ai-llm/README.md)
- **章节**：
  - [AI 发展脉络与名词词典](docs/09-ai-llm/01-ai-landscape-glossary.md) · [练习](exercises/09-ai-llm/01-ai-landscape-glossary.md)
  - [LLM API 实战](docs/09-ai-llm/02-llm-api.md) · [练习](exercises/09-ai-llm/02-llm-api.md)
  - [Prompt Engineering](docs/09-ai-llm/03-prompt-engineering.md) · [练习](exercises/09-ai-llm/03-prompt-engineering.md)
  - [Structured Output](docs/09-ai-llm/04-structured-output.md) · [练习](exercises/09-ai-llm/04-structured-output.md)
  - [Context Packer：优先级、预算与截断](docs/09-ai-llm/05-context-packer.md) · [练习](exercises/09-ai-llm/05-context-packer.md)

### 10-rag · Embedding 与 RAG

- **目标**：能构建可用的知识库问答系统，并理解失败原因。
- **周期**：2～3 周
- **导读**：[`docs/10-rag/README.md`](docs/10-rag/README.md)
- **章节**：
  - [Embedding 与向量检索](docs/10-rag/01-embedding-vector-search.md) · [练习](exercises/10-rag/01-embedding-vector-search.md)
  - [RAG 架构](docs/10-rag/02-rag-architecture.md) · [练习](exercises/10-rag/02-rag-architecture.md)
  - [RAG 实战与调优](docs/10-rag/03-rag-practice.md) · [练习](exercises/10-rag/03-rag-practice.md)

### 11-agent-core · Agent 核心开发

- **目标**：理解 Agent 本质，能手写并使用框架构建 Agent。
- **周期**：4～6 周
- **导读**：[`docs/11-agent-core/README.md`](docs/11-agent-core/README.md)
- **章节**：
  - [Tool Calling](docs/11-agent-core/01-tool-calling.md) · [练习](exercises/11-agent-core/01-tool-calling.md)
  - [手写一个 Agent](docs/11-agent-core/02-handwritten-agent.md) · [练习](exercises/11-agent-core/02-handwritten-agent.md)
  - [Agent Memory](docs/11-agent-core/05-agent-memory.md) · [练习](exercises/11-agent-core/05-agent-memory.md)
  - [Agent Framework 概览](docs/11-agent-core/03-agent-frameworks.md) · [练习](exercises/11-agent-core/03-agent-frameworks.md)
  - [LangGraph 与工作流](docs/11-agent-core/04-langgraph.md) · [练习](exercises/11-agent-core/04-langgraph.md)
  - [Multi-Agent](docs/11-agent-core/06-multi-agent.md) · [练习](exercises/11-agent-core/06-multi-agent.md)

### 12-agent-production · Agent 工程化与生产落地

- **目标**：具备评测、可观测、安全与系统设计能力，接近生产级。
- **周期**：3～4 周
- **导读**：[`docs/12-agent-production/README.md`](docs/12-agent-production/README.md)
- **章节**：
  - [Agent Evaluation](docs/12-agent-production/01-evaluation.md) · [练习](exercises/12-agent-production/01-evaluation.md)
  - [Observability](docs/12-agent-production/02-observability.md) · [练习](exercises/12-agent-production/02-observability.md)
  - [Agent Security](docs/12-agent-production/03-security.md) · [练习](exercises/12-agent-production/03-security.md)
  - [Agent 系统设计](docs/12-agent-production/04-system-design.md) · [练习](exercises/12-agent-production/04-system-design.md)


---

## 实战项目线

1. [Project 1：Python CLI 工具](docs/projects/01-cli-tool.md) · [运行参考实现](playground/projects/01-cli-tool/)
2. [Project 2：FastAPI Todo](docs/projects/02-fastapi-todo.md) · [运行参考实现](playground/projects/02-fastapi-todo/)
3. [Project 3：AI Chat](docs/projects/03-ai-chat.md) · [运行参考实现](playground/projects/03-ai-chat/)
4. [Project 4：RAG 知识库](docs/projects/04-rag-kb.md) · [运行参考实现](playground/projects/04-rag-kb/)
5. [Project 5：Tool Agent](docs/projects/05-tool-agent.md) · [运行参考实现](playground/projects/05-tool-agent/)
6. [Project 6：Research Agent](docs/projects/06-research-agent.md) · [运行参考实现](playground/projects/06-research-agent/)

项目导读：[`docs/projects/README.md`](docs/projects/README.md)

六个参考实现均已落在 `playground/projects/`（独立安装与测试）。项目文档里的里程碑 / 验收 `[ ]` 是**学习者自检清单**，与仓库「规格 + 参考实现已齐」不是同一回事——参考实现存在也不代替学习者勾选。

---

## 建议时间表（含练习、项目与缓冲）

下表是**日历工期**，按每周约 9 个有效学习小时（约 1.5 小时 × 6 天）并预留
20%～30% 环境排障、返工与复习缓冲。章内“建议学时”只代表净学习时间，不能直接当日历周期。

| 阶段 | 内容 | 建议日历工期 | 阶段门禁 |
|------|------|--------------|----------|
| 语言底座 | 01 | 2.5～3.5 周 | 基础题通过，可独立拆函数与模块 |
| 高级 Python | 02 | 5～7 周 | 必掌握练习通过；能解释异常与类型边界 |
| 工程化交付 | 03 + Project 1 | 4～6 周 | CLI 可安装、Fake/pytest CI 绿、能按 traceback 定位 |
| 系统直觉 | 04 | 2.5～3.5 周 | 完成超时/重试微设计；DSA 可后补 |
| 后端基础 | 05 | 1.5～2.5 周 | 异步并发、限流与超时实验通过 |
| Web 与数据 | 06～07 + Project 2 | 6～9 周 | Todo API、持久化、鉴权与测试通过 |
| 部署架构 | 08 | 2～3 周 | Project 2 可用 compose 启动并排障 |
| LLM 应用 | 09 + Project 3 | 3.5～5 周 | FakeLLM/真模型至少一路可重复运行 |
| RAG | 10 + Project 4 | 3.5～5 周 | MiniRAG + 题集评测 + 失败分析 |
| Agent 核心 | 11 + Project 5 | 5～7 周 | tool-loop、终止条件、ACL 与最小 eval |
| 生产化收官 | 12 + Project 6 | 4～6 周 | Fake 全链路、trace、评测、安全与设计评审 |

路线预期：

- **压缩路线**：已有编程基础、每天稳定接近 2 小时，只做必掌握 + 基础题 + 项目 M1/M2，约 **7～8 个月**
- **标准路线**：每天 1～2 小时，完成主线练习与 6 个项目，约 **9～13 个月**
- **深度路线**：补齐进阶/挑战、专题、完整部署与项目返工，约 **12～18 个月**

每连续完成两个高负荷阶段，安排半周只复习、补测试和整理错题。是否进入下一阶段，以练习通过线和项目验收为准，不以“读完文档”为准。

---

## 从哪里开始？

1. 打开 [`docs/01-python-basics/README.md`](docs/01-python-basics/README.md)
2. 学习第一章 [`docs/01-python-basics/01-syntax-basics.md`](docs/01-python-basics/01-syntax-basics.md)
3. 完成练习 [`exercises/01-python-basics/01-syntax-basics.md`](exercises/01-python-basics/01-syntax-basics.md)

---

## 当前仓库状态

- [x] 总览文档
- [x] 全部大模块目录
- [x] 全部小章节骨架
- [x] 全部练习题骨架
- [x] 项目线骨架
- [x] 第一章正文与练习：`docs/01-python-basics/01-syntax-basics.md`
- [x] 第二章正文与练习：`docs/01-python-basics/02-functions-scope.md`
- [x] 第三章正文与练习：`docs/01-python-basics/03-modules-packages.md`（模块 01 完成）
- [x] 模块 02 第一章：`docs/02-advanced-python/01-oop.md`
- [x] 模块 02 第二章：`docs/02-advanced-python/02-data-model.md`
- [x] 模块 02 第三章：`docs/02-advanced-python/03-iterator-generator.md`
- [x] 模块 02 第四章：`docs/02-advanced-python/04-decorator.md`
- [x] 模块 02 第五章：`docs/02-advanced-python/05-context-manager.md`
- [x] 模块 02 第六章：`docs/02-advanced-python/06-exception-system.md`
- [x] 模块 02 第七章：`docs/02-advanced-python/07-typing-system.md`（模块 02 完成）
- [x] 模块 03 全七章：`docs/03-engineering/`（项目结构 / 依赖 / pytest / logging / CLI / Git+CI / 调试）
- [x] 模块 04 全四章：`docs/04-systems-basics/`（OS / HTTP / 并发 / DSA 精要）
- [x] 模块 05 全两章：`docs/05-async-python/`（asyncio 基础 / 进阶）
- [x] 模块 06 全四章：`docs/06-web-backend/`（框架原理 / FastAPI+Pydantic / 认证 / Streaming SSE）
- [x] 模块 07 全六章：`docs/07-data-persistence/`（SQL / PG / ORM / Redis / 队列 / 数据生命周期）
- [x] 模块 08 全三章：`docs/08-devops-architecture/`（Linux / Docker / 架构）
- [x] 模块 09 全五章：`docs/09-ai-llm/`（名词 / API / Prompt / Structured Output / Context Packer）
- [x] 模块 10 全三章：`docs/10-rag/`（Embedding / 架构 / 实战调优）
- [x] 模块 11 全六章：`docs/11-agent-core/`（Tool/手写 Agent/Memory/框架/图/Multi）
- [x] 模块 12 全四章：`docs/12-agent-production/`（评测 / 可观测 / 安全 / 系统设计）
- [x] 全部 12 个大模块正文与练习已填充
- [x] 课程约定：`docs/CONVENTIONS.md`
- [x] 项目线 Project 1～6 实战说明已填充
- [x] 审查后勘误：队列语义、Redis 限流、LangGraph 合并、注入弱缓解、`gather` vs `TaskGroup` 等
- [x] 二次审查修订：统一 FakeLLM/`complete` 契约；FastAPI 生命周期顺序；ORM 异步阻塞警告；OS→GIL 链接；RBAC 角色/权限；RAG 间接注入与 chunk 单位；ReAct→tool-loop 命名；TaskGroup 示例；HTTP 超时分层等
- [x] 深度补强：LLM 流式 SSE 解析与 `tool_calls` 拼装；Agent Evaluation 最小 harness（jsonl → 报表 → baseline）
- [x] 文档加深：Observability 允许列表/成本；参数级工具 ACL；并行 tool 失败语义；Memory 三层；Multi-Agent 护栏；Hybrid RRF；AsyncSession 片段
- [x] 记忆/Harness：主线加深 + `docs/topics/` 专题；可跑 `playground/11-agent-core/memory/` 与 `playground/12-agent-production/evaluation/`
- [x] 六个项目在 `playground/projects/` 下的完整参考实现（独立 pyproject、pytest；P4～P6 含 eval）

---

## 来源与说明

- 路线参考：[ChatGPT 分享 · Python 到 Agent 学习路线](https://chatgpt.com/share/6acf680e-f448-83ea-8d57-fd52d62e6aac)
- 全局约定与刻意简化清单：[docs/CONVENTIONS.md](docs/CONVENTIONS.md)
- 文档以可练习、可演进为主；框架 API 以思想为准，实现细节以你安装的版本文档为准。
