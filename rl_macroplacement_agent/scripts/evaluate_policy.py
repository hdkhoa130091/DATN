#!/usr/bin/env python3
"""Run a trained MaskablePPO macro placement policy once and report metrics."""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

from sb3_contrib import MaskablePPO

from macro_env import MacroPlacementEnv


def main() -> int:
    parser = argparse.ArgumentParser(description="Evaluate a trained MaskablePPO placer.")
    parser.add_argument("--model", required=True, help="Path to maskable_ppo_model.zip")
    parser.add_argument("--netlist", required=True, help="Path to netlist.pb.txt")
    parser.add_argument("--init_plc", required=True, help="Path to initial .plc")
    parser.add_argument("--out_dir", required=True, help="Directory for eval outputs")
    parser.add_argument("--max_macros", type=int, default=20)
    parser.add_argument("--deterministic", action="store_true")
    args = parser.parse_args()

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    env = MacroPlacementEnv(
        netlist=args.netlist,
        init_plc=args.init_plc,
        out_dir=str(out_dir),
        max_macros=args.max_macros,
    )
    model = MaskablePPO.load(args.model, env=env)

    obs, _ = env.reset()
    done = False
    start = time.perf_counter()
    steps = 0
    last_info = {}
    while not done:
        action_masks = env.action_masks()
        action, _ = model.predict(
            obs,
            deterministic=args.deterministic,
            action_masks=action_masks,
        )
        obs, _, terminated, truncated, last_info = env.step(int(action))
        done = terminated or truncated
        steps += 1
    runtime = time.perf_counter() - start

    final_plc = out_dir / "ppo_final.plc"
    env.current_plc.save(final_plc)
    final_cost = float(last_info.get("cost", env.previous_cost))
    env._save_best_if_needed(final_cost)

    summary = {
        "method": "MaskablePPO",
        "model": args.model,
        "netlist": args.netlist,
        "init_plc": args.init_plc,
        "final_plc": str(final_plc),
        "best_plc": str(env.best_plc_path),
        "cost": final_cost,
        "best_cost": env.best_cost,
        "wirelength": env._safe_metric(env.evaluator.get_wirelength),
        "density_cost": env._safe_metric(env.evaluator.get_density_cost),
        "congestion_cost": env._safe_metric(env.evaluator.get_congestion_cost),
        "runtime_sec": runtime,
        "steps": steps,
    }
    out_path = out_dir / "ppo_eval_summary.json"
    out_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
