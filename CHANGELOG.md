# Changelog

## 0.1.0

- Initial narrow release candidate.
- R23 machine-specific database path hint.
- RD unreachable statement hint.
- R43 producer/reader boundary review hint, explicitly enabled with `--include-boundary-hints`.
- Invalid inputs and unreadable/unparseable source return status 2 instead of reporting a successful scan.
- Multiple roots, overlapping paths and Python source encodings are handled without executing inspected code.
