#!/usr/bin/env python3
"""Clamp placeInstance Tcl coordinates into the DEF core box."""

from __future__ import annotations

import argparse
import re
import shlex
from pathlib import Path


CORE_PATTERNS = {
    "llx": re.compile(r"FE_CORE_BOX_LL_X REAL ([0-9.]+)"),
    "lly": re.compile(r"FE_CORE_BOX_LL_Y REAL ([0-9.]+)"),
    "urx": re.compile(r"FE_CORE_BOX_UR_X REAL ([0-9.]+)"),
    "ury": re.compile(r"FE_CORE_BOX_UR_Y REAL ([0-9.]+)"),
}


def parse_def_core(def_path: Path) -> tuple[float, float, float, float]:
    text = def_path.read_text(encoding="utf-8", errors="replace")
    values = {}
    for key, pattern in CORE_PATTERNS.items():
        match = pattern.search(text)
        if not match:
            raise ValueError(f"Missing DEF core property for {key} in {def_path}")
        values[key] = float(match.group(1))
    return values["llx"], values["lly"], values["urx"], values["ury"]


def parse_pb_macro_sizes(pb_path: Path) -> dict[str, tuple[float, float]]:
    sizes: dict[str, list[float | str | None]] = {}
    current_name = None
    current_width = None
    current_height = None
    current_type = None
    current_key = None

    def register(name: str, width: float, height: float) -> None:
        sizes[name] = (float(width), float(height))
        sizes[name.replace(r"\[", "[").replace(r"\]", "]")] = (float(width), float(height))
        sizes[name.replace("[", r"\[").replace("]", r"\]")] = (float(width), float(height))

    def flush():
        if current_name and current_type == '"MACRO"' and current_width is not None and current_height is not None:
            register(current_name, float(current_width), float(current_height))

    for raw in pb_path.read_text(encoding="utf-8", errors="replace").splitlines():
        words = raw.split()
        if not words:
            continue
        if words[0] == "node":
            flush()
            current_name = None
            current_width = None
            current_height = None
            current_type = None
            current_key = None
        elif words[0] == "name:":
            current_name = words[1].strip('"')
        elif words[0] == "key:":
            current_key = words[1]
        elif words[0] == "placeholder:" and current_key == '"type"':
            current_type = words[1]
        elif words[0] == "f:" and current_key == '"width"':
            current_width = float(words[1])
        elif words[0] == "f:" and current_key == '"height"':
            current_height = float(words[1])
    flush()
    return sizes


def clamp(value: float, low: float, high: float) -> float:
    return min(max(value, low), high)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--in_tcl", required=True)
    parser.add_argument("--pb", required=True)
    parser.add_argument("--def_file", required=True)
    parser.add_argument("--out_tcl", required=True)
    args = parser.parse_args()

    in_tcl = Path(args.in_tcl)
    pb_path = Path(args.pb)
    def_path = Path(args.def_file)
    out_tcl = Path(args.out_tcl)

    llx, lly, urx, ury = parse_def_core(def_path)
    macro_sizes = parse_pb_macro_sizes(pb_path)

    out_lines: list[str] = []
    clamped = 0
    for raw in in_tcl.read_text(encoding="utf-8", errors="replace").splitlines():
        stripped = raw.strip()
        if not stripped or stripped.startswith("#"):
            out_lines.append(raw)
            continue

        tokens = shlex.split(stripped)
        if not tokens or tokens[0] != "placeInstance":
            out_lines.append(raw)
            continue

        inst_name = tokens[1]
        x = float(tokens[2])
        y = float(tokens[3])
        orient = tokens[4]
        status = tokens[5] if len(tokens) > 5 else "-fixed"

        if inst_name not in macro_sizes:
            raise KeyError(f"Macro {inst_name} not found in {pb_path}")
        width, height = macro_sizes[inst_name]
        new_x = clamp(x, llx, urx - width)
        new_y = clamp(y, lly, ury - height)
        if new_x != x or new_y != y:
            clamped += 1
        out_lines.append(f"placeInstance {inst_name} {new_x:.6f} {new_y:.6f} {orient} {status}")

    out_tcl.parent.mkdir(parents=True, exist_ok=True)
    out_tcl.write_text("\n".join(out_lines) + "\n", encoding="utf-8")
    print(f"core=({llx}, {lly})-({urx}, {ury})")
    print(f"macros={len(macro_sizes)}")
    print(f"clamped={clamped}")
    print(f"out={out_tcl}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
