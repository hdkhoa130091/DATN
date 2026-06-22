#!/usr/bin/env python3
"""Minimal PPO agent code for the AlphaChip-like PyTorch model.

The production AlphaChip/circuit_training stack uses TF-Agents PPO, Reverb,
distributed actors, and TensorFlow models. This file keeps the same conceptual
pieces in a compact PyTorch form so the agent logic is visible in the repo:

* rollout storage
* generalized advantage estimation
* clipped PPO policy loss
* value loss
* entropy regularization

It is intended as the next integration target for MacroPlacementEnv, not as a
claim of full AlphaChip reproduction.
"""

from __future__ import annotations

from dataclasses import dataclass

import torch
from torch import nn


@dataclass
class PPOConfig:
    gamma: float = 1.0
    gae_lambda: float = 0.95
    clip_range: float = 0.2
    value_coef: float = 0.5
    entropy_coef: float = 0.01
    max_grad_norm: float = 1.0
    learning_rate: float = 3.0e-4
    epochs: int = 4
    batch_size: int = 64


@dataclass
class RolloutBatch:
    obs: dict[str, torch.Tensor]
    actions: torch.Tensor
    old_log_probs: torch.Tensor
    rewards: torch.Tensor
    dones: torch.Tensor
    values: torch.Tensor
    returns: torch.Tensor | None = None
    advantages: torch.Tensor | None = None


class AlphaChipLikePPOAgent:
    """Small inspectable PPO agent around an actor-critic model."""

    def __init__(
        self,
        model: nn.Module,
        config: PPOConfig | None = None,
        device: str | torch.device = "cpu",
    ) -> None:
        self.model = model.to(device)
        self.config = config or PPOConfig()
        self.device = torch.device(device)
        self.optimizer = torch.optim.Adam(
            self.model.parameters(), lr=self.config.learning_rate
        )

    def compute_returns_and_advantages(
        self,
        rewards: torch.Tensor,
        dones: torch.Tensor,
        values: torch.Tensor,
        last_value: torch.Tensor | float = 0.0,
    ) -> tuple[torch.Tensor, torch.Tensor]:
        """Compute GAE advantages and bootstrapped returns."""
        rewards = rewards.to(self.device)
        dones = dones.to(self.device)
        values = values.to(self.device)
        if not torch.is_tensor(last_value):
            last_value = torch.tensor(last_value, device=self.device)

        advantages = torch.zeros_like(rewards)
        last_gae = torch.zeros((), device=self.device)
        next_value = last_value
        for t in reversed(range(rewards.shape[0])):
            nonterminal = 1.0 - dones[t].float()
            delta = rewards[t] + self.config.gamma * next_value * nonterminal - values[t]
            last_gae = (
                delta
                + self.config.gamma
                * self.config.gae_lambda
                * nonterminal
                * last_gae
            )
            advantages[t] = last_gae
            next_value = values[t]

        returns = advantages + values
        # Keep per-episode advantages raw here. The trainer concatenates several
        # complete placement episodes into one PPO rollout; normalization must
        # happen across that full rollout so better episodes remain distinguishable
        # from worse ones during the policy update.
        return returns.detach(), advantages.detach()

    def ppo_loss(self, batch: RolloutBatch) -> tuple[torch.Tensor, dict[str, float]]:
        """Compute clipped PPO loss for one minibatch."""
        if batch.returns is None or batch.advantages is None:
            raise ValueError("RolloutBatch must include returns and advantages.")

        logits, values = self.model(batch.obs)
        dist = torch.distributions.Categorical(logits=logits)
        log_probs = dist.log_prob(batch.actions)
        entropy = dist.entropy().mean()

        ratio = torch.exp(log_probs - batch.old_log_probs)
        unclipped = ratio * batch.advantages
        clipped = torch.clamp(
            ratio,
            1.0 - self.config.clip_range,
            1.0 + self.config.clip_range,
        ) * batch.advantages
        policy_loss = -torch.min(unclipped, clipped).mean()
        value_loss = torch.square(batch.returns - values).mean()
        entropy_loss = -entropy

        loss = (
            policy_loss
            + self.config.value_coef * value_loss
            + self.config.entropy_coef * entropy_loss
        )
        approx_kl = (batch.old_log_probs - log_probs).mean().detach()
        clip_fraction = (
            (torch.abs(ratio - 1.0) > self.config.clip_range).float().mean()
        ).detach()
        metrics = {
            "loss": float(loss.detach().cpu()),
            "policy_loss": float(policy_loss.detach().cpu()),
            "value_loss": float(value_loss.detach().cpu()),
            "entropy": float(entropy.detach().cpu()),
            "approx_kl": float(approx_kl.cpu()),
            "clip_fraction": float(clip_fraction.cpu()),
        }
        return loss, metrics

    @staticmethod
    def _slice_batch(batch: RolloutBatch, indices: torch.Tensor) -> RolloutBatch:
        return RolloutBatch(
            obs={key: value[indices] for key, value in batch.obs.items()},
            actions=batch.actions[indices],
            old_log_probs=batch.old_log_probs[indices],
            rewards=batch.rewards[indices],
            dones=batch.dones[indices],
            values=batch.values[indices],
            returns=batch.returns[indices] if batch.returns is not None else None,
            advantages=(
                batch.advantages[indices] if batch.advantages is not None else None
            ),
        )

    def update(self, batch: RolloutBatch) -> dict[str, float]:
        """Run PPO epochs over shuffled minibatches and average metrics."""
        self.model.train()
        sample_count = batch.actions.shape[0]
        metric_sums: dict[str, float] = {}
        updates = 0
        for _ in range(self.config.epochs):
            permutation = torch.randperm(sample_count, device=self.device)
            for start in range(0, sample_count, self.config.batch_size):
                indices = permutation[start : start + self.config.batch_size]
                minibatch = self._slice_batch(batch, indices)
                loss, metrics = self.ppo_loss(minibatch)
                self.optimizer.zero_grad(set_to_none=True)
                loss.backward()
                torch.nn.utils.clip_grad_norm_(
                    self.model.parameters(), self.config.max_grad_norm
                )
                self.optimizer.step()
                for key, value in metrics.items():
                    metric_sums[key] = metric_sums.get(key, 0.0) + value
                updates += 1
        return {key: value / max(updates, 1) for key, value in metric_sums.items()}
