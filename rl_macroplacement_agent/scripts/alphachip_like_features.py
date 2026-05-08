#!/usr/bin/env python3
"""AlphaChip-like graph observation extraction for MacroPlacement data.

The first running RL environment in this repo used an 8-value vector
observation. Circuit Training/AlphaChip uses a much richer observation: netlist
metadata, sparse graph connectivity, macro/port node features, current-node
state, and an action mask over a padded grid canvas.

This module builds that richer observation from the open-source
`plc_client_os.PlacementCost` interface so it can feed the local PyTorch
AlphaChip-like model.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from path_utils import add_repo_paths

add_repo_paths()

from plc_client_os import PlacementCost


HARD_MACRO = 1
SOFT_MACRO = 2
PORT_CLUSTER = 3


@dataclass(frozen=True)
class AlphaChipLikeObservationConfig:
    """Maximum tensor sizes used by the AlphaChip-like model."""

    max_num_nodes: int = 5000
    max_num_edges: int = 70000
    max_grid_size: int = 128


class AlphaChipLikeFeatureExtractor:
    """Extract graph observations from a `PlacementCost` object."""

    def __init__(
        self,
        plc: PlacementCost,
        config: AlphaChipLikeObservationConfig | None = None,
        netlist_index: int = 0,
    ) -> None:
        self.plc = plc
        self.config = config or AlphaChipLikeObservationConfig()
        self.netlist_index = int(netlist_index)

        self.canvas_width, self.canvas_height = plc.get_canvas_width_height()
        self.grid_cols, self.grid_rows = plc.get_grid_num_columns_rows()
        self.grid_width = self.canvas_width / max(self.grid_cols, 1)
        self.grid_height = self.canvas_height / max(self.grid_rows, 1)

        self.macro_indices = list(plc.get_macro_indices())
        self.macro_to_feature_index = {
            node_idx: idx for idx, node_idx in enumerate(self.macro_indices)
        }

        adjacency, port_grid_cells = plc.get_macro_and_clustered_port_adjacency()
        self.port_grid_cells = list(port_grid_cells)
        self.num_macro_nodes = len(self.macro_indices)
        self.num_port_nodes = len(self.port_grid_cells)
        self.num_feature_nodes = self.num_macro_nodes + self.num_port_nodes
        self._adjacency = adjacency

        if self.num_feature_nodes > self.config.max_num_nodes:
            raise ValueError(
                "Feature node count exceeds config max_num_nodes: "
                f"{self.num_feature_nodes} > {self.config.max_num_nodes}"
            )

        if self.grid_cols > self.config.max_grid_size or self.grid_rows > self.config.max_grid_size:
            raise ValueError(
                "Placement grid exceeds padded model grid: "
                f"{self.grid_cols}x{self.grid_rows} > "
                f"{self.config.max_grid_size}x{self.config.max_grid_size}"
            )

        self.static_obs = self._extract_static_obs()

    def _safe_bool_call(self, fn, node_idx: int) -> bool:
        try:
            return bool(fn(node_idx))
        except Exception:
            return False

    def _port_cluster_location(self, grid_cell: int) -> tuple[float, float]:
        col = grid_cell % self.grid_cols
        row = grid_cell // self.grid_cols
        if col == 0:
            x = 0.0
        elif col == self.grid_cols - 1:
            x = self.canvas_width
        else:
            x = (col + 0.5) * self.grid_width

        if row == 0:
            y = 0.0
        elif row == self.grid_rows - 1:
            y = self.canvas_height
        else:
            y = (row + 0.5) * self.grid_height

        return x, y

    def _metadata(self, sparse_adj_weight: np.ndarray) -> np.ndarray:
        routes_h, routes_v = self.plc.get_routes_per_micron()
        macro_routes_h, macro_routes_v = self.plc.get_macro_routing_allocation()
        hard_count = sum(
            1
            for idx in self.macro_indices
            if not self._safe_bool_call(self.plc.is_node_soft_macro, idx)
        )
        soft_count = self.num_macro_nodes - hard_count
        half_perimeter = max(self.canvas_width + self.canvas_height, 1.0)

        return np.asarray(
            [
                float(np.sum(sparse_adj_weight)) / max(self.config.max_num_edges, 1),
                hard_count / max(self.config.max_num_nodes, 1),
                soft_count / max(self.config.max_num_nodes, 1),
                self.num_port_nodes / max(self.config.max_num_nodes, 1),
                routes_h * self.canvas_height / 1000.0,
                routes_v * self.canvas_width / 1000.0,
                macro_routes_h * self.canvas_height / 1000.0,
                macro_routes_v * self.canvas_width / 1000.0,
                self.grid_cols / max(self.config.max_grid_size, 1),
                self.grid_rows / max(self.config.max_grid_size, 1),
                self.canvas_width / half_perimeter,
                self.canvas_height / half_perimeter,
            ],
            dtype=np.float32,
        )

    def _extract_sparse_edges(self) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        edge_i: list[int] = []
        edge_j: list[int] = []
        edge_w: list[float] = []
        node_count = self.num_feature_nodes

        for i in range(node_count):
            base = i * node_count
            for j in range(i + 1, node_count):
                weight = float(self._adjacency[base + j])
                if weight <= 0.0:
                    continue
                edge_i.append(i)
                edge_j.append(j)
                edge_w.append(weight)
                if len(edge_i) >= self.config.max_num_edges:
                    break
            if len(edge_i) >= self.config.max_num_edges:
                break

        sparse_i = np.zeros((self.config.max_num_edges,), dtype=np.int64)
        sparse_j = np.zeros((self.config.max_num_edges,), dtype=np.int64)
        sparse_w = np.zeros((self.config.max_num_edges,), dtype=np.float32)
        edge_counts = np.zeros((self.config.max_num_nodes,), dtype=np.int64)

        count = len(edge_i)
        if count:
            sparse_i[:count] = np.asarray(edge_i, dtype=np.int64)
            sparse_j[:count] = np.asarray(edge_j, dtype=np.int64)
            sparse_w[:count] = np.asarray(edge_w, dtype=np.float32)
            for src, dst in zip(edge_i, edge_j):
                edge_counts[src] += 1
                edge_counts[dst] += 1

        return sparse_i, sparse_j, sparse_w, edge_counts

    def _extract_node_features(self) -> np.ndarray:
        features = np.zeros((self.config.max_num_nodes, 8), dtype=np.float32)
        for feature_idx, node_idx in enumerate(self.macro_indices):
            is_soft = self._safe_bool_call(self.plc.is_node_soft_macro, node_idx)
            is_placed = self._safe_bool_call(self.plc.is_node_placed, node_idx)
            try:
                x, y = self.plc.get_node_location(node_idx)
            except Exception:
                x = self.canvas_width * 0.5
                y = self.canvas_height * 0.5
            try:
                width, height = self.plc.get_node_width_height(node_idx)
            except Exception:
                width = 0.0
                height = 0.0

            features[feature_idx] = np.asarray(
                [
                    x / max(self.canvas_width, 1.0),
                    y / max(self.canvas_height, 1.0),
                    width / max(self.canvas_width, 1.0),
                    height / max(self.canvas_height, 1.0),
                    0.0 if is_soft else 1.0,
                    1.0 if is_soft else 0.0,
                    0.0,
                    1.0 if is_placed else 0.0,
                ],
                dtype=np.float32,
            )

        offset = self.num_macro_nodes
        for port_offset, grid_cell in enumerate(self.port_grid_cells):
            feature_idx = offset + port_offset
            x, y = self._port_cluster_location(grid_cell)
            features[feature_idx] = np.asarray(
                [
                    x / max(self.canvas_width, 1.0),
                    y / max(self.canvas_height, 1.0),
                    0.0,
                    0.0,
                    0.0,
                    0.0,
                    1.0,
                    1.0,
                ],
                dtype=np.float32,
            )

        return features

    def _extract_static_obs(self) -> dict[str, np.ndarray]:
        sparse_i, sparse_j, sparse_w, edge_counts = self._extract_sparse_edges()
        return {
            "metadata": self._metadata(sparse_w),
            "node_features": self._extract_node_features(),
            "sparse_adj_i": sparse_i,
            "sparse_adj_j": sparse_j,
            "sparse_adj_weight": sparse_w,
            "edge_counts": edge_counts,
            "netlist_index": np.asarray([self.netlist_index], dtype=np.int64),
        }

    def padded_mask_for_node(self, node_idx: int) -> np.ndarray:
        """Return a 128x128-style padded grid mask for a real macro node."""
        real_mask = np.asarray(self.plc.get_node_mask(node_idx), dtype=np.int64)
        real_mask = real_mask.reshape(self.grid_rows, self.grid_cols)

        rows_pad = self.config.max_grid_size - self.grid_rows
        cols_pad = self.config.max_grid_size - self.grid_cols
        top = rows_pad // 2
        bottom = rows_pad - top
        left = cols_pad // 2
        right = cols_pad - left
        padded = np.pad(
            real_mask,
            ((top, bottom), (left, right)),
            mode="constant",
            constant_values=0,
        )
        return padded.reshape(self.config.max_grid_size**2).astype(np.int64)

    def observation_for_node(self, node_idx: int) -> dict[str, np.ndarray]:
        """Return model-ready observation for a macro node id."""
        if node_idx not in self.macro_to_feature_index:
            raise KeyError(f"Node is not in macro feature list: {node_idx}")
        obs = {key: np.copy(value) for key, value in self.static_obs.items()}
        # Locations and placement flags change after every action, so refresh
        # node features while reusing the expensive static graph tensors.
        obs["node_features"] = self._extract_node_features()
        obs["current_node"] = np.asarray(
            [self.macro_to_feature_index[node_idx]], dtype=np.int64
        )
        obs["mask"] = self.padded_mask_for_node(node_idx)
        return obs

    def movable_hard_macros(self, max_macros: int | None = None) -> list[int]:
        """Return movable hard macro node ids in placement order."""
        macros = []
        for node_idx in self.macro_indices:
            if self._safe_bool_call(self.plc.is_node_soft_macro, node_idx):
                continue
            if self._safe_bool_call(self.plc.is_node_fixed, node_idx):
                continue
            macros.append(node_idx)
            if max_macros is not None and len(macros) >= max_macros:
                break
        return macros

    def summary(self) -> dict[str, int | float]:
        """Small shape summary for reports and smoke tests."""
        nonzero_edges = int(np.count_nonzero(self.static_obs["sparse_adj_weight"]))
        hard_count = sum(
            1
            for idx in self.macro_indices
            if not self._safe_bool_call(self.plc.is_node_soft_macro, idx)
        )
        return {
            "feature_nodes": self.num_feature_nodes,
            "macro_nodes": self.num_macro_nodes,
            "hard_macros": hard_count,
            "soft_macros": self.num_macro_nodes - hard_count,
            "port_clusters": self.num_port_nodes,
            "nonzero_edges": nonzero_edges,
            "grid_cols": self.grid_cols,
            "grid_rows": self.grid_rows,
            "canvas_width": self.canvas_width,
            "canvas_height": self.canvas_height,
            "max_num_nodes": self.config.max_num_nodes,
            "max_num_edges": self.config.max_num_edges,
            "max_grid_size": self.config.max_grid_size,
        }
