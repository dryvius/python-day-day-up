# 练习：数据生命周期

> 对应文档：[`docs/07-data-persistence/06-data-lifecycle.md`](../../docs/07-data-persistence/06-data-lifecycle.md)  
> 建议用时：90～150 分钟

## 基础题（必做）

### B1. 生命周期矩阵

为会话、消息、job、日志、memory、vector 各写一行：真源、owner、保留期、软删恢复窗、硬删方式、导出范围、下游副本。

**验收**：六类齐全；期限有理由，不使用“永久保留”逃避设计。

### B2. 软删查询

为 `chat_sessions` 增加 `deleted_at`，写出：软删、恢复、只查活跃数据、按到期时间分批选择 1000 行的 SQL，并设计必要索引。

**验收**：默认查询排除已删；purge 有稳定顺序和批量上限。

### B3. 导出契约

设计异步导出 job 的状态机和 JSONL manifest，写清鉴权范围、快照时点、下载 URL TTL、导出包何时销毁。

**验收**：不会导出他租户、密钥或内部安全日志；失败可重试。

## 进阶题

### A1. 幂等 purge

实现一个 SQLite/Python 小脚本：按 `expires_at` 每批删除最多 100 行，重复运行结果一致；输出 eligible/deleted 计数。

### A2. 索引同步

画出“源文档删除 → outbox → vector consumer → 对账”的状态机，并为 consumer 设计幂等键。列出以下故障的恢复方式：

1. DB 已提交，worker 尚未消费；
2. vector 已删，ack 前崩溃；
3. 权限已变，旧 chunk 暂未删除；
4. 对账发现孤儿向量。

**验收**：检索路径始终强制 tenant/活跃过滤；不把异步删除当即时安全边界。

## 挑战题

### C1. 删除与备份恢复

写一页 runbook：恢复旧备份后，如何重放删除 tombstone，避免已删除用户数据“复活”；包含验证查询与审计证据。

## 通过线

- [ ] B1～B3 完成
- [ ] A1 或 A2 至少一题
- [ ] 能解释 TTL 与 purge、软删与硬删、源数据与派生索引的区别

## 参考要点

- `deleted_at` 记录状态发生时间；`expires_at` 表示进入可清理集合的时间。
- purge 是可观测的后台流程：小批量、幂等、可重试、可暂停。
- 导出包本身也是敏感数据，必须加密、审计并设置短 TTL。
- vector/memory 是派生副本；源删除与权限变化通过 outbox 传播，并用 reconciliation 收敛。
- 安全隔离必须在查询时强制 tenant/filter，不能等待最终一致性完成。
