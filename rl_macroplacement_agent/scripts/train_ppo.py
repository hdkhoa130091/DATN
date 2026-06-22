#!/usr/bin/env python3
"""Train a small custom PyTorch PPO loop with graph observations.

This is the first integration point for:

  AlphaChipLikeFeatureExtractor -> AlphaChipLikeActorCritic -> AlphaChipLikePPOAgent

It is intentionally a smoke-test trainer, not a full distributed AlphaChip
replacement. It uses terminal placement reward, graph observations, action
masks, and the inspectable PyTorch PPO code in this repository.
"""

from __future__ import annotations

import argparse
import csv
import json
import time
from pathlib import Path

import numpy as np
import torch

from ppo_agent import AlphaChipLikePPOAgent, PPOConfig, RolloutBatch
from obs_features import (
    AlphaChipLikeFeatureExtractor,
    AlphaChipLikeObservationConfig,
)
from policy_model import AlphaChipLikeActorCritic, AlphaChipLikeModelConfig
from path_utils import add_repo_paths
from placement_cost_optimizations import install_fast_wirelength_cache

add_repo_paths()

from plc_client_os import PlacementCost


def obs_to_torch(obs: dict[str, np.ndarray], device: torch.device) -> dict[str, torch.Tensor]:
    keys = {
        "metadata",
        "node_features",
        "sparse_adj_i",
        "sparse_adj_j",
        "sparse_adj_weight",
        "current_node",
        "mask",
    }
    return {
        key: torch.as_tensor(value, device=device).unsqueeze(0)
        for key, value in obs.items()
        if key in keys
    }


def stack_obs(observations: list[dict[str, np.ndarray]], device: torch.device) -> dict[str, torch.Tensor]:
    keys = {
        "metadata",
        "node_features",
        "sparse_adj_i",
        "sparse_adj_j",
        "sparse_adj_weight",
        "current_node",
        "mask",
    }
    return {
        key: torch.as_tensor(np.stack([obs[key] for obs in observations]), device=device)
        for key in keys
    }


def concat_rollout_batches(batches: list[RolloutBatch]) -> RolloutBatch:
    """Concatenate complete episodes into one PPO update batch."""
    advantages = torch.cat([batch.advantages for batch in batches], dim=0)
    advantages = (advantages - advantages.mean()) / (advantages.std() + 1.0e-8)
    return RolloutBatch(
        obs={
            key: torch.cat([batch.obs[key] for batch in batches], dim=0)
            for key in batches[0].obs
        },
        actions=torch.cat([batch.actions for batch in batches], dim=0),
        old_log_probs=torch.cat([batch.old_log_probs for batch in batches], dim=0),
        rewards=torch.cat([batch.rewards for batch in batches], dim=0),
        dones=torch.cat([batch.dones for batch in batches], dim=0),
        values=torch.cat([batch.values for batch in batches], dim=0),
        returns=torch.cat([batch.returns for batch in batches], dim=0),
        advantages=advantages,
    )


def padded_to_real_action(action: int, grid_cols: int, grid_rows: int, max_grid: int) -> int | None:
    top = (max_grid - grid_rows) // 2
    left = (max_grid - grid_cols) // 2
    row = action // max_grid - top
    col = action % max_grid - left
    if row < 0 or row >= grid_rows or col < 0 or col >= grid_cols:
        return None
    return row * grid_cols + col


def safe_metric(fn):
    try:
        return fn()
    except Exception as exc:
        return {"error": repr(exc)}


def format_seconds(seconds: float) -> str:
    seconds = max(float(seconds), 0.0)
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = seconds % 60.0
    if hours:
        return f"{hours:02d}:{minutes:02d}:{secs:04.1f}"
    return f"{minutes:02d}:{secs:04.1f}"


