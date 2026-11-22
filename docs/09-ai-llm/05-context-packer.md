# Context Packer：优先级、预算与截断

> 所属模块：`09-ai-llm` · 对应练习：[`exercises/09-ai-llm/05-context-packer.md`](../../exercises/09-ai-llm/05-context-packer.md)

## 学习目标

把 system/硬约束、历史、Memory、RAG、tool result 装配为可测试的模型输入，并明确预算不足时谁先保留、谁先丢弃。

## 1. 为什么需要独立 Packer

上下文不是把所有字符串 `append` 到窗口。来源的信任级别、生命周期和可截断性不同；若分散在路由、Agent 和 Provider 客户端中临时裁剪，同一请求会得到不可解释的结果。

`ContextPacker` 的输入是已分类消息，输出是 canonical `messages`。它不负责检索、写 Memory、调用工具或解析 Provider 流。

## 2. 优先级契约

默认优先级从高到低：

1. **system + 硬约束**：安全、工具 ACL、输出契约；不可静默截断。
2. **当前请求与最近历史**：保证本轮意图与近轮指代；历史按“新消息优先”截断。
3. **Memory**：少量、按用户隔离、带来源标签，不可覆盖系统规则。
4. **RAG**：检索片段，先在检索层 Top-K，再按预算裁剪。
5. **tool result**：只保留当前步骤需要的结构化摘要；原始大 JSON/HTML 优先丢弃。

注意：优先级描述的是**预算分配**，不强制最终消息的展示顺序。最终顺序通常为 system/约束 → Memory/RAG/工具材料 → 按时间排序的历史与当前请求。

## 3. 预算契约

生产应使用目标模型 tokenizer；教学项目可使用字符数作为确定性近似，但必须把预算器封装起来以便替换。

```text
总预算
- 预留输出预算
- system 与硬约束实际成本
= 可分配输入预算
```

硬规则：

- system/硬约束自身超预算：**立即失败**并修配置，不能截成半条安全规则。
- 任何单条内容不得按字节盲切，避免破坏 UTF-8、JSON 或 tool call 结构。
- 历史按完整消息截断，保留最近消息且维持时间顺序。
- Memory/RAG/tool result 在进入 Packer 前应有来源级上限；Packer 再做全局二次门禁。
- 输出需可观测：记录各分区条数/估算 token、被丢弃数量，不记录完整敏感内容。

## 4. 截断示例

```python
packed = packer.pack(
    system=system,
    hard_constraints=constraints,
    history=history,
    memory=memory_hits,
    rag=rag_chunks,
    tool_results=tool_summaries,
)
```

预算不足时：

1. 锁定 system/硬约束；
2. 从历史尾部向前选完整消息；
3. 依次给 Memory、RAG、tool result 分配剩余预算；
4. 输出时恢复历史时间顺序。

实际产品可为 RAG 或 tool result 设置动态配额，但必须把变更写进契约和测试，不能依赖列表偶然顺序。

## 5. 信任边界

- Memory 与 RAG 都是**数据**，不是 system 指令；外部文本中的“忽略之前指令”无权提升优先级。
- tool result 可能来自不可信网页，应先结构化、截断、标来源。
- 硬约束必须由应用代码提供，不能由用户字段声明自己是“高优先级”。
- Context Packer 只决定纳入哪些内容；Memory 写入过滤见 [Agent Memory](../11-agent-core/05-agent-memory.md)。

## 6. 必测不变量

- system 与硬约束永远完整保留，超预算时显式失败。
- 最近一条用户消息在合法配置下必定保留。
- 旧历史先于新历史被淘汰，输出仍按时间顺序。
- 低优先级巨型 tool result 不能挤掉硬约束。
- 同一输入和预算得到确定性输出。

可运行参考：[Project 3 的 `ContextPacker`](../../playground/projects/03-ai-chat/ai_chat/context.py)。

## 导航

- 返回模块：[README](./README.md)
- 上一章：[Structured Output](./04-structured-output.md)
- 练习：[05-context-packer.md](../../exercises/09-ai-llm/05-context-packer.md)
- 延伸：[Agent Memory](../11-agent-core/05-agent-memory.md)
