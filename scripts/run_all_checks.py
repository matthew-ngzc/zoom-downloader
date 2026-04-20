#!/usr/bin/env python3
from __future__ import annotations

import subprocess
from pathlib import Path


def run_step(label: str, command: list[str], cwd: Path) -> None:
    print(f"\n=== {label} ===")
    print(" ".join(command))
    result = subprocess.run(command, cwd=cwd)
    if result.returncode != 0:
        raise SystemExit(result.returncode)


def main() -> None:
    repo_root = Path(__file__).resolve().parents[1]

    steps = [
        ("Static analysis (ruff)", ["uv", "run", "ruff", "check", "."]),
        ("Dependency audit (pip-audit)", ["uv", "run", "pip-audit"]),
        ("All tests (pytest, including e2e)", ["uv", "run", "pytest", "-q"]),
    ]

    for label, command in steps:
        run_step(label, command, repo_root)

    print("\nAll checks passed.")


if __name__ == "__main__":
    main()
