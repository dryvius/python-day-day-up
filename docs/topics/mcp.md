# MCP 决策地图

> 定位：Model Context Protocol（MCP）的工程选型地图。工具执行、校验、幂等与 ACL 的 canonical 仍是 [Tool Calling](../11-agent-core/01-tool-calling.md)；本页不重复实现整章。

## 1. 先建立正确心智

MCP 解决的是「客户端如何发现并调用外部能力」的互操作协议，不会自动解决能力本身的安全、可靠性与业务语义。

```text
Agent Runtime
  → MCP client / transport
  → list_tools（发现菜单）
  → call_tool（结构化调用）
  → MCP server adapter
  → 你的 Tool Registry / 业务实现
```

- **发现**：`list_tools` 返回名称、描述、参数 Schema；这是动态菜单，不是授权证明。
- **调用**：`call_tool` 传名称与参数，返回内容或结构化错误；模型仍只提议，服务端才执行。
- **Transport**：stdio 适合本地子进程与桌面集成；HTTP 类 transport 适合远端、多实例与网关治理。Transport 只改变消息如何到达，不改变 ACL、幂等、超时和审计责任。
- **能力不只工具**：MCP 生态还可能暴露 resources / prompts；它们同样是不可信输入，不能升级为 system 权限。

## 2. 与自研 Registry 的关系

不要把 MCP server 做成第二套业务注册表。推荐：

```text
ToolSpec / Registry（canonical）
  ├─ 进程内 Agent executor
  ├─ HTTP adapter
  └─ MCP server adapter
```

Schema、参数模型、执行器、幂等记录和错误码只有一份；MCP adapter 只负责协议翻译。Project 5 的进程内 bridge 就采用这条边界：`list_tools` 从 Registry 导出，`call_tool` 仍回到同一个 ACL 执行入口。

反模式：

- MCP 与本地 Registry 各维护一份描述和校验模型；
- 因为 server 已经「列出工具」就跳过执行前授权；
- 把远端 server 返回的工具名直接加入所有用户菜单；
- transport 重连后重放写工具，却没有稳定 idempotency key。

## 3. 授权映射

MCP capability ≠ 业务 permission。授权必须把调用方身份映射到本地策略：

```text
authenticated principal
  → tenant / user / role / scopes
  → server allowlist
  → tool-name ACL
  → argument ACL（URL、路径、租户、资源归属）
  → human approval（高风险）
  → registry execution
```

身份来自可信接入层，不接受模型在 arguments 中自报 `tenant_id` 或 `role`。远端 MCP 使用 OAuth/API token 时，也要区分「能连 server」与「能为当前用户执行某工具」。拒绝应结构化回传并写脱敏审计。

## 4. 第三方 Server 是供应链依赖

接入前至少审查：

1. 来源、维护者、版本固定、发布签名与变更记录；
2. server 进程能读哪些环境变量、文件、凭证与宿主目录；
3. 默认出网范围、重定向、DNS/内网访问与数据外传面；
4. 工具 Schema 是否稳定，更新是否会静默扩大权限；
5. 日志、遥测、数据保留和跨境位置；
6. 超时、并发、结果大小、重试与副作用幂等语义；
7. kill switch、版本回退和审计可追踪性。

本地 stdio server 不是天然安全：它通常继承启动进程的环境与文件权限。远端 server 也不是天然隔离：它可能收到敏感参数和工具结果。最小权限运行，第三方默认无 secrets、无任意文件、无任意出网。

## 5. 何时上 / 何时不上

### 值得上

- 同一能力要被多个 MCP 客户端复用，互操作收益明确；
- 供应商只提供 MCP 接口，且经过供应链与权限评审；
- 工具目录动态变化，静态 SDK/Registry 同步成本已可度量；
- 已有稳定 Registry、ACL、审计、超时、幂等和隔离，MCP 只是适配层。

### 先不上

- 单进程、少量稳定工具；函数注册最清晰；
- 仍说不清工具副作用、参数 ACL 与租户身份来源；
- 为「生态兼容」复制第二套 Registry；
- 第三方 server 要求宿主机全盘、全环境变量或任意网络；
- 期待 MCP 自动解决注入、授权、沙箱、可靠重试或模型质量。

## 6. 上线检查

- [ ] ToolSpec / Schema / validator 单一来源
- [ ] `list_tools` 结果按调用方裁剪，而非全量暴露
- [ ] `call_tool` 执行前走名称 + 参数 ACL
- [ ] 写工具有稳定 idempotency key，重放返回同一结果
- [ ] transport 有 timeout、取消、并发上限、结果截断
- [ ] server 版本固定，权限与网络最小化，可一键禁用
- [ ] 第三方返回按不可信数据处理，不写入长期记忆
- [ ] allow/deny、server/version、tool、参数摘要进入审计

## 导航

- 工具执行 canonical：[Tool Calling](../11-agent-core/01-tool-calling.md)
- 安全 canonical：[Agent Security](../12-agent-production/03-security.md)
- 可运行参考：[Project 5](../../playground/projects/05-tool-agent/)
- 专题总览：[README](./README.md)
