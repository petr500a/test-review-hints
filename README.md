# test-review-hints

Small local review hints for Python tests.

It highlights a few patterns that deserve a second look:

- a machine-specific database path in a test;
- an assertion that is unreachable after `return` or `raise`;
- a test that produces and reads the same event, which may be checking the transport instead of the code under test.

The tool reads source files only. It does not run tests, modify your project, open databases, or send source code to a service. Findings are review prompts, not proof that a test is wrong.

## Quick start

```powershell
python -m test_review_hints.cli examples
```

Or install the local package:

```powershell
python -m pip install .
test-review-hints tests
```

Exit status is `0` even when hints are found. This first version is intentionally advisory; use your normal test runner and linter separately.

## Rules

| Code | Hint | Important limit |
|---|---|---|
| R23 | An absolute database path appears in a test | A path alone does not prove that the test writes production data |
| RD | Code follows an unconditional `return` or `raise` in the same block | The statement may be intentional in a fixture or example |
| R43 | A test calls a producer and reads its result in the same test | This can be correct when testing the transport itself; review the intended boundary |

## Privacy and safety

The scanner only reads text files supplied on the command line. It does not execute the files. Do not pass a production directory if you do not want its filenames and contents read locally by the process.

## Status

Early, deliberately narrow release. It is not a replacement for Ruff, pytest, mutation testing, or human review.

## License

MIT. See [LICENSE](LICENSE).
