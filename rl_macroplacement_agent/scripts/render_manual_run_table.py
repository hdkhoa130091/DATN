#!/usr/bin/env python3
"""Render the shared manual-run CSV as Markdown."""

from __future__ import annotations

import csv
import sys
from pathlib import Path


def main() -> int:
    csv_path = Path(sys.argv[1])
    md_path = csv_path.with_suffix(".md")
    rows = list(csv.DictReader(csv_path.open(encoding="utf-8")))
    headers = [
        "run_id",
        "agent",
        "steps",
        "episodes",
        "macros",
        "seed",
        "train_best_cost",
        "eval_cost",
        "wirelength",
        "train_runtime_sec",
        "eval_runtime_sec",
    ]
    lines = [
        "| " + " | ".join(headers) + " |",
        "|" + "|".join(["---"] * len(headers)) + "|",
    ]
    for row in rows:
        lines.append("| " + " | ".join(str(row.get(h, "")) for h in headers) + " |")
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(md_path.read_text(encoding="utf-8"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
