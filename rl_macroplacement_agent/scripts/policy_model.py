#!/usr/bin/env python3
"""PyTorch AlphaChip-like actor-critic model for macro placement.

This module intentionally mirrors the public Circuit Training model structure:

* static netlist metadata encoder
* edge-centric graph message passing over macro/port nodes
* attention from the current macro to all node embeddings
* deconvolution-like location policy head over placement grid cells
* value head for PPO

It is not a drop-in reproduction of Google's TensorFlow/TF-Agents code. It is a
small, inspectable PyTorch model that can be integrated with the local
MacroPlacement environment.
"""

from __future__ import annotations

from dataclasses import dataclass

import torch
from torch import nn


@dataclass(frozen=True)
class AlphaChipLikeModelConfig:
    """Shape/configuration values for the AlphaChip-like model."""

    max_num_nodes: int = 5000
    max_num_edges: int = 70000
    max_grid_size: int = 128
    node_feature_dim: int = 8
    metadata_dim: int = 12
    hidden_dim: int = 64
    gcn_layers: int = 3
    edge_mlp_layers: int = 1


class MLP(nn.Module):
    """Small helper MLP used for encoders and heads."""

    def __init__(self, dims: list[int], activate_last: bool = False) -> None:
        super().__init__()
        layers: list[nn.Module] = []
        for idx in range(len(dims) - 1):
            layers.append(nn.Linear(dims[idx], dims[idx + 1]))
            if idx < len(dims) - 2 or activate_last:
                layers.append(nn.ReLU())
        self.net = nn.Sequential(*layers)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.net(x)


class EdgeCentricGCNLayer(nn.Module):
    """Edge-centric message passing similar to Circuit Training.

    For every edge (i, j), the layer concatenates node_i, node_j and edge weight,
    transforms that edge representation, then scatters the edge embedding back
    to both endpoint nodes using mean aggregation.
    """

    def __init__(self, hidden_dim: int, edge_mlp_layers: int = 1) -> None:
        super().__init__()
        dims = [hidden_dim * 2 + 1]
        dims += [hidden_dim] * max(edge_mlp_layers, 1)
        self.edge_mlp = MLP(dims, activate_last=True)

    def forward(
        self,
        node_h: torch.Tensor,
        edge_i: torch.Tensor,
        edge_j: torch.Tensor,
        edge_w: torch.Tensor,
    ) -> torch.Tensor:
        """Run one message-passing layer.

        Args:
            node_h: [B, N, H] node embeddings.
            edge_i: [B, E] source node indices.
            edge_j: [B, E] target node indices.
            edge_w: [B, E] edge weights, zero for padded edges.

        Returns:
            [B, N, H] updated node embeddings with a residual connection.
        """
        batch, num_nodes, hidden_dim = node_h.shape
        edge_i = edge_i.long().clamp(min=0, max=num_nodes - 1)
        edge_j = edge_j.long().clamp(min=0, max=num_nodes - 1)
        edge_w = edge_w.float()

        gather_i = node_h.gather(
            1, edge_i.unsqueeze(-1).expand(-1, -1, hidden_dim)
        )
        gather_j = node_h.gather(
            1, edge_j.unsqueeze(-1).expand(-1, -1, hidden_dim)
        )
        edge_input_ij = torch.cat([gather_i, gather_j, edge_w.unsqueeze(-1)], dim=-1)
        edge_input_ji = torch.cat([gather_j, gather_i, edge_w.unsqueeze(-1)], dim=-1)

        edge_h = 0.5 * (self.edge_mlp(edge_input_ij) + self.edge_mlp(edge_input_ji))
        valid = (edge_w > 0).float().unsqueeze(-1)
        edge_h = edge_h * valid

        agg = torch.zeros(batch, num_nodes, hidden_dim, device=node_h.device)
        cnt = torch.zeros(batch, num_nodes, 1, device=node_h.device)
        agg.scatter_add_(1, edge_i.unsqueeze(-1).expand(-1, -1, hidden_dim), edge_h)
        agg.scatter_add_(1, edge_j.unsqueeze(-1).expand(-1, -1, hidden_dim), edge_h)
        cnt.scatter_add_(1, edge_i.unsqueeze(-1), valid)
        cnt.scatter_add_(1, edge_j.unsqueeze(-1), valid)

        return node_h + agg / cnt.clamp_min(1.0)


