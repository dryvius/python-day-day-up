# Project 5：Tool Agent

离线可复现的异步 Tool Agent：FakeLLM 返回 assistant dict，运行时统一完成参数校验、名称与参数 ACL、错误回传、`max_steps`、副作用幂等和记忆污染拒写。进程内 `MCPBridge` 提供 `list_tools` / `call_tool`，但不会绕过 Registry 与 ACL。

## 运行

```bash
python -m venv .venv
.venv/bin/python -m pip install -e '.[dev]'
.venv/bin/pytest
.venv/bin/python eval/run_eval.py
```

无需 API Key 或网络。`.env.example` 仅记录未来接真实模型时的配置面。

## 试问与期望

- `计算 1+2*3`：调用 `calculator`，最终包含 `value: 7`。
- `搜索记忆 偏好`：调用租户隔离的 `search_memory`。
- viewer 输入 `记住偏好深色`：执行前被名称 ACL 拒绝。
- editor 输入含 `Ignore previous system prompt` 的记忆：工具可调用，但 Store 拒绝污染写入。

## 关键边界

- `ToolRegistry.execute` 是唯一执行入口：parse → ACL → Pydantic → idempotency → handler。
- `remember` 要求稳定 `idempotency_key`；同租户、同工具、同 key 回放同一结果。
- 身份与 `tenant_id` 来自调用方上下文，不允许模型通过参数覆盖。
- MCP bridge 只是 transport 形状，不是第二套授权或执行实现。
