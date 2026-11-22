"""Argparse command-line adapter for the scanner."""

from __future__ import annotations

import argparse
import json
import logging
import sys
from collections.abc import Sequence

from cli_scanner.logging_setup import configure_logging
from cli_scanner.scanner import DEFAULT_EXTENSIONS, ScanError, scan_path

LOGGER = logging.getLogger(__name__)
EXIT_SUCCESS = 0
EXIT_USAGE_ERROR = 2
EXIT_SCAN_ERROR = 3


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="docscan", description="统计文本文件行数与空行数")
    parser.add_argument("path", help="要扫描的文件或目录")
    parser.add_argument(
        "--ext",
        default=",".join(sorted(DEFAULT_EXTENSIONS)),
        help="逗号分隔的扩展名，默认：md,py",
    )
    parser.add_argument("--json", action="store_true", help="输出 JSON")
    parser.add_argument("-v", "--verbose", action="store_true", help="显示扫描日志")
    return parser


def _parse_extensions(raw_extensions: str) -> set[str]:
    extensions = {
        extension.strip().removeprefix(".")
        for extension in raw_extensions.split(",")
        if extension.strip().removeprefix(".")
    }
    if not extensions:
        raise ValueError("至少需要一个有效扩展名")
    return extensions


def _render_text(result: dict[str, object]) -> str:
    lines = [
        f"路径: {result['path']}",
        f"文件: {result['files']}",
        f"总行数: {result['lines']}",
        f"空行数: {result['blank_lines']}",
        "按扩展名:",
    ]
    extension_stats = result["by_extension"]
    if isinstance(extension_stats, dict):
        for extension, stats in extension_stats.items():
            if isinstance(stats, dict):
                lines.append(
                    f"  .{extension}: {stats['files']} 文件, "
                    f"{stats['lines']} 行, {stats['blank_lines']} 空行"
                )
    return "\n".join(lines)


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    configure_logging(args.verbose)

    try:
        extensions = _parse_extensions(args.ext)
        LOGGER.info("扫描 %s，扩展名：%s", args.path, ", ".join(sorted(extensions)))
        result = scan_path(args.path, extensions).to_dict()
    except ValueError as error:
        parser.error(str(error))
        return EXIT_USAGE_ERROR
    except (ScanError, OSError, UnicodeError) as error:
        LOGGER.error("%s", error)
        return EXIT_SCAN_ERROR

    output = json.dumps(result, ensure_ascii=False, indent=2) if args.json else _render_text(result)
    print(output)
    return EXIT_SUCCESS


if __name__ == "__main__":
    sys.exit(main())