class AlphaChipLikeActorCritic(nn.Module):
    """Actor-critic network inspired by AlphaChip/Circuit Training."""

    def __init__(self, config: AlphaChipLikeModelConfig | None = None) -> None:
        super().__init__()
        self.config = config or AlphaChipLikeModelConfig()
        h = self.config.hidden_dim

        self.metadata_encoder = MLP([self.config.metadata_dim, h], activate_last=True)
        self.node_encoder = MLP([self.config.node_feature_dim, h], activate_last=True)
        self.gcn_layers = nn.ModuleList(
            [
                EdgeCentricGCNLayer(h, self.config.edge_mlp_layers)
                for _ in range(self.config.gcn_layers)
            ]
        )
        self.query = nn.Linear(h, h)
        self.key = nn.Linear(h, h)
        self.value = nn.Linear(h, h)

        context_dim = h * 6
        seed_grid = self.config.max_grid_size // 16
        self.policy_seed = nn.Sequential(
            nn.Linear(context_dim, seed_grid * seed_grid * 32),
            nn.ReLU(),
        )
        self.policy_deconv = nn.Sequential(
            nn.ConvTranspose2d(32, 16, kernel_size=3, stride=2, padding=1, output_padding=1),
            nn.ReLU(),
            nn.ConvTranspose2d(16, 8, kernel_size=3, stride=2, padding=1, output_padding=1),
            nn.ReLU(),
            nn.ConvTranspose2d(8, 4, kernel_size=3, stride=2, padding=1, output_padding=1),
            nn.ReLU(),
            nn.ConvTranspose2d(4, 2, kernel_size=3, stride=2, padding=1, output_padding=1),
            nn.ReLU(),
            nn.Conv2d(2, 1, kernel_size=3, padding=1),
        )
        self.value_head = MLP([context_dim, 64, 16, 1])

    def _attention(
        self, current_h: torch.Tensor, node_h: torch.Tensor
    ) -> torch.Tensor:
        q = self.query(current_h).unsqueeze(1)
        k = self.key(node_h)
        v = self.value(node_h)
        scale = k.shape[-1] ** 0.5
        weights = torch.softmax(torch.bmm(q, k.transpose(1, 2)) / scale, dim=-1)
        return torch.bmm(weights, v).squeeze(1)

    def forward(self, obs: dict[str, torch.Tensor]) -> tuple[torch.Tensor, torch.Tensor]:
        """Return masked location logits and value.

        Expected obs keys follow Circuit Training naming:
        metadata, node_features, sparse_adj_i, sparse_adj_j, sparse_adj_weight,
        current_node, mask.
        """
        metadata_h = self.metadata_encoder(obs["metadata"].float())
        node_h = self.node_encoder(obs["node_features"].float())

        for layer in self.gcn_layers:
            node_h = layer(
                node_h,
                obs["sparse_adj_i"],
                obs["sparse_adj_j"],
                obs["sparse_adj_weight"],
            )

        batch, _, hidden_dim = node_h.shape
        current_node = obs["current_node"].long().view(batch, 1, 1)
        current_h = node_h.gather(1, current_node.expand(-1, -1, hidden_dim)).squeeze(1)
        attended_h = self._attention(current_h, node_h)

        edge_mean = node_h.mean(dim=1)
        edge_var = node_h.var(dim=1, unbiased=False)
        edge_max = node_h.max(dim=1).values
        context = torch.cat(
            [metadata_h, edge_mean, edge_var, edge_max, attended_h, current_h],
            dim=-1,
        )

        seed_grid = self.config.max_grid_size // 16
        policy = self.policy_seed(context).view(batch, 32, seed_grid, seed_grid)
        logits = self.policy_deconv(policy).flatten(start_dim=1)
        value = self.value_head(context).squeeze(-1)

        mask = obs.get("mask")
        if mask is not None:
            logits = logits.masked_fill(mask <= 0, -1.0e9)

        return logits, value

    def act(
        self, obs: dict[str, torch.Tensor], deterministic: bool = False
    ) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        logits, value = self.forward(obs)
        dist = torch.distributions.Categorical(logits=logits)
        action = torch.argmax(logits, dim=-1) if deterministic else dist.sample()
        log_prob = dist.log_prob(action)
        return action, log_prob, value
