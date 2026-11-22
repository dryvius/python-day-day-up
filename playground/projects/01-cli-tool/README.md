# Project 1：文档扫描 CLI

可安装的目录扫描器，支持扩展名过滤、跳过开发目录、人类可读或 JSON 输出，以及明确的错误退出码。

## 安装

```bash
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[dev]'
```

## 用法

```bash
docscan . --ext md,py
docscan . --ext .py --json
docscan . -v
python -m cli_scanner .
```

默认跳过 `.git`、`.venv`、`__pycache__`。成功退出码为 `0`，参数错误为 `2`，扫描错误（路径不存在、权限或编码问题）为 `3`。

## 开发

```bash
pytest
```

核心扫描逻辑位于 `cli_scanner/scanner.py`，不依赖命令行或日志，可独立复用和测试。
