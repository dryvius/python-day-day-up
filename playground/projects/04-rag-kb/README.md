# Project 4：RAG 知识库参考实现

完全离线、可复现的最小 RAG：读取 Markdown/TXT，切分并写入内存向量索引，Top-K 检索后由 FakeLLM 生成带 citations 的回答；资料不足时明确拒答。

## 口径与默认参数

- 切分口径：**Unicode 字符数**，不是 token；`chunk_size=240`、`overlap=40`
- 检索：余弦相似度，`K=3`，最低分 `0.15`
- FakeEmbedding：256 维 BLAKE2 特征哈希；不使用进程随机化的 Python `hash()`
- 元数据：`source`、`chunk_index`、`extension`；引用输出 `source/chunk_id/snippet/score`
- FakeLLM 遵守 `complete(...) -> {"role": "assistant", "content": ...}` 契约

字符实验不得与 tokenizer 的 token 实验直接比较。真实私有语料放入已忽略的 `data/private_docs/`。

## 安装与运行

```bash
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[dev]'
pytest
python scripts/run_eval.py
```

评测分别输出：

- `Retrieval Hit@K`：应命中题的期望来源是否出现在 Top-K
- `Refusal accuracy`：库外问题是否进入拒答分支

## 代码边界

- `rag_kb/chunking.py`：字符切分
- `rag_kb/embedding.py`：确定性 FakeEmbedding
- `rag_kb/index.py`：内存索引、metadata filter、Top-K
- `rag_kb/pipeline.py`：`ingest/ask`
- `eval/cases.json`：离线题集

这是教学参考实现，不持久化索引。替换 embedding 或索引时保留 `embed/embed_many` 与 `add/search` 边界，pipeline 无需改问答契约。
