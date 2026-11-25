from __future__ import annotations

import argparse
import json
import sys

from .lint import lint_dir


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="crew-config-lint", description="Lint agents.yaml and tasks.yaml")
    p.add_argument("path", help="project folder (agents.yaml/tasks.yaml here or in ./config)")
    p.add_argument("--input", "-i", action="append", default=None,
                   help="declared input name (repeatable). Enables placeholder checks.")
    p.add_argument("--json", action="store_true", help="print JSON")
    p.add_argument("--strict", action="store_true", help="warnings also fail the run")
    a = p.parse_args(argv)
    try:
        findings = lint_dir(a.path, a.input)
    except FileNotFoundError as e:
        print(f"error: {e}", file=sys.stderr)
        return 2
    if a.json:
        print(json.dumps([f.__dict__ | {"level": f.level} for f in findings], indent=2))
    else:
        for f in findings:
            print(f)
        errs = sum(f.level == "error" for f in findings)
        print(f"{errs} error(s), {len(findings) - errs} warning(s)")
    bad = any(f.level == "error" or a.strict for f in findings)
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
