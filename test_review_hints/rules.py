from __future__ import annotations

import ast
from dataclasses import dataclass
from pathlib import Path
import re


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
            findings.append(Finding("R43", rel, node.lineno, "test both produces and reads an event; review the tested boundary"))
    return findings


def scan_file(path: Path, root: Path | None = None) -> list[Finding]:
    root = root or path.parent
    rel = str(path.relative_to(root)).replace("\\", "/")
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    except (OSError, SyntaxError) as exc:
        return [Finding("PARSE", rel, 1, f"could not parse file: {type(exc).__name__}")]
    return _path_hints(tree, rel) + _unreachable(tree, rel) + _producer_reader(tree, rel)


def scan(paths: list[Path]) -> list[Finding]:
    files: list[Path] = []
    for path in paths:
        if path.is_file() and path.suffix == ".py":
            files.append(path)
        elif path.is_dir():
            files.extend(x for x in path.rglob("*.py") if "__pycache__" not in x.parts and ".venv" not in x.parts)
    findings: list[Finding] = []
    for path in sorted(files):
        root = paths[0] if paths and paths[0].is_dir() else path.parent
        findings.extend(scan_file(path, root))
    return findings
