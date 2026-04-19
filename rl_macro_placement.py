#!/usr/bin/env python3
"""
RL-based Macro Placement using DREAMPlace
Integration with circuit_training for chip design
"""

import sys
sys.path.insert(0, '/home/DATN/DREAMPlace/install')

import torch
import numpy as np
import json
import os
from dreamplace.Placer import Placer
from dreamplace.Params import Params

class MacroPlacementEnv:
    """Gym-like environment for macro placement using DREAMPlace"""
    
    def __init__(self, benchmark_path, gpu=0):
        self.params = Params()
        self.params.gpu = gpu
        self.params.aux_input = benchmark_path
        self.placer = None
        self.reset()
    
    def reset(self):
        """Reset environment and return initial state"""
        # Load benchmark
        self.placer = Placer(self.params)
        self.placer.initialize()
        
        # Get initial state (node positions, net info, etc.)
        state = self._get_state()
        return state
    
    def _get_state(self):
        """Extract state representation for RL agent"""
        # Node positions
        pos = self.placer.placedb.node_x, self.placer.placedb.node_y
        
        # Node sizes
        sizes = self.placer.placedb.node_size_x, self.placer.placedb.node_size_y
        
        # Net connections
        flat_net2pin = self.placer.placedb.flat_net2pin_map
        
        # Macro mask (movable macros)
        macro_mask = self.placer.placedb.movable_macro_mask
        
        return {
            'pos': torch.tensor([pos[0], pos[1]]).T,
            'sizes': torch.tensor([sizes[0], sizes[1]]).T,
            'flat_net2pin': flat_net2pin,
            'macro_mask': macro_mask,
            'num_nodes': self.placer.placedb.num_nodes,
            'num_nets': self.placer.placedb.num_nets
        }
    
    def step(self, action):
        """
        Execute action (macro position update)
        action: new positions for movable macros
        """
        # Update macro positions
        reward = self._compute_reward()
        done = self._check_done()
        next_state = self._get_state()
        
        return next_state, reward, done, {}
    
    def _compute_reward(self):
        """Compute reward based on HPWL and density"""
        # Get current metrics
        hpwl = self.placer.placedb.compute_hpwl()
        density = self.placer.placedb.compute_density()
        
        # Negative reward (lower is better)
        reward = -hpwl - 0.1 * density
        return reward
    
    def _check_done(self):
        """Check if placement is converged"""
        return self.placer.iteration >= self.placer.max_iter
    
    def run_placement(self, json_file):
        """Run full DREAMPlace placement"""
        self.placer.run()
        return self.placer.metrics


class SimpleRLAgent:
    """Simple RL agent for testing"""
    
    def __init__(self, state_dim, action_dim):
        self.state_dim = state_dim
        self.action_dim = action_dim
        
    def select_action(self, state):
        """Select action given state"""
        # Random action for now
        return torch.randn(self.action_dim)
    
    def train(self, env, num_episodes=100):
        """Train agent on environment"""
        for episode in range(num_episodes):
            state = env.reset()
            done = False
            episode_reward = 0
            
            while not done:
                action = self.select_action(state)
                next_state, reward, done, _ = env.step(action)
                episode_reward += reward
                state = next_state
            
            print(f"Episode {episode}: Reward = {episode_reward:.2f}")


def main():
    """Main entry point"""
    # Test with ISPD2005 benchmark
    benchmark = "adaptec1"
    benchmark_path = f"/home/DATN/DREAMPlace/benchmarks/ispd2005/{benchmark}/{benchmark}.aux"
    
    # Create environment
    env = MacroPlacementEnv(benchmark_path, gpu=0)
    
    # Run baseline placement
    print("Running DREAMPlace baseline placement...")
    metrics = env.run_placement(None)
    print(f"Baseline HPWL: {metrics['hpwl']:.2e}")
    
    # Create RL agent
    state = env.reset()
    state_dim = state['num_nodes'] * 2  # x, y positions
    action_dim = sum(state['macro_mask']) * 2  # x, y for each macro
    
    agent = SimpleRLAgent(state_dim, action_dim)
    
    # Train agent
    print("Training RL agent...")
    agent.train(env, num_episodes=10)
    
    print("Done!")


if __name__ == "__main__":
    main()
