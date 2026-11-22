# 数据生命周期：保留、删除、导出与索引同步

> 所属模块：`07-data-persistence` · 数据库与数据持久化  
> 建议学时：3～5 小时  
> 对应练习：[`exercises/07-data-persistence/06-data-lifecycle.md`](../../exercises/07-data-persistence/06-data-lifecycle.md)

## 1. 生命周期不是一条 `DELETE`

Agent 数据分散在关系库、对象存储、日志平台与向量索引。删除主表一行，不代表引用、embedding、缓存、备份和日志都已处理。上线前要为每类数据写清：

```text
创建 → 活跃 → 归档/软删 → TTL 到期 → purge 硬删 → 对账证明
                       └→ 用户导出
```

先定义数据所有者、用途、保留期、删除 SLA、导出格式与下游副本；法规或诉讼保全（legal hold）可暂停 purge，但必须审计。

## 2. 六类数据的默认策略

| 数据 | 常见真源 | 保留与删除要点 |
|------|----------|----------------|
| 会话 | PostgreSQL | 用户可软删；短恢复窗后连同消息 purge |
| 消息 | PostgreSQL/对象存储 | 跟随会话；附件单独引用计数，避免误删共享对象 |
| job | PostgreSQL/队列 | 状态留作排障；payload 尽早脱敏，终态按 TTL 清理 |
| 日志/trace | 日志平台 | 字段允许列表；安全审计通常比 debug 日志保留更久 |
| memory | DB/专用 store | 写入前审核；按用户导出/删除；事实更新应替换旧值 |
| vector/chunk | 向量库 | 派生数据；源文档删除或权限改变时同步删除/重建 |

期限必须来自产品、合规和排障需求，不能照抄示例。可把策略版本化：

```text
chat_session: soft_delete=30d, purge=30d
completed_job: ttl=14d
debug_log: ttl=7d
security_audit: ttl=180d
```

## 3. 软删除与硬删除

软删除字段建议用 `deleted_at TIMESTAMPTZ`，不要仅用布尔值；时间戳能支持恢复窗与 purge 游标。所有默认查询必须显式排除已删行：

```sql
SELECT * FROM chat_sessions
WHERE user_id = :user_id AND deleted_at IS NULL;
```

软删不是安全边界：唯一约束、JOIN、缓存和管理员接口都可能重新暴露数据。PostgreSQL 可按业务使用部分唯一索引：

```sql
CREATE UNIQUE INDEX uq_active_session_title
ON chat_sessions(user_id, title)
WHERE deleted_at IS NULL;
```

硬删使用可重试、小批量、带上限的 purge job：

```sql
DELETE FROM messages
WHERE id IN (
  SELECT id FROM messages
  WHERE deleted_at < now() - interval '30 days'
  ORDER BY id
  LIMIT 1000
);
```

不要在请求事务里级联删除百万行。purge 应记录策略版本、游标、删除数量与失败原因；对 legal hold、共享附件和外键顺序做显式处理。

## 4. TTL 与调度

TTL 是“何时有资格删除”，purge 是“实际执行删除”。两者不要混成一次无审计的定时 SQL。

- 数据库：`expires_at` + `(expires_at)` 索引；worker 分批删除。
- Redis：原生 TTL 只负责缓存，不代表真源已删除。
- 对象存储：生命周期规则适合附件/导出包，但要和元数据状态对账。
- 日志平台：按索引/数据集设置 retention，敏感 debug 日志期限更短。

purge 指标至少包括 `eligible_count`、`deleted_count`、`oldest_expired_at`、失败与重试次数。任务必须幂等：重复运行不能删错租户或未到期数据。

## 5. 导出

用户导出应先鉴权并固定 tenant/user 范围，生成一致快照，再异步打包 JSON/JSONL 与附件清单。导出包：

1. 使用短期签名 URL，不通过公开永久链接分发；
2. 加密存储，下载与生成均审计；
3. 自身设置短 TTL，过期后删除；
4. 标注生成时间、schema/version、包含与未包含的数据；
5. 不混入内部 prompt、密钥、他租户数据或纯内部安全审计。

删除与导出会竞态。服务应定义快照时点：导出开始后的新数据是否包含，软删数据是否仍在恢复窗导出，均要写进契约。

## 6. memory 与 vector 的特殊风险

Memory 不是“永不忘记”。长期记忆应有 `source_message_id`、`user_id/tenant_id`、`created_at`、`expires_at`、`deleted_at`，源消息删除时可追踪派生 memory。敏感内容应在写入前阻止，而非只依赖日后清理。

向量是源文档的派生副本，必须保留 `document_id`、`chunk_id`、`tenant_id`、`source_version`。典型同步流程：

```text
同一 DB 事务：源记录软删/改权限 + 写 outbox 事件
→ worker 删除 vector/chunk/cache
→ 标记事件完成
→ 定期对账：源已删但向量仍在 / 源活跃但向量缺失
```

不要在 DB 提交后“顺手调一次向量库”就认为一致：进程可能恰好崩溃。Outbox + 幂等 consumer + reconciliation 才能覆盖双写间隙。检索时仍必须服务端强制 tenant 与 `deleted_at` 过滤，不能等待异步删除完成才保证隔离。

## 7. 上线清单

- [ ] 六类数据都有 owner、retention、导出范围、软删/硬删规则
- [ ] `deleted_at` / `expires_at` 有查询与 purge 所需索引
- [ ] purge 小批量、幂等、有游标、指标、审计与 legal hold
- [ ] 导出严格按调用者租户过滤，包本身有 TTL
- [ ] memory/vector 能追溯到源数据
- [ ] 删除/权限变化通过 outbox 同步索引，并有失败重试与对账
- [ ] 备份保留期与删除承诺一致，明确恢复时如何防止已删数据复活

## 导航

- 上一章：[消息队列基础](./05-message-queue.md)
- 相关：[PostgreSQL](./02-postgresql.md) · [Agent Security](../12-agent-production/03-security.md)
- 返回模块：[README](./README.md)
