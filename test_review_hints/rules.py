from __future__ import annotations

import ast
from dataclasses import dataclass
from pathlib import Path
import os
import re
import tokenize


@dataclass(frozen=True)
class Finding:
    code: str
    path: str
    line: int
    message: str


DB_PATH = re.compile(r"(?:^|[/\\])[A-Za-z0-9_.-]+\.(?:db|sqlite3?|db3)(?:$|[?#])", re.I)
TEMP_MARKERS = {"tmp", "temp", "fixture", "fixtures", "testdata", "example", "examples"}


def _is_test_file(path: Path) -> bool:
    return path.name.startswith("test_") or path.name.endswith("_test.py") or "tests" in path.parts


def _is_temporary(value: str) -> bool:
    parts = {part for part in re.split(r"[/\\._-]+", value.lower()) if part}
    return bool(parts & TEMP_MARKERS)


def _string_value(node: ast.AST) -> str | None:
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
        left, right = _string_value(node.left), _string_value(node.right)
        if left is not None and right is not None:
            return left + right
    return None


def _path_hints(tree: ast.AST, rel: str) -> list[Finding]:
    findings: list[Finding] = []
    if not _is_test_file(Path(rel)):
        return findings
    for node in ast.walk(tree):
        value = _string_value(node)
        if value is not None:
            value = value.replace("\\", "/")
            if DB_PATH.search(value) and re.match(r"^[A-Za-z]:/", value) and not _is_temporary(value):
                findings.append(Finding("R23", rel, node.lineno, f"machine-specific database path: {value}"))
    return findings


def _unreachable(tree: ast.AST, rel: str) -> list[Finding]:
    findings: list[Finding] = []
    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        for block in (node.body,):
            for index, statement in enumerate(block[:-1]):
                if isinstance(statement, (ast.Return, ast.Raise)):
                    findings.append(Finding("RD", rel, block[index + 1].lineno, "statement follows an unconditional return/raise"))
                    break
    return findings


def _producer_reader(tree: ast.AST, rel: str) -> list[Finding]:
    findings: list[Finding] = []
    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) or not node.name.startswith("test"):
            continue
        producer = any(isinstance(x, ast.Call) and getattr(x.func, "attr", "") in {"emit", "insert", "publish", "append_event"} for x in ast.walk(node))
        reader = any(isinstance(x, ast.Call) and getattr(x.func, "attr", "") in {"get_all", "get_events", "fetchall", "fetchone", "query"} for x in ast.walk(node))
        if producer and reader:
            findings.append(Finding("R43", rel, node.lineno, "test calls producer-like and reader-like methods; review the tested boundary"))
    return findings


def scan_file(path: Path, root: Path | None = None, *, include_boundary_hints: bool = False) -> list[Finding]:
    root = root or path.parent
    rel = str(path.relative_to(root)).replace("\\", "/")
    try:
        with tokenize.open(path) as source:
            tree = ast.parse(source.read(), filename=str(path))
    except (OSError, SyntaxError, UnicodeError, LookupError) as exc:
        return [Finding("PARSE", rel, getattr(exc, "lineno", None) or 1,
                        f"could not read or parse file: {type(exc).__name__}")]
    findings = _path_hints(tree, rel) + _unreachable(tree, rel)
    if include_boundary_hints:
        findings += _producer_reader(tree, rel)
    return findings


def scan(paths: list[Path], *, include_boundary_hints: bool = False) -> list[Finding]:
    files: dict[Path, tuple[Path, Path]] = {}
    findings: list[Finding] = []

    def walk_error(exc: OSError) -> None:
        findings.append(Finding("INPUT", str(exc.filename), 1, f"could not read directory: {type(exc).__name__}"))

    for path in paths:
        candidates: list[Path] = []
        if path.is_file() and path.suffix == ".py":
            candidates.append(path)
            root = path.parent
        elif path.is_dir():
            root = path
            for directory, subdirs, names in os.walk(path, onerror=walk_error):
                subdirs[:] = sorted(name for name in subdirs if name not in {"__pycache__", ".venv", ".git"})
                candidates.extend(Path(directory) / name for name in names if name.endswith(".py"))
            if not candidates:
                findings.append(Finding("INPUT", str(path), 1, "no Python files found in directory"))
        else:
            findings.append(Finding("INPUT", str(path), 1, "expected an existing .py file or directory"))
        for candidate in candidates:
            files.setdefault(candidate.resolve(), (candidate, root))
    for candidate, root in sorted(files.values()):
        items = scan_file(candidate, root, include_boundary_hints=include_boundary_hints)
        if len(paths) > 1:
            items = [Finding(item.code, str(candidate), item.line, item.message) for item in items]
        findings.extend(items)
    return findings
