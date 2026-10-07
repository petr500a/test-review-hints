from __future__ import annotations

import argparse
from pathlib import Path

from .rules import scan


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="test-review-hints")
    parser.add_argument("paths", nargs="+", type=Path)
    args = parser.parse_args(argv)
    findings = scan(args.paths)
    for item in findings:
        print(f"{item.path}:{item.line}: {item.code} {item.message}")
    print(f"\n{len(findings)} review hint(s). Hints are advisory; no tests were executed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