def get_proxy_cost(
    plc: PlacementCost,
    *,
    wirelength_weight: float = 1.0,
    density_weight: float = 0.5,
    congestion_weight: float = 0.5,
) -> tuple[float, dict[str, float | dict[str, str]]]:
    """Match the default MacroPlacement proxy cost used by Circuit Training."""
    wirelength = safe_metric(plc.get_cost)
    density = safe_metric(plc.get_density_cost)
    congestion = safe_metric(plc.get_congestion_cost)

    proxy_cost = 0.0
    if not isinstance(wirelength, dict):
        proxy_cost += wirelength_weight * float(wirelength)
    if not isinstance(density, dict):
        proxy_cost += density_weight * float(density)
    if not isinstance(congestion, dict):
        proxy_cost += congestion_weight * float(congestion)

    return proxy_cost, {
        "wirelength_cost": wirelength,
        "density_cost": density,
        "congestion_cost": congestion,
    }


def create_plc(netlist: str, init_plc: str) -> PlacementCost:
    plc = PlacementCost(netlist)
    plc.restore_placement(
        init_plc,
        ifInital=True,
        ifValidate=False,
        ifReadComment=True,
    )
    install_fast_wirelength_cache(plc)
    return plc


def collect_episode(
    *,
    model: AlphaChipLikeActorCritic,
    netlist: str,
    init_plc: str,
    device: torch.device,
    max_nodes: int,
    max_edges: int,
    max_grid: int,
    max_macros: int,
    reward_scale: float,
    wirelength_weight: float,
    density_weight: float,
    congestion_weight: float,
    deterministic: bool = False,
    plc: PlacementCost | None = None,
    extractor: AlphaChipLikeFeatureExtractor | None = None,
    progress_every_steps: int = 0,
    episode_idx: int | None = None,
    total_episodes: int | None = None,
) -> tuple[RolloutBatch, dict, list[dict], str | None]:
    if plc is None:
        plc = create_plc(netlist, init_plc)
    else:
        plc.restore_placement(
            init_plc,
            ifInital=True,
            ifValidate=False,
            ifReadComment=True,
        )
    if extractor is None:
        extractor = AlphaChipLikeFeatureExtractor(
            plc,
            AlphaChipLikeObservationConfig(
                max_num_nodes=max_nodes,
                max_num_edges=max_edges,
                max_grid_size=max_grid,
            ),
        )
    macros = extractor.movable_hard_macros(max_macros=max_macros)
    if not macros:
        raise RuntimeError("No movable hard macros found.")

    observations: list[dict[str, np.ndarray]] = []
    actions: list[int] = []
    log_probs: list[float] = []
    values: list[float] = []
    rewards = [0.0 for _ in macros]
    dones = [0.0 for _ in macros]
    step_rows: list[dict] = []
    invalid_action = None

    initial_cost, initial_components = get_proxy_cost(
        plc,
        wirelength_weight=wirelength_weight,
        density_weight=density_weight,
        congestion_weight=congestion_weight,
    )
    # Match Circuit Training's episode reset semantics: all movable nodes are
    # unplaced before hard-macro placement begins. Otherwise macros that are due
    # to be placed later remain at their initial locations and incorrectly block
    # the action mask, which can make larger episodes infeasible.
    plc.unplace_all_nodes()
    final_cost = initial_cost
    final_components = initial_components
    episode_start = time.perf_counter()
    total_steps = len(macros)

    if episode_idx is not None and total_episodes is not None:
        print(
            f"[train] episode {episode_idx + 1}/{total_episodes} started | "
            f"initial_cost={initial_cost:.6f} | macros={total_steps}",
            flush=True,
        )

    model.eval()
    for step_idx, node_idx in enumerate(macros):
        obs = extractor.observation_for_node(node_idx)
        if not np.any(obs["mask"]):
            invalid_action = -1
            rewards[step_idx] = -4.0
            dones[step_idx] = 1.0
            observations.append(obs)
            actions.append(0)
            log_probs.append(0.0)
            values.append(0.0)
            step_rows.append(
                {
                    "step": step_idx + 1,
                    "node_idx": node_idx,
                    "padded_action": None,
                    "real_action": None,
                    "valid": 0,
                    "proxy_cost": final_cost,
                    "reward": rewards[step_idx],
                }
            )
            if progress_every_steps > 0:
                elapsed = time.perf_counter() - episode_start
                print(
                    f"[train] episode {episode_idx + 1 if episode_idx is not None else '?'} "
                    f"step {step_idx + 1}/{total_steps} | invalid_mask | "
                    f"proxy_cost={final_cost:.6f} | elapsed={format_seconds(elapsed)}",
                    flush=True,
                )
            break
        torch_obs = obs_to_torch(obs, device)
        with torch.no_grad():
            action_t, log_prob_t, value_t = model.act(
                torch_obs, deterministic=deterministic
            )

        padded_action = int(action_t.item())
        real_action = padded_to_real_action(
            padded_action,
            extractor.grid_cols,
            extractor.grid_rows,
            max_grid,
        )
        valid = real_action is not None and bool(obs["mask"][padded_action])
        observations.append(obs)
        actions.append(padded_action)
        log_probs.append(float(log_prob_t.item()))
        values.append(float(value_t.item()))

        if not valid:
            invalid_action = padded_action
            rewards[step_idx] = -4.0
            dones[step_idx] = 1.0
            step_rows.append(
                {
                    "step": step_idx + 1,
                    "node_idx": node_idx,
                    "padded_action": padded_action,
                    "real_action": real_action,
                    "valid": 0,
                    "proxy_cost": final_cost,
                    "reward": rewards[step_idx],
                }
            )
            break

        plc.place_node(node_idx, real_action)
        plc.FLAG_UPDATE_WIRELENGTH = True
        plc.FLAG_UPDATE_DENSITY = True
        plc.FLAG_UPDATE_CONGESTION = True
        final_cost, final_components = get_proxy_cost(
            plc,
            wirelength_weight=wirelength_weight,
            density_weight=density_weight,
            congestion_weight=congestion_weight,
        )
        step_rows.append(
            {
                "step": step_idx + 1,
                "node_idx": node_idx,
                "padded_action": padded_action,
                "real_action": real_action,
                "valid": 1,
                "proxy_cost": final_cost,
                "reward": 0.0,
            }
        )

        should_log = (
            progress_every_steps > 0
            and (
                step_idx == 0
                or (step_idx + 1) % progress_every_steps == 0
                or step_idx + 1 == total_steps
            )
        )
        if should_log:
            elapsed = time.perf_counter() - episode_start
            print(
                f"[train] episode {episode_idx + 1 if episode_idx is not None else '?'} "
                f"step {step_idx + 1}/{total_steps} | "
                f"proxy_cost={final_cost:.6f} | elapsed={format_seconds(elapsed)}",
                flush=True,
            )

    terminal_idx = len(observations) - 1
    if terminal_idx >= 0 and invalid_action is None:
        rewards[terminal_idx] = (initial_cost - final_cost) * reward_scale
        dones[terminal_idx] = 1.0
        step_rows[terminal_idx]["reward"] = rewards[terminal_idx]

    used_len = len(observations)
    rewards_t = torch.as_tensor(rewards[:used_len], dtype=torch.float32, device=device)
    dones_t = torch.as_tensor(dones[:used_len], dtype=torch.float32, device=device)
    values_t = torch.as_tensor(values, dtype=torch.float32, device=device)
    old_log_probs_t = torch.as_tensor(log_probs, dtype=torch.float32, device=device)
    actions_t = torch.as_tensor(actions, dtype=torch.int64, device=device)

    batch = RolloutBatch(
        obs=stack_obs(observations, device),
        actions=actions_t,
        old_log_probs=old_log_probs_t,
        rewards=rewards_t,
        dones=dones_t,
        values=values_t,
    )
    summary = {
        "initial_cost": initial_cost,
        "final_cost": final_cost,
        "episode_reward": float(rewards_t.sum().item()),
        "steps": used_len,
        "invalid_action": invalid_action,
        "wirelength": safe_metric(plc.get_wirelength),
        "wirelength_cost": final_components["wirelength_cost"],
        "density_cost": final_components["density_cost"],
        "congestion_cost": final_components["congestion_cost"],
        "episode_runtime_sec": time.perf_counter() - episode_start,
    }
    return batch, summary, step_rows, None


