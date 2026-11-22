# 练习：CLI 入口与参数解析

> 对应文档：[`docs/03-engineering/05-cli-entrypoints.md`](../../docs/03-engineering/05-cli-entrypoints.md)  
> 状态：`已完成出题`  
> 建议用时：60～90 分钟

## 练习说明

在 `playground/03-engineering/05-cli-entrypoints/` 实现一个可测试的文本统计 CLI：

```text
textstat <path> [--json] [-v]
```

建议结构：

```text
app/
├── __init__.py
├── __main__.py
├── cli.py
└── counter.py
tests/
├── test_cli.py
└── test_counter.py
pyproject.toml
```

先完成基础题，再看文末验收提示。

---

## 热身题

### W1. 三层职责

分别用一句话说明：

1. `cli.py`
2. `counter.py`
3. `__main__.py`

**验收**：CLI 负责适配、counter 负责业务、`__main__` 只负责启动。

### W2. 退出码

写出成功、参数错误、业务输入错误应返回什么类型的退出码。

**验收**：成功为 0；失败为非零；不要把具体非零数字误当跨项目统一标准。

---

## 基础题（必做）

### B1. 纯业务函数

实现：

```python
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class TextStats:
    lines: int
    words: int
    characters: int


def count_text(path: Path) -> TextStats:
    ...
```

要求：

- UTF-8 读取文本文件。
- 路径不存在时抛 `FileNotFoundError`。
- 目录或非普通文件时抛 `ValueError`。
- 不 import `argparse`，不打印输出。

**验收**：使用 `tmp_path` 覆盖正常文件、空文件、缺失文件。

### B2. 参数解析器

实现 `build_parser() -> argparse.ArgumentParser`：

- 位置参数 `path`
- 开关 `--json`
- 开关 `-v/--verbose`

**验收**：`build_parser().parse_args(["note.txt", "--json"])` 的字段正确；`--help` 自动存在。

### B3. 可注入入口

实现：

```python
def main(argv: list[str] | None = None) -> int:
    ...
```

要求：

- 调用 `count_text`。
- 默认输出 `lines=... words=... characters=...`。
- `--json` 输出合法 JSON。
- 文件不存在或路径非法时写 stderr 并返回非零。
- 不把 `argparse.Namespace` 传入业务层。

**验收**：pytest 用 `capsys` 检查 stdout / stderr；成功与失败路径均有测试。

### B4. 模块入口

实现 `app/__main__.py`，确认以下命令可运行：

```bash
python -m app sample.txt --json
```

**验收**：成功时 shell 退出码为 0；缺失文件时为非零。

---

## 进阶题（建议）

### A1. 安装命令

在 `pyproject.toml` 配置：

```toml
[project.scripts]
textstat = "app.cli:main"
```

执行：

```bash
python -m pip install -e .
textstat sample.txt
```

**验收**：不切到源码文件目录也能执行安装后的命令。

### A2. 日志边界

`-v` 时开启 INFO 日志，记录 `count_ok path=...`，但 JSON 结果仍可被解析。

**验收**：JSON 只出现在 stdout；日志出现在 stderr。

---

## 挑战题（可选）

### C1. 子命令

增加：

```text
textstat file <path>
textstat stdin
```

使用 `add_subparsers()`，但复用同一个 `TextStats` 结果模型。

**验收**：两个子命令均有测试；业务计算没有复制两份。

---

## 本章通过线

- [ ] B1～B4 全部完成
- [ ] pytest 覆盖正常、空文件、缺失路径、JSON 输出
- [ ] 核心业务不依赖 CLI 框架
- [ ] stdout / stderr 与退出码语义正确
- [ ] 至少手工跑通一次 `python -m app`

达到通过线后再进入 Project 1；A1/A2 可与 Project 1 的 M2/M3 合并完成。

## 验收提示（做完再看）

1. `main(argv)` 应把 `argv` 原样交给 `parse_args`；`None` 时自然读取 `sys.argv`。
2. `capsys.readouterr()` 可分别检查 `.out` 与 `.err`。
3. 业务异常应在 CLI 边界转换成用户消息与退出码，不要在 `counter.py` 内 `sys.exit()`。
4. `__main__.py` 推荐仅包含导入和 `raise SystemExit(main())`。

## 导航

- 对应正文：[CLI 入口与参数解析](../../docs/03-engineering/05-cli-entrypoints.md)
- 下一站：[Project 1：Python CLI 工具](../../docs/projects/01-cli-tool.md)
- 练习总览：[../README.md](../README.md)
