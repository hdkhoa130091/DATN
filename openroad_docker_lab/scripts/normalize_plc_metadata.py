#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
from pathlib import Path


NG45_DEFAULTS = {
    "route_hor": "57.031",
    "route_ver": "56.818",
    "macro_route_hor": "39.583",
    "macro_route_ver": "30.303",
    "smooth_range": "0",
    "overlap_threshold": "0.0000",
}


def _replace_or_insert(lines: list[str], prefix: str, new_line: str, insert_at: int) -> list[str]:
    for idx, line in enumerate(lines):
        if line.startswith(prefix):
            lines[idx] = new_line
            return lines
    lines.insert(insert_at, new_line)
    return lines


def _needs_default(line: str | None) -> bool:
    if line is None:
        return True
    nums = re.findall(r"[-+]?\d+(?:\.\d+)?", line)
    if not nums:
        return True
    return all(float(num) == 0.0 for num in nums)


def normalize_ng45(plc_path: Path) -> None:
    lines = plc_path.read_text().splitlines()
    comment_prefixes = {
        "routes": "# Routes per micron, hor : ",
        "macro_routes": "# Routes used by macros, hor : ",
        "smooth": "# Smoothing factor : ",
        "overlap": "# Overlap threshold : ",
    }

    existing = {
        key: next((line for line in lines if line.startswith(prefix)), None)
        for key, prefix in comment_prefixes.items()
    }

    insert_at = 0
    for idx, line in enumerate(lines):
        if not line.startswith("#"):
            insert_at = idx
            break
    else:
        insert_at = len(lines)

    if _needs_default(existing["routes"]):
        lines = _replace_or_insert(
            lines,
            comment_prefixes["routes"],
            f"# Routes per micron, hor : {NG45_DEFAULTS['route_hor']}  ver : {NG45_DEFAULTS['route_ver']}",
            insert_at,
        )
        insert_at += 1

    if _needs_default(existing["macro_routes"]):
        lines = _replace_or_insert(
            lines,
            comment_prefixes["macro_routes"],
            f"# Routes used by macros, hor : {NG45_DEFAULTS['macro_route_hor']}  ver : {NG45_DEFAULTS['macro_route_ver']}",
            insert_at,
        )
        insert_at += 1

    if existing["smooth"] is None:
        lines = _replace_or_insert(
            lines,
            comment_prefixes["smooth"],
            f"# Smoothing factor : {NG45_DEFAULTS['smooth_range']}",
            insert_at,
        )
        insert_at += 1

    if existing["overlap"] is None:
        lines = _replace_or_insert(
            lines,
            comment_prefixes["overlap"],
            f"# Overlap threshold : {NG45_DEFAULTS['overlap_threshold']}",
            insert_at,
        )

    plc_path.write_text("\n".join(lines) + "\n")


def main() -> int:
    parser = argparse.ArgumentParser(description="Normalize missing PLC metadata.")
    parser.add_argument("plc", help="Path to the .plc file to normalize")
    parser.add_argument(
        "--platform",
        default="ng45",
        choices=["ng45"],
        help="Technology platform defaults to apply when metadata is missing.",
    )
    args = parser.parse_args()

    plc_path = Path(args.plc)
    if not plc_path.is_file():
        raise SystemExit(f"PLC file not found: {plc_path}")

    normalize_ng45(plc_path)
    print(f"Normalized PLC metadata: {plc_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
