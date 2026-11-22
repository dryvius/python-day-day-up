# CLI 入口与参数解析

> 所属模块：`03-engineering` · Python 工程化  
> 状态：`已完成正文`  
> 建议学时：1.5～2.5 小时  
> 对应练习：[`exercises/03-engineering/05-cli-entrypoints.md`](../../exercises/03-engineering/05-cli-entrypoints.md)

## 本章定位

- **模块目标**：从「会写 Python」进入「会交付可安装、可测试的命令行程序」。
- **本章角色**：补齐 Project 1 的直接前置：参数解析、退出码、`python -m` 与安装后的命令入口。
- **学习策略**：主线只用标准库 `argparse`；Typer 等第三方库等真正需要复杂 CLI 时再选。
- **前置**：模块与包、项目结构、异常、pytest、logging。

## 学习目标

1. 用 `argparse` 定义位置参数、可选参数与布尔开关。
2. 把 CLI 适配层与业务逻辑分开，保持核心函数可直接单测。
3. 用 `main(argv: list[str] | None = None) -> int` 表达可测试入口与进程退出码。
4. 同时支持 `python -m app` 和安装后的命令入口。

## 重点分级

| 级别 | 内容 | 要求 |
|------|------|------|
| **必掌握** | `ArgumentParser`、`main(argv)`、退出码、薄 CLI | 能完成 Project 1 |
| **建议掌握** | 子命令、`pyproject.toml` 脚本入口 | 能交付可安装工具 |
| **了解即可** | Typer / Click、补全、复杂交互 | 有需求再引入 |

---

## 1. CLI 只是适配层

命令行和 HTTP API 本质相似：都负责接收外部输入、调用业务逻辑、把结果转换成外部能理解的输出。

```text
命令行参数 → 校验 / 转换 → 业务函数 → stdout / stderr + 退出码
```

因此不要把扫描目录、处理 JSON、写数据库等业务全部塞进 `cli.py`。推荐边界：

```text
app/
├── __init__.py
├── __main__.py
├── cli.py       # 解析参数、输出、异常映射
└── scanner.py   # 纯业务逻辑
```

业务函数应能绕过 CLI 直接调用：

```python
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ScanResult:
    files: int
    lines: int


def scan_path(path: Path, extensions: set[str]) -> ScanResult:
    if not path.exists():
        raise FileNotFoundError(path)

    files = 0
    lines = 0
    for item in path.rglob("*"):
        if not item.is_file() or item.suffix.removeprefix(".") not in extensions:
            continue
        files += 1
        with item.open(encoding="utf-8") as file:
            lines += sum(1 for _ in file)
    return ScanResult(files=files, lines=lines)
```

---

## 2. 用 `argparse` 定义输入契约

```python
import argparse


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="docscan",
        description="统计目录中指定类型文件的数量与行数",
    )
    parser.add_argument("path", help="待扫描目录")
    parser.add_argument(
        "--ext",
        default="md,py",
        help="逗号分隔的扩展名，默认 md,py",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="输出 JSON",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="显示详细日志",
    )
    return parser
```

几个关键点：

- 位置参数 `path` 必须提供。
- `--ext` 是有值的可选参数。
- `action="store_true"` 表示出现开关即为 `True`。
- `argparse` 会自动生成 `-h/--help`，缺必填参数时返回非零退出码。

把字符串转换成领域输入时尽早规范化：

```python
def parse_extensions(raw: str) -> set[str]:
    extensions = {
        item.strip().lower().removeprefix(".")
        for item in raw.split(",")
        if item.strip()
    }
    if not extensions:
        raise ValueError("至少提供一个扩展名")
    return extensions
```

---

## 3. 可测试入口：`main(argv) -> int`

不要在 import 时立即解析真实终端参数。把参数列表作为可注入依赖：

