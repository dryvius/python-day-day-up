# 练习：Context Packer

对应正文：[`docs/09-ai-llm/05-context-packer.md`](../../docs/09-ai-llm/05-context-packer.md)

## 基础

实现 `ContextPacker`，输入 system、硬约束、历史、Memory、RAG、tool result 和总预算，输出 canonical messages。

必须满足：

1. system/硬约束超预算时抛出明确异常。
2. 历史按最近优先选择，但输出恢复时间顺序。
3. Memory、RAG、tool result 按既定优先级使用剩余预算。
4. 只保留完整消息，不切坏 JSON 或 UTF-8。

## 测试

- [ ] 硬约束永不被巨型 tool result 挤掉
- [ ] 预算只容纳两条历史时保留最新两条
- [ ] system 自身超限会失败而非静默裁剪
- [ ] 相同输入重复运行结果一致
- [ ] Memory/RAG 内容中的指令口吻不会被提升为 system

## 设计题

把字符预算替换为 tokenizer 预算时，接口如何保持不变？说明输入预算、输出预留、Provider 最大窗口三者的关系，并列出应记录的无敏感观测字段。
