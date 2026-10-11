from __future__ import annotations

import argparse
from pathlib import Path

from .rules import scan


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="test-review-hints")
    parser.add_argument("paths", nargs="+", type=Path)
    parser.add_argument("--include-boundary-hints", action="store_true",
                        help="include the ambiguous producer/reader review hint (R43)")
    args = parser.parse_args(argv)
    findings = scan(args.paths, include_boundary_hints=args.include_boundary_hints)
    for item in findings:
        print(f"{item.path}:{item.line}: {item.code} {item.message}")
    errors = sum(item.code in {"INPUT", "PARSE"} for item in findings)
    print(f"\n{len(findings) - errors} review hint(s). Hints are advisory; no tests were executed.")
    if errors:
        print(f"Scan incomplete: {errors} input/parse error(s).")
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
