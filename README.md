# test-review-hints

Small local review hints for Python tests.

It highlights a few patterns that deserve a second look:

- a Windows drive-letter database path in a test;
- a statement after an unconditional `return` or `raise` at the top level of a function body;
- optionally, a test that calls producer-like and reader-like methods. This can be a correct transport test; the tool cannot establish whether they operate on the same event.

The tool reads source files only. It does not run tests, modify your project, open databases, or send source code to a service. Findings are review prompts, not proof that a test is wrong.

## Quick start

Requires Python 3.11 or newer. From a terminal:

```sh
git clone https://github.com/petr500a/test-review-hints.git
cd test-review-hints
python -m test_review_hints.cli examples
```

The default demo prints an `R23` hint for `test_db_path.py` and an `RD` hint for `test_unreachable.py`. The `tmp_path` example is not flagged.

Or install the local package:

```sh
python -m pip install .
test-review-hints tests
```

Enable the noisier boundary hint explicitly:

```sh
test-review-hints --include-boundary-hints examples
```

This adds `R43` for `test_boundary.py`, an intentionally valid transport test. Review context before changing a test.

Exit status is `0` for a completed scan, even when hints are found. Status `2` means the scan is incomplete: invalid/missing input, an empty directory, a read/encoding error, or a Python syntax error. Other readable files are still checked. No result proves that your tests are correct; use your normal test runner and linter separately.

## Rules

| Code | Hint | Important limit |
|---|---|---|
| R23 | A Windows drive-letter database path appears in a test file | POSIX/UNC paths and dynamically computed paths are not covered; fixture/temp markers are excluded |
| RD | A statement follows an unconditional `return` or `raise` directly in a function body | Nested branches, loops and other control-flow cases are not analyzed |
| R43 (opt-in) | A test function calls producer-like and reader-like methods | Name-based heuristic only; does not prove a shared event, object, or incorrect boundary |

Directories are scanned recursively, excluding `.git`, `.venv` and `__pycache__`. Multiple input paths are supported; overlapping files are checked once. Python encoding declarations and UTF-8 BOM are supported.

## Privacy and safety

The scanner only reads text files supplied on the command line. It does not execute the files. Do not pass a production directory if you do not want its filenames and contents read locally by the process.

## Status

Early, deliberately narrow release candidate. It is not a replacement for Ruff, pytest, mutation testing, or human review. There is no published PyPI package; install this repository locally with the command above.

To report a problem, [open an issue](https://github.com/petr500a/test-review-hints/issues) with your command, Python/OS versions and a small sanitized example. Never attach private source code, database files or credentials.

## License

MIT. See [LICENSE](LICENSE).
