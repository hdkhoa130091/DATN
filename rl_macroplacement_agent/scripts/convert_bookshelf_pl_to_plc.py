#!/usr/bin/env python3
"""Convert a DREAMPlace/Bookshelf .pl placement into MacroPlacement .plc."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

from path_utils import add_repo_paths
from plc_utils import PlcFile

add_repo_paths()

from plc_client_os import PlacementCost


NODE_RE = re.compile(r'^\s*name:\s*"(?P<name>.*)"\s*$')


def parse_netlist_node_names(netlist_path: Path) -> dict[str, int]:
    names: dict[str, int] = {}
    node_index = 0
    for line in netlist_path.read_text(encoding="utf-8", errors="replace").splitlines():
        match = NODE_RE.match(line)
        if not match:
            continue
        name = match.group("name")
        names.setdefault(name, node_index)
        node_index += 1
    return names


def parse_bookshelf_pl(path: Path) -> dict[str, tuple[float, float, str | None]]:
    coords: dict[str, tuple[float, float, str | None]] = {}
    for raw_line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or line.lower().startswith("ucla"):
            continue
        fields = line.split()
        if len(fields) < 3:
            continue
        name = fields[0]
        try:
            x = float(fields[1])
            y = float(fields[2])
        except ValueError:
            continue
        orient = None
        if ":" in fields:
            colon_idx = fields.index(":")
            if colon_idx + 1 < len(fields):
                orient = fields[colon_idx + 1]
        coords[name] = (x, y, orient)
    return coords


def bookshelf_name_to_node_index(name: str, name_to_index: dict[str, int]) -> int | None:
    if name.isdigit():
        return int(name)
    for prefix in ("o", "node", "inst"):
        if name.startswith(prefix) and name[len(prefix) :].isdigit():
            return int(name[len(prefix) :])
    return name_to_index.get(name)


def main() -> int:
    parser = argparse.ArgumentParser(description="Convert DREAMPlace .pl output to .plc.")
    parser.add_argument("--dreamplace_pl", required=True, help="DREAMPlace Bookshelf .pl file")
    parser.add_argument("--template_plc", required=True, help="Initial .plc to preserve metadata")
    parser.add_argument("--netlist", required=True, help="MacroPlacement netlist.pb.txt")
    parser.add_argument("--out", required=True, help="Output .plc path")
    parser.add_argument(
        "--coords",
        choices=["lower_left", "center"],
        default="lower_left",
        help="Coordinate convention of the input .pl. DREAMPlace Bookshelf is usually lower_left.",
    )
    args = parser.parse_args()

    template = PlcFile(args.template_plc).load()
    netlist_path = Path(args.netlist)
    name_to_index = parse_netlist_node_names(netlist_path)
    bookshelf = parse_bookshelf_pl(Path(args.dreamplace_pl))
    evaluator = PlacementCost(str(netlist_path))

    converted = 0
    skipped = []
    for name, (x, y, orient) in bookshelf.items():
        node_index = bookshelf_name_to_node_index(name, name_to_index)
        if node_index is None or node_index not in template.node_data:
            skipped.append(name)
            continue
        current = template.get_node(node_index)
        new_x, new_y = x, y
        if args.coords == "lower_left":
            width, height = evaluator.get_node_width_height(node_index)
            new_x += width / 2.0
            new_y += height / 2.0
        template.set_node_position(
            node_index,
            new_x,
            new_y,
            orientation=orient or current["orientation"],
            fixed=current["fixed"],
        )
        converted += 1

    out_path = template.save(args.out)
    summary = {
        "dreamplace_pl": args.dreamplace_pl,
        "template_plc": args.template_plc,
        "out": str(out_path),
        "converted_nodes": converted,
        "skipped_nodes": len(skipped),
        "skipped_examples": skipped[:20],
    }
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
