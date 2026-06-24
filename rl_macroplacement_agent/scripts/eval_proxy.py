#!/usr/bin/env python3
"""Evaluate MacroPlacement proxy metrics for a given netlist and placement."""

import argparse
import json
from pathlib import Path

from path_utils import add_repo_paths

add_repo_paths()

from plc_client_os import PlacementCost
from train_ppo import create_plc, get_proxy_cost


def safe_call(name, fn):
    try:
        return {name: fn()}
    except Exception as exc:
        return {f"{name}_error": repr(exc)}


def main() -> int:
    parser = argparse.ArgumentParser(description="Evaluate proxy cost on a .plc placement.")
    parser.add_argument("--netlist", required=True, help="Path to netlist.pb.txt")
    parser.add_argument("--plc", required=True, help="Path to placement .plc file")
    parser.add_argument("--out", required=True, help="Path to write result JSON")
    parser.add_argument("--wirelength_weight", type=float, default=1.0)
    parser.add_argument("--density_weight", type=float, default=0.5)
    parser.add_argument("--congestion_weight", type=float, default=0.5)
    args = parser.parse_args()

    netlist_path = Path(args.netlist)
    plc_path = Path(args.plc)
    out_path = Path(args.out)

    if not netlist_path.is_file():
        raise FileNotFoundError(f"Netlist not found: {netlist_path}")
    if not plc_path.is_file():
        raise FileNotFoundError(f"Placement file not found: {plc_path}")

    plc = create_plc(str(netlist_path), str(plc_path))

    width, height = plc.get_canvas_width_height()
    cols, rows = plc.get_grid_num_columns_rows()

    result = {
        "netlist": str(netlist_path),
        "plc": str(plc_path),
        "canvas_width": width,
        "canvas_height": height,
        "grid_columns": cols,
        "grid_rows": rows,
        "hard_macros": plc.get_hard_macros_count(),
        "soft_macros": plc.get_soft_macros_count(),
        "ports": plc.get_ports_count(),
        "macro_indices_count": len(plc.get_macro_indices()),
    }

    proxy_cost, components = get_proxy_cost(
        plc,
        wirelength_weight=args.wirelength_weight,
        density_weight=args.density_weight,
        congestion_weight=args.congestion_weight,
    )
    result["proxy_cost"] = proxy_cost
    result["wirelength_weight"] = args.wirelength_weight
    result["density_weight"] = args.density_weight
    result["congestion_weight"] = args.congestion_weight
    result.update(safe_call("wirelength", plc.get_wirelength))
    result["wirelength_cost"] = components["wirelength_cost"]
    result["density_cost"] = components["density_cost"]
    result["congestion_cost"] = components["congestion_cost"]

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(result, indent=2), encoding="utf-8")

    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
