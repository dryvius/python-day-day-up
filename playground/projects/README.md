# 实战项目参考实现

每个项目都是独立 Python 包，请进入对应目录后创建虚拟环境、安装和测试。

## 当前项目

- [Project 1：文档扫描 CLI](./01-cli-tool/README.md) — argparse、可安装脚本入口、纯扫描逻辑、JSON/扩展名/跳过目录/退出码与 pytest。
- [Project 2：FastAPI Todo](./02-fastapi-todo/README.md) — FastAPI、Pydantic v2、SQLAlchemy 2、API Key、分层 CRUD、Alembic 与隔离测试。
- [Project 3：AI Chat](./03-ai-chat/README.md) — FakeLLM、多轮历史、Context Packer、非流式 Chat API、SSE 与脱敏日志。
- [Project 4：RAG 知识库](./04-rag-kb/README.md) — 离线检索、引用、评测集与回归基线。
- [Project 5：Tool Agent](./05-tool-agent/README.md) — tool-loop、名称/参数 ACL、幂等副作用、Memory 与 MCP bridge。
- [Project 6：Research Agent](./06-research-agent/README.md) — 队列 Worker、HITL、硬预算、生命周期、引用报告与 eval。

## 通用验证

```bash
cd 01-cli-tool
python -m pip install -e '.[dev]'
pytest

cd ../02-fastapi-todo
python -m pip install -e '.[dev]'
pytest

cd ../03-ai-chat
python -m pip install -e '.[dev]'
pytest

cd ../04-rag-kb
python -m pip install -e '.[dev]'
pytest && python scripts/run_eval.py

cd ../05-tool-agent
python -m pip install -e '.[dev]'
pytest && python eval/run_eval.py

cd ../06-research-agent
python -m pip install -e '.[dev]'
pytest && python eval/run_eval.py
```

六个项目分别维护依赖和测试配置，不应从仓库根目录混合安装。
