#!/usr/bin/env python3
"""
🚀 Quick Test Runner for Memory Learning Experiment
Runs a small 5-game test to verify everything works before full 40-game run
"""

import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from prove_memory_learning import MemoryLearningExperiment

def main():
    """Run quick test"""

    print("="*60)
    print("🚀 QUICK TEST: Memory Learning Experiment")
    print("="*60)
    print("\\nRunning 5-game test to verify system works...")
    print("This should complete in ~2-3 minutes.\\n")

    # Create experiment
    experiment = MemoryLearningExperiment(experiment_name="quick_test")

    # Run for just 5 games
    experiment.run_experiment(num_games=5)

    print("\\n✅ Quick test complete!")
    print("\\nIf this worked, run the full experiment:")
    print("  python scripts/prove_memory_learning.py")
    print("\\nTo analyze results:")
    print("  python scripts/analyze_memory_experiment.py results/<results_file>.json")


if __name__ == "__main__":
    main()
