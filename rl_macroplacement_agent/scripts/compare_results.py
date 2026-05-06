#!/usr/bin/env python3
"""Compare aligned placement metric JSON files."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path


METRICS = ("cost", "wirelength", "congestion_cost", "density_cost", "runtime_sec")


def load_method(path: Path, method: str | None) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    row = {"method": method or data.get("method") or path.stem, "source": str(path)}
    for metric in METRICS:
        row[metric] = data.get(metric)
    return row


def render_markdown(rows: list[dict]) -> str:
    header = "| method | cost | wirelength | congestion | density | runtime_sec |\n"
    sep = "|---|---:|---:|---:|---:|---:|\n"
    body = []
    for row in rows:
        body.append(
            "| {method} | {cost} | {wirelength} | {congestion_cost} | {density_cost} | {runtime_sec} |".format(
                **{key: "-" if value is None else value for key, value in row.items()}
            )
        )
    return header + sep + "\n".join(body) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Compare PPO and DREAMPlace metrics.")
    parser.add_argument("--result", action="append", required=True, help="METHOD=path.json or path.json")
    parser.add_argument("--out_dir", required=True)
    args = parser.parse_args()

    rows = []
    for item in args.result:
        if "=" in item:
            method, path = item.split("=", 1)
        else:
            method, path = None, item
        rows.append(load_method(Path(path), method))

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    json_path = out_dir / "comparison.json"
    csv_path = out_dir / "comparison.csv"
    md_path = out_dir / "comparison.md"

    json_path.write_text(json.dumps(rows, indent=2), encoding="utf-8")
    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["method", *METRICS, "source"])
        writer.writeheader()
        writer.writerows(rows)
    md_path.write_text(render_markdown(rows), encoding="utf-8")
    print(md_path.read_text(encoding="utf-8"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
