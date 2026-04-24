#!/usr/bin/env python3
"""Convert placeInstance Tcl into OpenROAD-friendly placement commands."""

from __future__ import annotations

import argparse
import shlex
from pathlib import Path


STATUS_MAP = {
    "-fixed": "FIXED",
    "-placed": "PLACED",
}


def parse_place_instance(line: str):
    stripped = line.strip()
    if not stripped or stripped.startswith("#"):
        return None

    tokens = shlex.split(stripped)
    if not tokens or tokens[0] != "placeInstance":
        return None
    if len(tokens) < 5:
        raise ValueError(f"Unsupported placeInstance line: {line.rstrip()}")

    inst_name = tokens[1]
    x = tokens[2]
    y = tokens[3]
    orientation = tokens[4]
    status = "PLACED"
    if len(tokens) >= 6:
        status = STATUS_MAP.get(tokens[5], tokens[5].lstrip("-").upper())

    return {
        "inst_name": inst_name,
        "x": x,
        "y": y,
        "orientation": orientation,
        "status": status,
    }


def format_place_inst(entry: dict) -> str:
    return (
        f'place_inst -name {{{entry["inst_name"]}}} '
        f'-location {{{entry["x"]} {entry["y"]}}} '
        f'-orientation {entry["orientation"]} '
        f'-status {entry["status"]}'
    )


def format_place_macro(entry: dict, exact: bool) -> str:
    cmd = (
        f'place_macro -macro_name {{{entry["inst_name"]}}} '
        f'-location {{{entry["x"]} {entry["y"]}}} '
        f'-orientation {entry["orientation"]}'
    )
    if exact:
        cmd += " -exact"
    return cmd


def convert_file(in_path: Path, out_path: Path, mode: str, exact: bool) -> int:
    converted = 0
    out_lines = [
        "# Auto-generated from placeInstance Tcl\n",
        f"# Source: {in_path}\n",
    ]

    for raw_line in in_path.read_text(encoding="utf-8", errors="replace").splitlines():
        parsed = parse_place_instance(raw_line)
        if parsed is None:
            if raw_line.strip():
                out_lines.append(raw_line + "\n")
            continue

        if mode == "place_macro":
            out_lines.append(format_place_macro(parsed, exact) + "\n")
        else:
            out_lines.append(format_place_inst(parsed) + "\n")
        converted += 1

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("".join(out_lines), encoding="utf-8")
    return converted


def main() -> int:
    parser = argparse.ArgumentParser(description="Convert placeInstance Tcl to OpenROAD Tcl.")
    parser.add_argument("--in_tcl", required=True, help="Input Tcl with placeInstance commands")
    parser.add_argument("--out_tcl", required=True, help="Output Tcl for OpenROAD")
    parser.add_argument(
        "--mode",
        choices=["place_inst", "place_macro"],
        default="place_inst",
        help="Output command style",
    )
    parser.add_argument(
        "--exact",
        action="store_true",
        help="When using place_macro, append -exact",
    )
    args = parser.parse_args()

    in_path = Path(args.in_tcl)
    out_path = Path(args.out_tcl)
    converted = convert_file(in_path, out_path, args.mode, args.exact)
    print(f"Converted {converted} placement commands to {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
