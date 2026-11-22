"""Pure directory-scanning logic with no CLI or logging concerns."""

from __future__ import annotations

from collections.abc import Iterator
from dataclasses import asdict, dataclass
from pathlib import Path

DEFAULT_EXTENSIONS = frozenset({"md", "py"})
SKIPPED_DIRECTORIES = frozenset({".git", ".venv", "__pycache__"})


class ScanError(Exception):
    """Base error raised for an invalid scan request."""


class ScanPathNotFoundError(ScanError):
    """Raised when the requested path does not exist."""


@dataclass(frozen=True, slots=True)
class ExtensionStats:
    files: int = 0
    lines: int = 0
    blank_lines: int = 0


@dataclass(frozen=True, slots=True)
class ScanResult:
    path: str
    files: int
    lines: int
    blank_lines: int
    by_extension: dict[str, ExtensionStats]

    def to_dict(self) -> dict[str, object]:
        """Return a JSON-serializable representation."""
        return asdict(self)


def normalize_extensions(extensions: set[str] | frozenset[str]) -> frozenset[str]:
    """Normalize extension names to lowercase values without leading dots."""
    return frozenset(
        extension.strip().lower().removeprefix(".")
        for extension in extensions
        if extension.strip().removeprefix(".")
    )


def _iter_files(path: Path, extensions: frozenset[str]) -> Iterator[Path]:
    if path.is_file():
        if path.suffix.lower().removeprefix(".") in extensions:
            yield path
        return

    for candidate in path.rglob("*"):
        if any(part in SKIPPED_DIRECTORIES for part in candidate.parts):
            continue
        if candidate.is_file() and candidate.suffix.lower().removeprefix(".") in extensions:
            yield candidate


def scan_path(
    path: str | Path,
    extensions: set[str] | frozenset[str] = DEFAULT_EXTENSIONS,
) -> ScanResult:
    """Scan a file or directory and return aggregate text statistics."""
    root = Path(path).expanduser()
    if not root.exists():
        raise ScanPathNotFoundError(f"路径不存在：{root}")

    normalized_extensions = normalize_extensions(extensions)
    mutable_stats: dict[str, list[int]] = {}
    total_files = total_lines = total_blank_lines = 0

    for file_path in _iter_files(root, normalized_extensions):
        with file_path.open("r", encoding="utf-8") as file:
            lines = file.readlines()
        extension = file_path.suffix.lower().removeprefix(".")
        blank_lines = sum(not line.strip() for line in lines)
        extension_stats = mutable_stats.setdefault(extension, [0, 0, 0])
        extension_stats[0] += 1
        extension_stats[1] += len(lines)
        extension_stats[2] += blank_lines
        total_files += 1
        total_lines += len(lines)
        total_blank_lines += blank_lines

    by_extension = {
        extension: ExtensionStats(*values)
        for extension, values in sorted(mutable_stats.items())
    }
    return ScanResult(
        path=str(root),
        files=total_files,
        lines=total_lines,
        blank_lines=total_blank_lines,
        by_extension=by_extension,
    )
