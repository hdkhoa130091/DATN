#!/usr/bin/env python3
"""Evaluate a trained AlphaChip-like PPO policy once and save placement outputs."""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import torch

from alphachip_like_features import AlphaChipLikeFeatureExtractor, AlphaChipLikeObservationConfig
from alphachip_like_model import AlphaChipLikeActorCritic, AlphaChipLikeModelConfig
from train_alphachip_like_ppo import create_plc, obs_to_torch, padded_to_real_action, safe_metric


def main() -> int:
    parser = argparse.ArgumentParser(description="Evaluate AlphaChip-like PPO placer.")
    parser.add_argument("--model", required=True)
    parser.add_argument("--netlist", required=True)
    parser.add_argument("--init_plc", required=True)
    parser.add_argument("--out_dir", required=True)
    parser.add_argument("--max_macros", type=int, default=5)
    parser.add_argument("--max_nodes", type=int, default=1024)
    parser.add_argument("--max_edges", type=int, default=10000)
    parser.add_argument("--max_grid", type=int, default=32)
    parser.add_argument("--device", default="cuda" if torch.cuda.is_available() else "cpu")
    parser.add_argument("--deterministic", action="store_true")
    args = parser.parse_args()

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    device = torch.device(args.device)

    model = AlphaChipLikeActorCritic(
        AlphaChipLikeModelConfig(
            max_num_nodes=args.max_nodes,
            max_num_edges=args.max_edges,
            max_grid_size=args.max_grid,
        )
    ).to(device)
    state_dict = torch.load(args.model, map_location=device, weights_only=True)
    model.load_state_dict(state_dict)
    model.eval()

    plc = create_plc(args.netlist, args.init_plc)
    extractor = AlphaChipLikeFeatureExtractor(
        plc,
        AlphaChipLikeObservationConfig(
            max_num_nodes=args.max_nodes,
            max_num_edges=args.max_edges,
            max_grid_size=args.max_grid,
        ),
    )
    macros = extractor.movable_hard_macros(max_macros=args.max_macros)
    initial_cost = float(plc.get_cost())
    # Circuit Training resets placement by unplacing movable nodes before the
    # hard-macro sequence starts. Keep evaluation aligned with training.
    plc.unplace_all_nodes()
    final_cost = initial_cost
    invalid_action = None

    start = time.perf_counter()
    steps = 0
    for node_idx in macros:
        obs = extractor.observation_for_node(node_idx)
        if not obs["mask"].any():
            invalid_action = -1
            break
        with torch.no_grad():
            action_t, _, _ = model.act(obs_to_torch(obs, device), deterministic=args.deterministic)
        padded_action = int(action_t.item())
        real_action = padded_to_real_action(
            padded_action,
            extractor.grid_cols,
            extractor.grid_rows,
            args.max_grid,
        )
        valid = real_action is not None and bool(obs["mask"][padded_action])
        if not valid:
            invalid_action = padded_action
            break
        plc.place_node(node_idx, real_action)
        plc.FLAG_UPDATE_WIRELENGTH = True
        plc.FLAG_UPDATE_DENSITY = True
        plc.FLAG_UPDATE_CONGESTION = True
        final_cost = float(plc.get_cost())
        steps += 1
    runtime = time.perf_counter() - start

    final_plc = out_dir / "alphachip_like_final.plc"
    plc.save_placement(str(final_plc))
    summary = {
        "method": "AlphaChipLikePPO",
        "model": args.model,
        "netlist": args.netlist,
        "init_plc": args.init_plc,
        "final_plc": str(final_plc),
        "initial_cost": initial_cost,
        "cost": final_cost,
        "best_cost": final_cost,
        "wirelength": safe_metric(plc.get_wirelength),
        "density_cost": safe_metric(plc.get_density_cost),
        "congestion_cost": safe_metric(plc.get_congestion_cost),
        "runtime_sec": runtime,
        "steps": steps,
        "invalid_action": invalid_action,
    }
    out_path = out_dir / "alphachip_like_eval_summary.json"
    out_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
