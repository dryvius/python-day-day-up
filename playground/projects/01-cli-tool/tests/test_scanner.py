from pathlib import Path

import pytest
from cli_scanner.scanner import ScanPathNotFoundError, scan_path


def test_scan_path_counts_files_lines_and_extensions(tmp_path: Path) -> None:
    (tmp_path / "guide.md").write_text("# Guide\n\nHello\n", encoding="utf-8")
    (tmp_path / "main.py").write_text("print('ok')\n", encoding="utf-8")
    (tmp_path / "ignored.txt").write_text("ignored\n", encoding="utf-8")
    skipped = tmp_path / ".venv"
    skipped.mkdir()
    (skipped / "hidden.py").write_text("ignored\n", encoding="utf-8")

    result = scan_path(tmp_path)

    assert (result.files, result.lines, result.blank_lines) == (2, 4, 1)
    assert result.by_extension["md"].files == 1
    assert result.by_extension["py"].lines == 1


def test_scan_path_returns_zeroes_for_empty_directory(tmp_path: Path) -> None:
    result = scan_path(tmp_path)

    assert (result.files, result.lines, result.blank_lines) == (0, 0, 0)
    assert result.by_extension == {}


def test_scan_path_rejects_missing_path(tmp_path: Path) -> None:
    with pytest.raises(ScanPathNotFoundError, match="路径不存在"):
        scan_path(tmp_path / "missing")


def test_scan_path_filters_custom_extensions(tmp_path: Path) -> None:
    (tmp_path / "notes.txt").write_text("one\n\n", encoding="utf-8")
    (tmp_path / "ignored.py").write_text("ignored\n", encoding="utf-8")

    result = scan_path(tmp_path, {"txt"})

    assert result.files == 1
    assert set(result.by_extension) == {"txt"}
