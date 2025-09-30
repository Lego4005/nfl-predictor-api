"""
Monte Carlo Simulation Framework

This package provides Monte Carlo simulation capabilities to analyze
risk, elimination probabilities, and expected outcomes across thousands
of simulated seasons.

Modules:
- monte_carlo: Run Monte Carlo simulations and analyze risk metrics
"""

from tests.simulation.monte_carlo import MonteCarloSimulator, SimulationConfig, ExpertProfile

__all__ = [
    'MonteCarloSimulator',
    'SimulationConfig',
    'ExpertProfile',
]