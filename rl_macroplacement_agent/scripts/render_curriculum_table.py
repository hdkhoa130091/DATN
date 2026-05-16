#!/usr/bin/env python3
"""Render a curriculum-vs-scratch performance table."""

from __future__ import annotations

import csv
import sys
from pathlib import Path


def pct_improvement(initial: float, value: float) -> float:
    return (initial - value) / initial * 100.0


def main() -> int:
    csv_path = Path(sys.argv[1])
    rows = list(csv.DictReader(csv_path.open(encoding="utf-8")))
    headers = [
        "run_id",
        "mode",
        "stage",
        "macros",
        "seed",
        "eval_cost",
        "improvement_vs_initial_pct",
        "wirelength",
        "train_runtime_sec",
    ]
    lines = [
        "| " + " | ".join(headers) + " |",
        "|" + "|".join(["---"] * len(headers)) + "|",
    ]
    for row in rows:
        initial = float(row["initial_cost"])
        eval_cost = float(row["eval_cost"])
        values = {
            **row,
            "improvement_vs_initial_pct": f"{pct_improvement(initial, eval_cost):.4f}",
        }
        lines.append("| " + " | ".join(str(values[h]) for h in headers) + " |")
    md_path = csv_path.with_suffix(".md")
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(md_path.read_text(encoding="utf-8"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
