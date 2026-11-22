import json
from pathlib import Path

from cli_scanner.cli import EXIT_SCAN_ERROR, EXIT_SUCCESS, main


def test_cli_outputs_json(tmp_path: Path, capsys) -> None:
    (tmp_path / "sample.py").write_text("x = 1\n", encoding="utf-8")

    exit_code = main([str(tmp_path), "--ext", ".py", "--json"])

    output = json.loads(capsys.readouterr().out)
    assert exit_code == EXIT_SUCCESS
    assert output["files"] == 1
    assert output["by_extension"]["py"]["lines"] == 1


def test_cli_returns_non_zero_for_missing_path(tmp_path: Path, capsys) -> None:
    exit_code = main([str(tmp_path / "missing")])

    assert exit_code == EXIT_SCAN_ERROR
    assert "路径不存在" in capsys.readouterr().err
