#!/usr/bin/env python3
"""Inspect a MacroPlacement dataset bundle for RL experiments."""

import argparse
import json
from pathlib import Path

from path_utils import add_repo_paths

add_repo_paths()

try:
    from plc_client_os import PlacementCost
except Exception as exc:  # pragma: no cover
    PlacementCost = None
    IMPORT_ERROR = repr(exc)
else:
    IMPORT_ERROR = None


def parse_plc_metadata(plc_path: Path) -> dict:
    """Extract lightweight metadata from a .plc file without assuming full format."""
    metadata = {
        "columns": None,
        "rows": None,
        "width": None,
        "height": None,
        "placement_rows": 0,
        "comment_lines": 0,
    }

    with plc_path.open("r", encoding="utf-8", errors="replace") as handle:
        for raw_line in handle:
            line = raw_line.strip()
            if not line:
                continue

            if line.startswith("#"):
                metadata["comment_lines"] += 1
                lowered = line.lower()
                tokens = line.replace(":", " ").split()
                for idx, token in enumerate(tokens):
                    token_lower = token.lower()
                    if token_lower == "columns" and idx + 1 < len(tokens):
                        metadata["columns"] = safe_int(tokens[idx + 1], metadata["columns"])
                    elif token_lower == "rows" and idx + 1 < len(tokens):
                        metadata["rows"] = safe_int(tokens[idx + 1], metadata["rows"])
                    elif token_lower == "width" and idx + 1 < len(tokens):
                        metadata["width"] = safe_float(tokens[idx + 1], metadata["width"])
                    elif token_lower == "height" and idx + 1 < len(tokens):
                        metadata["height"] = safe_float(tokens[idx + 1], metadata["height"])

                if "columns" in lowered and "rows" in lowered:
                    continue

            fields = line.split()
            if fields and fields[0].isdigit() and len(fields) >= 5:
                metadata["placement_rows"] += 1

    return metadata


def safe_int(value: str, default):
    try:
        return int(value)
    except Exception:
        return default


def safe_float(value: str, default):
    try:
        return float(value)
    except Exception:
        return default


def build_plc_summary(plc_path: Path) -> dict:
    summary = {
        "path": str(plc_path),
        "exists": plc_path.is_file(),
    }
    if not summary["exists"]:
        return summary

    summary["size_bytes"] = plc_path.stat().st_size
    summary["metadata"] = parse_plc_metadata(plc_path)
    return summary


def inspect_with_placement_cost(netlist_path: Path, plc_path: Path | None) -> dict:
    summary = {
        "placement_cost_import_ok": PlacementCost is not None,
    }
    if PlacementCost is None:
        summary["placement_cost_import_error"] = IMPORT_ERROR
        return summary

    plc = PlacementCost(str(netlist_path))
    summary["block_name"] = plc.get_block_name()
    summary["project_name"] = plc.get_project_name()
    summary["hard_macros"] = plc.get_hard_macros_count()
    summary["soft_macros"] = plc.get_soft_macros_count()
    summary["ports"] = plc.get_ports_count()
    summary["macro_indices_count"] = len(plc.get_macro_indices())

    if plc_path is not None:
        plc.restore_placement(
            str(plc_path),
            ifInital=True,
            ifValidate=False,
            ifReadComment=True,
        )

    width, height = plc.get_canvas_width_height()
    cols, rows = plc.get_grid_num_columns_rows()
    summary["canvas_width"] = width
    summary["canvas_height"] = height
    summary["grid_columns"] = cols
    summary["grid_rows"] = rows
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description="Inspect RL macroplacement dataset files.")
    parser.add_argument("--netlist", required=True, help="Path to netlist.pb.txt")
    parser.add_argument("--initial_plc", help="Path to initial.plc")
    parser.add_argument("--legalized_plc", help="Path to legalized.plc")
    parser.add_argument("--out", help="Optional JSON output path")
    args = parser.parse_args()

    netlist_path = Path(args.netlist)
    initial_plc = Path(args.initial_plc) if args.initial_plc else None
    legalized_plc = Path(args.legalized_plc) if args.legalized_plc else None

    result = {
        "netlist": {
            "path": str(netlist_path),
            "exists": netlist_path.is_file(),
        },
        "initial_plc": build_plc_summary(initial_plc) if initial_plc else None,
        "legalized_plc": build_plc_summary(legalized_plc) if legalized_plc else None,
    }

    if netlist_path.is_file():
        result["netlist"]["size_bytes"] = netlist_path.stat().st_size
        try:
            preferred_plc = legalized_plc if legalized_plc and legalized_plc.is_file() else initial_plc
            result["placement_cost_summary"] = inspect_with_placement_cost(netlist_path, preferred_plc)
        except Exception as exc:
            result["placement_cost_summary"] = {
                "placement_cost_import_ok": PlacementCost is not None,
                "error": repr(exc),
            }

    if args.out:
        out_path = Path(args.out)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(result, indent=2), encoding="utf-8")

    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
