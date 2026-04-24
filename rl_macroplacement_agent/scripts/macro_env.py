#!/usr/bin/env python3
"""Minimal Gymnasium environment for open-source macro placement RL."""

from __future__ import annotations

import csv
import json
from pathlib import Path

import gymnasium as gym
import numpy as np

from plc_utils import PlcFile

PLLC_CLIENT_DIR = Path("/home/DATN/MacroPlacement/CodeElements/Plc_client")
import sys

if str(PLLC_CLIENT_DIR) not in sys.path:
    sys.path.insert(0, str(PLLC_CLIENT_DIR))

from plc_client_os import PlacementCost


class MacroPlacementEnv(gym.Env):
    """Sequential macro placement environment with proxy-cost reward."""

    metadata = {"render_modes": []}

    def __init__(
        self,
        netlist: str,
        init_plc: str,
        out_dir: str,
        max_macros: int = 20,
        reward_scale: float = 1000.0,
        invalid_action_penalty: float = -1.0,
        no_improvement_penalty: float = -0.01,
    ) -> None:
        super().__init__()
        self.netlist = str(netlist)
        self.init_plc = str(init_plc)
        self.out_dir = Path(out_dir)
        self.out_dir.mkdir(parents=True, exist_ok=True)

        self.max_macros = int(max_macros)
        self.reward_scale = float(reward_scale)
        self.invalid_action_penalty = float(invalid_action_penalty)
        self.no_improvement_penalty = float(no_improvement_penalty)

        self.base_plc = PlcFile(self.init_plc).load()
        self.current_plc = PlcFile(self.init_plc).load()
        self.evaluator = PlacementCost(self.netlist)
        self.evaluator.restore_placement(
            self.init_plc,
            ifInital=True,
            ifValidate=False,
            ifReadComment=True,
        )

        self.canvas_width, self.canvas_height = self.evaluator.get_canvas_width_height()
        self.grid_cols, self.grid_rows = self.evaluator.get_grid_num_columns_rows()
        self.grid_cell_count = self.grid_cols * self.grid_rows
        self.grid_width = self.canvas_width / self.grid_cols
        self.grid_height = self.canvas_height / self.grid_rows

        self.macro_indices = self._select_macro_indices()
        self.macro_dims = {
            node_idx: self.evaluator.get_node_width_height(node_idx)
            for node_idx in self.macro_indices
        }
        self.node_dims = {}
        self.obstacle_indices = []
        for node_idx in self.base_plc.node_data:
            width, height = self.evaluator.get_node_width_height(node_idx)
            self.node_dims[node_idx] = (width, height)
            if width > 0.0 and height > 0.0:
                self.obstacle_indices.append(node_idx)

        self.action_space = gym.spaces.Discrete(self.grid_cell_count)
        self.observation_space = gym.spaces.Box(
            low=-np.inf,
            high=np.inf,
            shape=(8,),
            dtype=np.float32,
        )

        self.initial_cost = float(self.evaluator.get_cost())
        self.previous_cost = self.initial_cost
        self.best_cost = self.initial_cost
        self.best_plc_path = self.out_dir / "best_rl.plc"
        self.best_proxy_path = self.out_dir / "best_proxy.json"

        self.current_macro_ptr = 0
        self.current_episode_reward = 0.0
        self.last_reward = 0.0
        self.episode_idx = 0
        self.step_idx = 0

        self.history_csv_path = self.out_dir / "reward_history.csv"
        self._ensure_history_csv()

    def _ensure_history_csv(self) -> None:
        if self.history_csv_path.exists():
            return
        with self.history_csv_path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.writer(handle)
            writer.writerow(
                [
                    "episode",
                    "step",
                    "macro_ptr",
                    "node_idx",
                    "action",
                    "reward",
                    "cost",
                    "best_cost",
                    "valid_action",
                ]
            )

    def _select_macro_indices(self) -> list[int]:
        candidates = []
        for node_idx in self.evaluator.get_macro_indices():
            if node_idx not in self.base_plc.node_data:
                continue
            node = self.base_plc.get_node(node_idx)
            if node["fixed"] != 0:
                continue
            candidates.append(node_idx)
            if len(candidates) >= self.max_macros:
                break

        if not candidates:
            raise RuntimeError("No movable macro indices found for RL environment.")
        return candidates

    def _mark_dirty(self) -> None:
        self.evaluator.FLAG_UPDATE_CONGESTION = True
        self.evaluator.FLAG_UPDATE_DENSITY = True
        self.evaluator.FLAG_UPDATE_WIRELENGTH = True
        self.evaluator.FLAG_UPDATE_MACRO_ADJ = True
        self.evaluator.FLAG_UPDATE_MACRO_AND_CLUSTERED_PORT_ADJ = True
        self.evaluator.FLAG_UPDATE_NODE_MASK = True

    def _grid_cell_to_center(self, action: int) -> tuple[int, int, float, float]:
        row = action // self.grid_cols
        col = action % self.grid_cols
        x = (col + 0.5) * self.grid_width
        y = (row + 0.5) * self.grid_height
        return row, col, x, y

    def _bbox_for_node(self, node_idx: int, x: float, y: float) -> tuple[float, float, float, float]:
        width, height = self.macro_dims[node_idx]
        return (x - width / 2.0, y - height / 2.0, x + width / 2.0, y + height / 2.0)

    @staticmethod
    def _boxes_overlap(a, b) -> bool:
        return not (a[2] <= b[0] or b[2] <= a[0] or a[3] <= b[1] or b[3] <= a[1])

    def _is_valid_placement(self, node_idx: int, action: int) -> bool:
        row, col, x, y = self._grid_cell_to_center(action)
        if row < 0 or row >= self.grid_rows or col < 0 or col >= self.grid_cols:
            return False

        candidate_box = self._bbox_for_node(node_idx, x, y)
        if candidate_box[0] < 0 or candidate_box[1] < 0:
            return False
        if candidate_box[2] > self.canvas_width or candidate_box[3] > self.canvas_height:
            return False

        for other_idx in self.obstacle_indices:
            if other_idx == node_idx:
                continue

            placement = self.current_plc.node_data[other_idx]
            other_x = placement["x"]
            other_y = placement["y"]
            other_width, other_height = self.node_dims[other_idx]
            other_box = (
                other_x - other_width / 2.0,
                other_y - other_height / 2.0,
                other_x + other_width / 2.0,
                other_y + other_height / 2.0,
            )
            if self._boxes_overlap(candidate_box, other_box):
                return False

        return True

    def _save_best_if_needed(self, cost: float) -> None:
        should_save = (
            not self.best_plc_path.exists()
            or not self.best_proxy_path.exists()
            or cost < self.best_cost
        )
        if not should_save:
            return

        self.best_cost = float(cost)
        self.current_plc.save(self.best_plc_path)
        payload = {
            "netlist": self.netlist,
            "plc": str(self.best_plc_path),
            "cost": self.best_cost,
            "wirelength": self._safe_metric(self.evaluator.get_wirelength),
            "density_cost": self._safe_metric(self.evaluator.get_density_cost),
            "congestion_cost": self._safe_metric(self.evaluator.get_congestion_cost),
        }
        self.best_proxy_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    @staticmethod
    def _safe_metric(fn):
        try:
            return fn()
        except Exception as exc:
            return {"error": repr(exc)}

    def _get_current_node(self) -> int:
        return self.macro_indices[self.current_macro_ptr]

    def _get_obs(self) -> np.ndarray:
        node_idx = self._get_current_node()
        x, y = self.current_plc.get_node(node_idx)["x"], self.current_plc.get_node(node_idx)["y"]
        width, height = self.macro_dims[node_idx]

        obs = np.array(
            [
                self.current_macro_ptr / max(len(self.macro_indices), 1),
                self.previous_cost / max(self.initial_cost, 1e-9),
                self.best_cost / max(self.initial_cost, 1e-9),
                self.last_reward,
                x / max(self.canvas_width, 1e-9),
                y / max(self.canvas_height, 1e-9),
                width / max(self.canvas_width, 1e-9),
                height / max(self.canvas_height, 1e-9),
            ],
            dtype=np.float32,
        )
        return obs

    def action_masks(self) -> np.ndarray:
        node_idx = self._get_current_node()
        mask = np.zeros(self.action_space.n, dtype=bool)
        for action in range(self.action_space.n):
            mask[action] = self._is_valid_placement(node_idx, action)
        if not mask.any():
            mask[:] = True
        return mask

    def reset(self, *, seed=None, options=None):
        super().reset(seed=seed)
        self.evaluator = PlacementCost(self.netlist)
        self.evaluator.restore_placement(
            self.init_plc,
            ifInital=True,
            ifValidate=False,
            ifReadComment=True,
        )
        self.current_plc = PlcFile(self.init_plc).load()

        self.current_macro_ptr = 0
        self.current_episode_reward = 0.0
        self.last_reward = 0.0
        self.step_idx = 0
        self.previous_cost = float(self.evaluator.get_cost())
        self.initial_cost = self.previous_cost
        self._save_best_if_needed(self.previous_cost)

        return self._get_obs(), {}

    def step(self, action: int):
        node_idx = self._get_current_node()
        valid = self._is_valid_placement(node_idx, int(action))

        if valid:
            _, _, x, y = self._grid_cell_to_center(int(action))
            current = self.current_plc.get_node(node_idx)
            self.current_plc.set_node_position(
                node_idx,
                x,
                y,
                orientation=current["orientation"],
                fixed=current["fixed"],
            )
            self.evaluator.update_node_coords(node_idx, x, y)
            self._mark_dirty()
            cost = float(self.evaluator.get_cost())
            reward = (self.previous_cost - cost) * self.reward_scale
            if reward == 0.0:
                reward = self.no_improvement_penalty
            self.previous_cost = cost
            self._save_best_if_needed(cost)
        else:
            cost = float(self.previous_cost)
            reward = self.invalid_action_penalty

        self.last_reward = float(reward)
        self.current_episode_reward += float(reward)
        self.step_idx += 1

        terminated = self.current_macro_ptr >= len(self.macro_indices) - 1
        info = {
            "cost": cost,
            "best_cost": self.best_cost,
            "node_idx": node_idx,
            "macro_ptr": self.current_macro_ptr,
            "valid_action": valid,
        }

        with self.history_csv_path.open("a", newline="", encoding="utf-8") as handle:
            writer = csv.writer(handle)
            writer.writerow(
                [
                    self.episode_idx,
                    self.step_idx,
                    self.current_macro_ptr,
                    node_idx,
                    int(action),
                    reward,
                    cost,
                    self.best_cost,
                    int(valid),
                ]
            )

        if terminated:
            info["episode"] = {
                "r": self.current_episode_reward,
                "l": self.step_idx,
            }
            self.episode_idx += 1
        else:
            self.current_macro_ptr += 1

        return self._get_obs(), float(reward), terminated, False, info