def main() -> int:
    parser = argparse.ArgumentParser(description="Train custom AlphaChip-like PPO.")
    parser.add_argument("--netlist", required=True)
    parser.add_argument("--init_plc", required=True)
    parser.add_argument("--out_dir", required=True)
    parser.add_argument("--episodes", type=int, default=2)
    parser.add_argument("--rollout_episodes", type=int, default=8)
    parser.add_argument("--max_macros", type=int, default=5)
    parser.add_argument("--max_nodes", type=int, default=1024)
    parser.add_argument("--max_edges", type=int, default=10000)
    parser.add_argument("--max_grid", type=int, default=32)
    parser.add_argument("--reward_scale", type=float, default=1000.0)
    parser.add_argument("--wirelength_weight", type=float, default=1.0)
    parser.add_argument("--density_weight", type=float, default=0.5)
    parser.add_argument("--congestion_weight", type=float, default=0.5)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--resume_from", help="Optional actor-critic checkpoint to continue from.")
    parser.add_argument("--stage_name", default="")
    parser.add_argument("--learning_rate", type=float, default=3.0e-4)
    parser.add_argument("--entropy_coef", type=float, default=0.01)
    parser.add_argument("--clip_range", type=float, default=0.2)
    parser.add_argument("--gae_lambda", type=float, default=0.95)
    parser.add_argument("--gamma", type=float, default=1.0)
    parser.add_argument("--ppo_epochs", type=int, default=4)
    parser.add_argument(
        "--log_every_steps",
        type=int,
        default=10,
        help="Print progress every N macro-placement steps inside an episode. Use 0 to disable.",
    )
    parser.add_argument(
        "--batch_size",
        type=int,
        default=8,
        help="PPO minibatch size for GPU updates. Smaller values reduce VRAM usage.",
    )
    parser.add_argument("--device", default="cuda" if torch.cuda.is_available() else "cpu")
    args = parser.parse_args()

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    torch.manual_seed(args.seed)
    np.random.seed(args.seed)
    device = torch.device(args.device)

    model = AlphaChipLikeActorCritic(
        AlphaChipLikeModelConfig(
            max_num_nodes=args.max_nodes,
            max_num_edges=args.max_edges,
            max_grid_size=args.max_grid,
        )
    )
    if args.resume_from:
        model.load_state_dict(
            torch.load(args.resume_from, map_location=device, weights_only=True)
        )
    agent = AlphaChipLikePPOAgent(
        model=model,
        config=PPOConfig(
            gamma=args.gamma,
            gae_lambda=args.gae_lambda,
            clip_range=args.clip_range,
            entropy_coef=args.entropy_coef,
            learning_rate=args.learning_rate,
            epochs=args.ppo_epochs,
            batch_size=args.batch_size,
        ),
        device=device,
    )

    history_path = out_dir / "alphachip_like_training_history.csv"
    history_fields = [
        "episode",
        "initial_cost",
        "final_cost",
        "episode_reward",
        "steps",
        "episode_runtime_sec",
        "invalid_action",
        "loss",
        "policy_loss",
        "value_loss",
        "entropy",
        "approx_kl",
        "clip_fraction",
    ]
    with history_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=history_fields)
        writer.writeheader()

    train_start = time.perf_counter()
    best_cost = float("inf")
    last_summary = {}
    rollout_plc = create_plc(args.netlist, args.init_plc)
    rollout_extractor = AlphaChipLikeFeatureExtractor(
        rollout_plc,
        AlphaChipLikeObservationConfig(
            max_num_nodes=args.max_nodes,
            max_num_edges=args.max_edges,
            max_grid_size=args.max_grid,
        ),
    )
    pending_batches: list[RolloutBatch] = []
    pending_rows: list[tuple[int, dict]] = []
    last_metrics = {
        "loss": "",
        "policy_loss": "",
        "value_loss": "",
        "entropy": "",
        "approx_kl": "",
        "clip_fraction": "",
    }
    for episode in range(args.episodes):
        batch, summary, _step_rows, _ = collect_episode(
            model=agent.model,
            netlist=args.netlist,
            init_plc=args.init_plc,
            device=device,
            max_nodes=args.max_nodes,
            max_edges=args.max_edges,
            max_grid=args.max_grid,
            max_macros=args.max_macros,
            reward_scale=args.reward_scale,
            wirelength_weight=args.wirelength_weight,
            density_weight=args.density_weight,
            congestion_weight=args.congestion_weight,
            plc=rollout_plc,
            extractor=rollout_extractor,
            progress_every_steps=args.log_every_steps,
            episode_idx=episode,
            total_episodes=args.episodes,
        )
        returns, advantages = agent.compute_returns_and_advantages(
            batch.rewards, batch.dones, batch.values
        )
        batch.returns = returns
        batch.advantages = advantages
        pending_batches.append(batch)
        pending_rows.append((episode, summary))
        best_cost = min(best_cost, float(summary["final_cost"]))
        should_update = (
            len(pending_batches) >= args.rollout_episodes
            or episode == args.episodes - 1
        )
        if not should_update:
            continue

        print(
            f"[train] PPO update starting | collected_episodes={len(pending_batches)}",
            flush=True,
        )
        metrics = agent.update(concat_rollout_batches(pending_batches))
        last_metrics = metrics
        for pending_episode, pending_summary in pending_rows:
            with history_path.open("a", newline="", encoding="utf-8") as handle:
                writer = csv.DictWriter(handle, fieldnames=history_fields)
                writer.writerow(
                    {
                        "episode": pending_episode,
                        "initial_cost": pending_summary["initial_cost"],
                        "final_cost": pending_summary["final_cost"],
                        "episode_reward": pending_summary["episode_reward"],
                        "steps": pending_summary["steps"],
                        "episode_runtime_sec": pending_summary["episode_runtime_sec"],
                        "invalid_action": pending_summary["invalid_action"],
                        **metrics,
                    }
                )
        last_summary = {**pending_rows[-1][1], **metrics}
        batch_best_cost = min(float(row["final_cost"]) for _, row in pending_rows)
        print(
            f"[train] PPO update done | "
            f"best_cost_so_far={best_cost:.6f} | "
            f"batch_best_cost={batch_best_cost:.6f} | "
            f"loss={metrics['loss']:.6f} | "
            f"policy_loss={metrics['policy_loss']:.6f} | "
            f"value_loss={metrics['value_loss']:.6f} | "
            f"entropy={metrics['entropy']:.6f} | "
            f"clip_fraction={metrics['clip_fraction']:.6f}",
            flush=True,
        )
        pending_batches.clear()
        pending_rows.clear()

    train_runtime = time.perf_counter() - train_start
    model_path = out_dir / "alphachip_like_actor_critic.pt"
    torch.save(agent.model.state_dict(), model_path)
    train_summary = {
        "model_path": str(model_path),
        "history_csv": str(history_path),
        "episodes": args.episodes,
        "rollout_episodes": args.rollout_episodes,
        "max_macros": args.max_macros,
        "max_nodes": args.max_nodes,
        "max_edges": args.max_edges,
        "max_grid": args.max_grid,
        "wirelength_weight": args.wirelength_weight,
        "density_weight": args.density_weight,
        "congestion_weight": args.congestion_weight,
        "batch_size": args.batch_size,
        "learning_rate": args.learning_rate,
        "entropy_coef": args.entropy_coef,
        "clip_range": args.clip_range,
        "gae_lambda": args.gae_lambda,
        "gamma": args.gamma,
        "ppo_epochs": args.ppo_epochs,
        "device": str(device),
        "resume_from": args.resume_from,
        "stage_name": args.stage_name,
        "best_cost": best_cost,
        "last_episode": last_summary,
        "train_runtime_sec": train_runtime,
    }
    (out_dir / "alphachip_like_train_summary.json").write_text(
        json.dumps(train_summary, indent=2),
        encoding="utf-8",
    )
    print(json.dumps(train_summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
