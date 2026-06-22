#!/usr/bin/env python3
"""Clamp PLC node coordinates into the declared canvas bounds.

Optionally keep a safety margin measured in grid cells. This is useful when a
macro center may still be inside the canvas, but its pins can extend beyond the
top/right edges and break downstream congestion evaluation.
"""

from __future__ import annotations

import argparse
import math
from pathlib import Path


def parse_canvas(lines: list[str]) -> tuple[float, float]:
    width = height = None
    for line in lines:
        if line.startswith("# Width :"):
            parts = line.replace("#", "").split()
            width = float(parts[2])
            height = float(parts[5])
            break
    if width is None or height is None:
        raise ValueError("Could not find '# Width :' header in PLC file.")
    return width, height


def clamp_value(value: float, lower: float, upper: float) -> float:
    return min(max(value, lower), upper)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, help="Source .plc file")
    parser.add_argument("--output", required=True, help="Clamped .plc file")
    parser.add_argument(
        "--margin_grid_cells",
        type=float,
        default=0.0,
        help="Safety margin from each canvas edge, measured in grid cells.",
    )
    args = parser.parse_args()

    src = Path(args.input)
    dst = Path(args.output)

    lines = src.read_text().splitlines()
    width, height = parse_canvas(lines)
    cols = rows = None
    for line in lines:
        if line.startswith("# Columns :"):
            parts = line.split()
            cols = int(parts[3])
            rows = int(parts[6])
            break
    if cols is None or rows is None:
        raise ValueError("Could not find '# Columns :' header in PLC file.")

    grid_w = width / cols
    grid_h = height / rows
    margin_x = args.margin_grid_cells * grid_w
    margin_y = args.margin_grid_cells * grid_h

    max_x = math.nextafter(width - margin_x, float("-inf"))
    max_y = math.nextafter(height - margin_y, float("-inf"))
    min_x = margin_x
    min_y = margin_y

    out_lines: list[str] = []
    clamp_count = 0
    x_count = 0
    y_count = 0

    inserted_note = False
    for line in lines:
        if not inserted_note and line.startswith("# node_index x y orientation fixed"):
            out_lines.append(f"# Clamped to canvas bounds: x in [0, {max_x}], y in [0, {max_y}]")
            inserted_note = True

        if line and not line.startswith("#"):
            parts = line.split()
            if len(parts) == 5 and parts[0].isdigit():
                node_idx, x_str, y_str, orient, fixed = parts
                x = float(x_str)
                y = float(y_str)
                new_x = clamp_value(x, min_x, max_x)
                new_y = clamp_value(y, min_y, max_y)
                if new_x != x or new_y != y:
                    clamp_count += 1
                    if new_x != x:
                        x_count += 1
                    if new_y != y:
                        y_count += 1
                out_lines.append(f"{node_idx} {new_x:.6f} {new_y:.6f} {orient} {fixed}")
                continue

        out_lines.append(line)

    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text("\n".join(out_lines) + "\n")

    print(f"input={src}")
    print(f"output={dst}")
    print(f"canvas_width={width}")
    print(f"canvas_height={height}")
    print(f"grid_cols={cols}")
    print(f"grid_rows={rows}")
    print(f"margin_grid_cells={args.margin_grid_cells}")
    print(f"margin_x={margin_x}")
    print(f"margin_y={margin_y}")
    print(f"clamped_nodes={clamp_count}")
    print(f"clamped_x={x_count}")
    print(f"clamped_y={y_count}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
