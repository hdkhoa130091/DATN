#!/usr/bin/env python3
"""Utilities for reading and updating Circuit Training .plc files."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def _safe_int(value, default=None):
    try:
        return int(value)
    except Exception:
        return default


def _safe_float(value, default=None):
    try:
        return float(value)
    except Exception:
        return default


class PlcFile:
    """A lightweight .plc editor that preserves comments and formatting."""

    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.lines: list[str] = []
        self.node_rows: dict[int, int] = {}
        self.node_data: dict[int, dict] = {}
        self.columns = None
        self.rows = None
        self.width = None
        self.height = None
        self.node_header_line = None

    def load(self) -> "PlcFile":
        self.lines = self.path.read_text(encoding="utf-8", errors="replace").splitlines(True)
        self.node_rows = {}
        self.node_data = {}
        self.columns = None
        self.rows = None
        self.width = None
        self.height = None
        self.node_header_line = None

        for idx, line in enumerate(self.lines):
            stripped = line.strip()
            if not stripped:
                continue

            if stripped.startswith("#"):
                self._parse_comment_metadata(stripped)
                if stripped.lower().startswith("# node_index x y orientation fixed"):
                    self.node_header_line = idx
                continue

            fields = stripped.split()
            if fields and fields[0].isdigit() and len(fields) >= 5:
                node_index = int(fields[0])
                self.node_rows[node_index] = idx
                self.node_data[node_index] = {
                    "x": float(fields[1]),
                    "y": float(fields[2]),
                    "orientation": fields[3],
                    "fixed": int(fields[4]),
                }

        return self

    def _parse_comment_metadata(self, stripped: str) -> None:
        tokens = stripped.replace(":", " ").split()
        for idx, token in enumerate(tokens):
            token_lower = token.lower()
            if token_lower == "columns" and idx + 1 < len(tokens):
                self.columns = _safe_int(tokens[idx + 1], self.columns)
            elif token_lower == "rows" and idx + 1 < len(tokens):
                self.rows = _safe_int(tokens[idx + 1], self.rows)
            elif token_lower == "width" and idx + 1 < len(tokens):
                self.width = _safe_float(tokens[idx + 1], self.width)
            elif token_lower == "height" and idx + 1 < len(tokens):
                self.height = _safe_float(tokens[idx + 1], self.height)

    def get_node_indices(self) -> list[int]:
        return sorted(self.node_rows.keys())

    def get_node(self, node_index: int) -> dict:
        if node_index not in self.node_data:
            raise KeyError(f"Node index not found in .plc: {node_index}")
        return dict(self.node_data[node_index])

    def set_node_position(self, node_index: int, x: float, y: float, orientation=None, fixed=None) -> None:
        if node_index not in self.node_rows:
            raise KeyError(f"Node index not found in .plc: {node_index}")

        current = self.node_data[node_index]
        if orientation is None:
            orientation = current["orientation"]
        if fixed is None:
            fixed = current["fixed"]

        line_idx = self.node_rows[node_index]
        self.lines[line_idx] = f"{node_index} {x:.6f} {y:.6f} {orientation} {int(fixed)}\n"
        self.node_data[node_index] = {
            "x": float(x),
            "y": float(y),
            "orientation": orientation,
            "fixed": int(fixed),
        }

    def save(self, out_path: str | Path) -> Path:
        out_path = Path(out_path)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text("".join(self.lines), encoding="utf-8")
        return out_path

    def summary(self) -> dict:
        return {
            "path": str(self.path),
            "columns": self.columns,
            "rows": self.rows,
            "width": self.width,
            "height": self.height,
            "node_count": len(self.node_rows),
            "node_header_line": self.node_header_line,
            "min_node_index": min(self.node_rows) if self.node_rows else None,
            "max_node_index": max(self.node_rows) if self.node_rows else None,
        }


def main() -> int:
    parser = argparse.ArgumentParser(description="Inspect or edit a .plc file.")
    parser.add_argument("--plc", required=True, help="Input .plc file")
    parser.add_argument("--summary", action="store_true", help="Print parsed summary")
    parser.add_argument("--set-node", type=int, help="Node index to update")
    parser.add_argument("--x", type=float, help="New x coordinate")
    parser.add_argument("--y", type=float, help="New y coordinate")
    parser.add_argument("--orientation", help="Optional orientation override")
    parser.add_argument("--fixed", type=int, choices=[0, 1], help="Optional fixed flag override")
    parser.add_argument("--out", help="Output .plc path when editing")
    args = parser.parse_args()

    plc = PlcFile(args.plc).load()

    if args.summary:
        print(json.dumps(plc.summary(), indent=2))

    if args.set_node is not None:
        if args.x is None or args.y is None or not args.out:
            raise SystemExit("--set-node requires --x, --y, and --out")
        plc.set_node_position(
            args.set_node,
            args.x,
            args.y,
            orientation=args.orientation,
            fixed=args.fixed,
        )
        out_path = plc.save(args.out)
        print(json.dumps({"saved_to": str(out_path), "node": plc.get_node(args.set_node)}, indent=2))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
