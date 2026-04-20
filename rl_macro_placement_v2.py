#!/usr/bin/env python3
"""
RL-based Macro Placement using DREAMPlace (Simplified Version)
Integration with circuit_training for chip design
"""

import sys
import os
sys.path.insert(0, '/home/DATN/DREAMPlace/install')

import torch
import numpy as np
import json
import gymnasium as gym
from gymnasium import spaces

class SimpleMacroPlacementEnv(gym.Env):
    """Simplified Gym-like environment for macro placement"""
    
    def __init__(self, num_macros=10, canvas_size=(100, 100)):
        super().__init__()
        self.num_macros = num_macros
        self.canvas_size = canvas_size
        
        # Define action space: (x, y) positions for each macro
        self.action_space = spaces.Box(
            low=0, high=1, 
            shape=(num_macros * 2,), 
            dtype=np.float32
        )
        
        # Define observation space: current positions + sizes
        self.observation_space = spaces.Box(
            low=0, high=1,
            shape=(num_macros * 4,),  # x, y, w, h for each macro
            dtype=np.float32
        )
        
        # Random macro sizes
        self.macro_sizes = np.random.uniform(5, 20, (num_macros, 2))
        self.positions = np.zeros((num_macros, 2))
        
    def reset(self, seed=None, options=None):
        super().reset(seed=seed)
        # Random initial positions
        self.positions = np.random.uniform(0, 1, (self.num_macros, 2))
        obs = self._get_obs()
        info = {}
        return obs, info
    
    def _get_obs(self):
        # Flatten positions and sizes
        obs = np.concatenate([
            self.positions.flatten(),
            self.macro_sizes.flatten() / max(self.canvas_size)
        ]).astype(np.float32)
        return obs
    
    def step(self, action):
        # Update positions based on action
        self.positions = action.reshape(self.num_macros, 2)
        self.positions = np.clip(self.positions, 0, 1)
        
        # Compute reward (negative HPWL approximation + density penalty)
        reward = self._compute_reward()
        
        # Check termination
        terminated = False
        truncated = False
        info = {"hpwl": self._compute_hpwl(), "density": self._compute_density()}
        
        obs = self._get_obs()
        return obs, reward, terminated, truncated, info
    
    def _compute_hpwl(self):
        """Approximate Half-Perimeter Wirelength"""
        if self.num_macros < 2:
            return 0.0
        # Simple HPWL: sum of bounding box perimeters
        x_coords = self.positions[:, 0] * self.canvas_size[0]
        y_coords = self.positions[:, 1] * self.canvas_size[1]
        hpwl = (x_coords.max() - x_coords.min() + 
                y_coords.max() - y_coords.min())
        return hpwl
    
    def _compute_density(self):
        """Compute placement density (overlap penalty)"""
        overlap_penalty = 0.0
        for i in range(self.num_macros):
            for j in range(i + 1, self.num_macros):
                # Simple overlap check
                dx = abs(self.positions[i, 0] - self.positions[j, 0])
                dy = abs(self.positions[i, 1] - self.positions[j, 1])
                if dx < 0.1 and dy < 0.1:  # Approximate overlap threshold
                    overlap_penalty += 1.0
        return overlap_penalty
    
    def _compute_reward(self):
        """Compute reward based on HPWL and density"""
        hpwl = self._compute_hpwl()
        density = self._compute_density()
        # Negative reward (lower is better), with density penalty
        reward = -hpwl / 100.0 - density * 10.0
        return reward
    
    def render(self):
        pass


class RLAgent:
    """Simple RL agent using Stable Baselines3"""
    
    def __init__(self, env):
        self.env = env
        try:
            from stable_baselines3 import PPO
            self.model = PPO("MlpPolicy", env, verbose=1)
        except ImportError:
            print("Warning: stable_baselines3 not available, using random policy")
            self.model = None
    
    def train(self, total_timesteps=10000):
        if self.model:
            self.model.learn(total_timesteps=total_timesteps)
        else:
            print("Random policy - no training needed")
    
    def predict(self, obs):
        if self.model:
            return self.model.predict(obs)
        else:
            return self.env.action_space.sample(), None


def main():
    """Main entry point"""
    print("=" * 60)
    print("RL Macro Placement - Simplified Demo")
    print("=" * 60)
    
    # Create environment
    env = SimpleMacroPlacementEnv(num_macros=5, canvas_size=(100, 100))
    
    # Test environment
    print("\nTesting environment...")
    obs, info = env.reset(seed=42)
    print(f"Initial observation shape: {obs.shape}")
    
    total_reward = 0
    for step in range(10):
        action = env.action_space.sample()
        obs, reward, terminated, truncated, info = env.step(action)
        total_reward += reward
        print(f"Step {step}: Reward={reward:.2f}, HPWL={info['hpwl']:.2f}, Density={info['density']:.2f}")
        if terminated or truncated:
            break
    
    print(f"\nTotal reward: {total_reward:.2f}")
    
    # Train RL agent
    print("\n" + "=" * 60)
    print("Training RL Agent...")
    print("=" * 60)
    
    agent = RLAgent(env)
    agent.train(total_timesteps=1000)
    
    print("\nTraining complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()