```python
import json
import logging
from pathlib import Path

from app.scanner import scan_path

logger = logging.getLogger(__name__)


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        extensions = parse_extensions(args.ext)
        result = scan_path(Path(args.path), extensions)
    except (FileNotFoundError, PermissionError, ValueError) as error:
        parser.error(str(error))

    payload = {"files": result.files, "lines": result.lines}
    if args.json:
        print(json.dumps(payload, ensure_ascii=False))
    else:
        print(f"files={result.files} lines={result.lines}")

    logger.info("scan_ok path=%s files=%d", args.path, result.files)
    return 0
```

`main(["docs", "--ext", "md", "--json"])` 可在测试中直接调用，不需要启动子进程。

### 退出码约定

| 退出码 | 含义 |
|--------|------|
| `0` | 成功 |
| `2` | 参数格式或输入契约错误（`argparse` 默认） |
| 其他非零值 | 应用定义的失败 |

正常结果写到 stdout；错误与诊断写到 stderr。调用者才能稳定地把输出接入管道或脚本。

---

## 4. 两种运行入口

### 4.1 `python -m app`

`app/__main__.py`：

```python
from app.cli import main


if __name__ == "__main__":
    raise SystemExit(main())
```

使用：

```bash
python -m app docs --ext md --json
```

`SystemExit(main())` 会把返回值交给操作系统，避免入口代码散落。

### 4.2 安装后的命令

`pyproject.toml`：

```toml
[project]
name = "docscan"
version = "0.1.0"
requires-python = ">=3.11"

[project.scripts]
docscan = "app.cli:main"
```

开发期安装：

```bash
python -m pip install -e .
docscan docs --ext md
```

脚本入口引用的是可导入函数，因此包布局、虚拟环境和安装方式必须先正确。

---

## 5. 什么时候才用子命令或 Typer

只有一个动作时，优先保持：

```text
docscan <path> [options]
```

存在多个独立动作时，再使用子命令：

```text
todo add "学习 argparse"
todo list
todo done 42
```

`argparse` 支持 `add_subparsers()`；但 Project 1 不需要为了展示技术而强行增加层级。

Typer / Click 的价值主要在复杂类型声明、命令分组、终端体验和自动补全。引入第三方 CLI 框架前先确认：

1. 标准库是否已经够用？
2. 新依赖是否会增加安装与版本维护成本？
3. 核心业务是否仍然独立于框架？

---

## 6. 常见错误

| 错误 | 后果 | 修正 |
|------|------|------|
| import 时直接 `parse_args()` | 测试与复用模块时意外退出 | 放进 `main(argv)` |
| 业务逻辑全在 `cli.py` | 难测试、难复用到 API | CLI 只做适配 |
| 捕获所有 `Exception` 后返回 0 | 自动化误以为成功 | 映射明确异常并返回非零 |
| 正常结果与日志混在 stdout | JSON/管道无法解析 | 日志和错误走 stderr |
| 只支持源码目录运行 | 安装后导入失败 | 同时验证 `python -m` 与脚本入口 |

---

## 7. 练习与通关

练习：[`exercises/03-engineering/05-cli-entrypoints.md`](../../exercises/03-engineering/05-cli-entrypoints.md)

### 自检

- [ ] 能写 `build_parser()`，包含位置参数、值参数与布尔开关
- [ ] 能直接调用 `main([...])` 测试，而不依赖真实 `sys.argv`
- [ ] 业务函数不依赖 `argparse.Namespace`
- [ ] 成功返回 0，错误返回非零且信息进入 stderr
- [ ] `python -m app` 与安装后的命令至少跑通一种

完成本章后，先学 [Git 协作与 CI 门禁](./06-git-ci.md) 与 [调试与故障定位](./07-debugging.md)，再进入 [Project 1：Python CLI 工具](../projects/01-cli-tool.md)，把模块 01～03 收成第一个可交付项目。

## 导航

- 返回总览：[../../README.md](../../README.md)
- 上一章：[Logging](./04-logging.md)
- 下一章：[Git 协作与 CI 门禁](./06-git-ci.md)
- 之后：[调试与故障定位](./07-debugging.md) → [Project 1：Python CLI 工具](../projects/01-cli-tool.md)
