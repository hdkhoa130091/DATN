#!/usr/bin/env python3
"""Smoke-test AlphaChip-like observations on a MacroPlacement benchmark."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from alphachip_like_features import (
    AlphaChipLikeFeatureExtractor,
    AlphaChipLikeObservationConfig,
)
from path_utils import add_repo_paths

add_repo_paths()

from plc_client_os import PlacementCost


def shape_summary(obs: dict) -> dict:
    return {
        key: list(value.shape) if hasattr(value, "shape") else type(value).__name__
        for key, value in obs.items()
    }


def maybe_run_model(obs: dict, max_nodes: int, max_edges: int, max_grid: int) -> dict:
    import torch

    from alphachip_like_model import (
        AlphaChipLikeActorCritic,
        AlphaChipLikeModelConfig,
    )

    model = AlphaChipLikeActorCritic(
        AlphaChipLikeModelConfig(
            max_num_nodes=max_nodes,
            max_num_edges=max_edges,
            max_grid_size=max_grid,
        )
    )
    torch_obs = {
        key: torch.as_tensor(value).unsqueeze(0)
        for key, value in obs.items()
        if key
        in {
            "metadata",
            "node_features",
            "sparse_adj_i",
            "sparse_adj_j",
            "sparse_adj_weight",
            "current_node",
            "mask",
        }
    }
    with torch.no_grad():
        logits, value = model(torch_obs)
    finite_logits = torch.isfinite(logits).sum().item()
    action = torch.argmax(logits, dim=-1).item()
    return {
        "logits_shape": list(logits.shape),
        "value_shape": list(value.shape),
        "value": float(value.squeeze().item()),
        "finite_logits": int(finite_logits),
        "argmax_action": int(action),
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Inspect AlphaChip-like graph observations."
    )
    parser.add_argument("--netlist", required=True)
    parser.add_argument("--init_plc", required=True)
    parser.add_argument("--out", help="Optional path to write JSON summary")
    parser.add_argument("--max_nodes", type=int, default=5000)
    parser.add_argument("--max_edges", type=int, default=70000)
    parser.add_argument("--max_grid", type=int, default=128)
    parser.add_argument("--max_macros", type=int, default=20)
    parser.add_argument("--run_model", action="store_true")
    args = parser.parse_args()

    plc = PlacementCost(args.netlist)
    plc.restore_placement(
        args.init_plc,
        ifInital=True,
        ifValidate=False,
        ifReadComment=True,
    )
    extractor = AlphaChipLikeFeatureExtractor(
        plc,
        AlphaChipLikeObservationConfig(
            max_num_nodes=args.max_nodes,
            max_num_edges=args.max_edges,
            max_grid_size=args.max_grid,
        ),
    )
    macros = extractor.movable_hard_macros(max_macros=args.max_macros)
    if not macros:
        raise RuntimeError("No movable hard macros found.")

    obs = extractor.observation_for_node(macros[0])
    summary = {
        "netlist": args.netlist,
        "init_plc": args.init_plc,
        "extractor": extractor.summary(),
        "selected_node": int(macros[0]),
        "selected_node_feature_index": int(obs["current_node"][0]),
        "selected_node_valid_actions": int(obs["mask"].sum()),
        "observation_shapes": shape_summary(obs),
    }

    if args.run_model:
        summary["model_forward"] = maybe_run_model(
            obs,
            max_nodes=args.max_nodes,
            max_edges=args.max_edges,
            max_grid=args.max_grid,
        )

    payload = json.dumps(summary, indent=2)
    print(payload)
    if args.out:
        out_path = Path(args.out)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(payload + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
