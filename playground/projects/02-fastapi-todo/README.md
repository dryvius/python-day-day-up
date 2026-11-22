# Project 2：FastAPI Todo

基于 FastAPI、Pydantic v2、SQLAlchemy 2 和 Alembic 的分层 Todo REST API。除健康检查外，所有接口均要求 `X-API-Key`。

规格文档里的学习者脚手架常用包名 `app/`；本参考实现包名为 `todo_api`。中间件会写入 / 回传 `X-Request-ID`，并在结构化日志中带上 `request_id`。

## 安装与配置

```bash
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[dev]'
cp .env.example .env
```

请在 `.env` 中替换开发密钥。应用配置全部来自环境变量；仓库不会提交 `.env`。

## 迁移与启动

应用不会用 `create_all` 隐式建表，启动前必须执行迁移：

```bash
alembic upgrade head
uvicorn todo_api.main:app --reload
```

修改模型时先生成并审查 revision，再执行 `upgrade head`；完整流程见 [`docs/07-data-persistence/03-orm.md`](../../../docs/07-data-persistence/03-orm.md)。参考实现已有迁移与测试，练习新迁移时不要覆盖现有 revision。

## API 示例

```bash
curl http://127.0.0.1:8000/health
curl -X POST http://127.0.0.1:8000/v1/todos \
  -H 'Content-Type: application/json' \
  -H 'X-API-Key: replace-with-a-long-random-value' \
  -d '{"title":"学习 FastAPI"}'
curl http://127.0.0.1:8000/v1/todos \
  -H 'X-API-Key: replace-with-a-long-random-value'
```

完整 OpenAPI 文档位于 `/docs`。

## 测试

```bash
pytest
```

测试使用独立 SQLite 文件，先执行真实 Alembic 迁移，再通过依赖覆盖注入测试 Session；每个测试后清理数据，不接触开发数据库。
