#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path


def load_last_json(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    decoder = json.JSONDecoder()
    for idx in range(len(text) - 1, -1, -1):
        if text[idx] != "{":
            continue
        try:
            obj, end = decoder.raw_decode(text[idx:])
        except json.JSONDecodeError:
            continue
        if idx + end <= len(text):
            return obj
    raise ValueError(f"Could not locate JSON summary in {path}")


def load_history(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def to_float(value):
    if value in ("", None):
        return None
    return float(value)


def extract_row(seed_dir: Path) -> dict:
    log_path = seed_dir / "train.log"
    history_path = seed_dir / "alphachip_like_training_history.csv"
    summary_path = seed_dir / "alphachip_like_train_summary.json"
    history = load_history(history_path)
    last_history = history[-1]
    best_final_cost = min(float(row["final_cost"]) for row in history)
    initial_cost = float(last_history["initial_cost"])
    final_cost = float(last_history["final_cost"])
    best_improvement = (initial_cost - best_final_cost) / initial_cost * 100.0
    final_improvement = (initial_cost - final_cost) / initial_cost * 100.0

    if summary_path.exists():
        summary = json.loads(summary_path.read_text(encoding="utf-8"))
        last_episode = summary["last_episode"]
        episodes = summary["episodes"]
        rollout_episodes = summary["rollout_episodes"]
        best_cost = summary["best_cost"]
        episode_reward = last_episode["episode_reward"]
        wirelength = last_episode["wirelength"]
        density_cost = last_episode["density_cost"]
        congestion_cost = last_episode["congestion_cost"]
        loss = last_episode["loss"]
        policy_loss = last_episode["policy_loss"]
        value_loss = last_episode["value_loss"]
        entropy = last_episode["entropy"]
        approx_kl = last_episode["approx_kl"]
        clip_fraction = last_episode["clip_fraction"]
        train_runtime_sec = summary["train_runtime_sec"]
    elif log_path.exists():
        summary = load_last_json(log_path)
        last_episode = summary["last_episode"]
        episodes = summary["episodes"]
        rollout_episodes = summary["rollout_episodes"]
        best_cost = summary["best_cost"]
        episode_reward = last_episode["episode_reward"]
        wirelength = last_episode["wirelength"]
        density_cost = last_episode["density_cost"]
        congestion_cost = last_episode["congestion_cost"]
        loss = last_episode["loss"]
        policy_loss = last_episode["policy_loss"]
        value_loss = last_episode["value_loss"]
        entropy = last_episode["entropy"]
        approx_kl = last_episode["approx_kl"]
        clip_fraction = last_episode["clip_fraction"]
        train_runtime_sec = summary["train_runtime_sec"]
    else:
        episodes = len(history)
        rollout_episodes = None
        best_cost = best_final_cost
        episode_reward = to_float(last_history["episode_reward"])
        wirelength = None
        density_cost = None
        congestion_cost = None
        loss = to_float(last_history["loss"])
        policy_loss = to_float(last_history["policy_loss"])
        value_loss = to_float(last_history["value_loss"])
        entropy = to_float(last_history["entropy"])
        approx_kl = to_float(last_history["approx_kl"])
        clip_fraction = to_float(last_history["clip_fraction"])
        train_runtime_sec = None

    return {
        "seed": seed_dir.name.replace("seed_", ""),
        "episodes": episodes,
        "rollout_episodes": rollout_episodes,
        "best_cost": best_cost,
        "initial_cost": initial_cost,
        "final_cost": final_cost,
        "best_cost_from_history": best_final_cost,
        "best_improvement_pct": best_improvement,
        "final_improvement_pct": final_improvement,
        "episode_reward": episode_reward,
        "wirelength": wirelength,
        "density_cost": density_cost,
        "congestion_cost": congestion_cost,
        "loss": loss,
        "policy_loss": policy_loss,
        "value_loss": value_loss,
        "entropy": entropy,
        "approx_kl": approx_kl,
        "clip_fraction": clip_fraction,
        "train_runtime_sec": train_runtime_sec,
        "last_history_reward": to_float(last_history["episode_reward"]),
        "last_history_loss": to_float(last_history["loss"]),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", required=True, help="Experiment root containing seed_* dirs.")
    parser.add_argument("--output", help="Optional CSV output path.")
    args = parser.parse_args()

    root = Path(args.root)
    if not root.exists():
        raise SystemExit(f"Experiment root does not exist: {root}")
    seed_dirs = sorted(path for path in root.iterdir() if path.is_dir() and path.name.startswith("seed_"))
    if not seed_dirs:
        raise SystemExit(f"No seed_* directories found under {root}")

    rows = [extract_row(seed_dir) for seed_dir in seed_dirs]
    fieldnames = list(rows[0].keys())

    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with output_path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)

    print(json.dumps(rows, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
