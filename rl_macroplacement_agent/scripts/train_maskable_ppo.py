#!/usr/bin/env python3
"""Train a minimal MaskablePPO agent for macro placement smoke tests."""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

from sb3_contrib import MaskablePPO
from stable_baselines3.common.callbacks import BaseCallback

from macro_env import MacroPlacementEnv


class ProgressCallback(BaseCallback):
    """Persist lightweight training progress for debugging and reports."""

    def __init__(self, out_dir: Path):
        super().__init__()
        self.out_dir = out_dir
        self.progress_path = out_dir / "training_progress.json"

    def _on_step(self) -> bool:
        if self.n_calls % 50 != 0:
            return True

        env = self.training_env.envs[0].unwrapped
        payload = {
            "timesteps": self.num_timesteps,
            "best_cost": getattr(env, "best_cost", None),
            "previous_cost": getattr(env, "previous_cost", None),
            "episode_idx": getattr(env, "episode_idx", None),
        }
        self.progress_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        return True


def main() -> int:
    parser = argparse.ArgumentParser(description="Train MaskablePPO for macro placement.")
    parser.add_argument("--netlist", required=True)
    parser.add_argument("--init_plc", required=True)
    parser.add_argument("--out_dir", required=True)
    parser.add_argument("--steps", type=int, default=1000)
    parser.add_argument("--max_macros", type=int, default=20)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--n_steps", type=int, default=128)
    parser.add_argument("--batch_size", type=int, default=64)
    args = parser.parse_args()

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    env = MacroPlacementEnv(
        netlist=args.netlist,
        init_plc=args.init_plc,
        out_dir=str(out_dir),
        max_macros=args.max_macros,
    )

    model = MaskablePPO(
        "MlpPolicy",
        env,
        verbose=1,
        n_steps=args.n_steps,
        batch_size=args.batch_size,
        gamma=0.99,
        learning_rate=3e-4,
        seed=args.seed,
    )

    callback = ProgressCallback(out_dir)
    train_start = time.perf_counter()
    model.learn(total_timesteps=args.steps, callback=callback)
    train_runtime = time.perf_counter() - train_start
    model_path = out_dir / "maskable_ppo_model"
    model.save(str(model_path))

    summary = {
        "model_path": str(model_path) + ".zip",
        "best_cost": env.best_cost,
        "best_plc": str(env.best_plc_path),
        "best_proxy": str(env.best_proxy_path),
        "reward_history_csv": str(env.history_csv_path),
        "steps": args.steps,
        "max_macros": args.max_macros,
        "n_steps": args.n_steps,
        "batch_size": args.batch_size,
        "train_runtime_sec": train_runtime,
    }
    (out_dir / "train_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
