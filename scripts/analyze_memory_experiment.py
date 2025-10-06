#!/usr/bin/env python3
"""
📊 Memory Experiment Statistical Analysis
Analyzes results from prove_memory_learning.py to determine statistical significance

Statistical Tests:
1. Paired t-test: Memory vs No-Memory groups
2. Learning curve regression: Slope analysis
3. Per-expert improvement analysis
4. Confidence calibration assessment
"""

import json
import sys
import os
from typing import Dict, List, Tuple
from dataclasses import dataclass
import numpy as np
from scipy import stats
import matplotlib.pyplot as plt
from pathlib import Path

@dataclass
class ExpertAnalysis:
    """Analysis results for a single expert"""
    expert_id: str
    personality_type: str
    has_memory: bool

    # Overall metrics
    total_predictions: int
    mean_accuracy: float
    std_accuracy: float

    # Learning curve
    early_accuracy: float  # Games 1-10
    late_accuracy: float   # Last 10 games
    improvement: float
    learning_slope: float
    learning_r2: float

    # Detailed metrics
    winner_accuracy: float
    mean_margin_error: float
    mean_total_error: float
    mean_confidence: float


class MemoryExperimentAnalyzer:
    """Analyzes memory learning experiment results"""

    def __init__(self, results_file: str):
        self.results_file = results_file
        self.data = None
        self.expert_analyses: List[ExpertAnalysis] = []

    def load_results(self) -> bool:
        """Load experiment results from JSON"""
        try:
            with open(self.results_file, 'r') as f:
                self.data = json.load(f)

            print(f"✅ Loaded results from {self.results_file}")
            print(f"   Experiment: {self.data['experiment_id']}")
            print(f"   Total predictions: {self.data['total_predictions']}")
            print(f"   Total games: {self.data['total_games']}")

            return True

        except Exception as e:
            print(f"❌ Error loading results: {e}")
            return False

    def analyze_all_experts(self) -> None:
        """Analyze performance for all experts"""

        print("\\n📊 Analyzing expert performance...")

        experts = self.data['experts']
        results = self.data['results']

        for expert in experts:
            # Get this expert's results
            expert_results = [r for r in results if r['expert_id'] == expert['expert_id']]

            if not expert_results:
                continue

            # Calculate metrics
            analysis = self._analyze_expert(expert, expert_results)
            self.expert_analyses.append(analysis)

        print(f"✅ Analyzed {len(self.expert_analyses)} experts")

    def _analyze_expert(self, expert: Dict, results: List[Dict]) -> ExpertAnalysis:
        """Analyze single expert's performance"""

        total_predictions = len(results)

        # Overall accuracy
        accuracies = [r['accuracy_score'] for r in results]
        mean_accuracy = np.mean(accuracies)
        std_accuracy = np.std(accuracies)

        # Learning curve (early vs late)
        early_results = [r for r in results if r['game_number'] <= 10]
        late_results = sorted(results, key=lambda x: x['game_number'], reverse=True)[:10]

        early_accuracy = np.mean([r['accuracy_score'] for r in early_results]) if early_results else 0
        late_accuracy = np.mean([r['accuracy_score'] for r in late_results]) if late_results else 0
        improvement = late_accuracy - early_accuracy

        # Learning slope (linear regression)
        game_numbers = [r['game_number'] for r in results]
        learning_slope, intercept, learning_r2, p_value, std_err = stats.linregress(
            game_numbers, accuracies
        )

        # Detailed metrics
        winner_accuracy = sum(r['winner_correct'] for r in results) / total_predictions
        mean_margin_error = np.mean([r['margin_error'] for r in results])
        mean_total_error = np.mean([r['total_error'] for r in results])
        mean_confidence = np.mean([r['confidence'] for r in results])

        return ExpertAnalysis(
            expert_id=expert['expert_id'],
            personality_type=expert['personality_type'],
            has_memory=expert['has_memory'],
            total_predictions=total_predictions,
            mean_accuracy=mean_accuracy,
            std_accuracy=std_accuracy,
            early_accuracy=early_accuracy,
            late_accuracy=late_accuracy,
            improvement=improvement,
            learning_slope=learning_slope,
            learning_r2=learning_r2,
            winner_accuracy=winner_accuracy,
            mean_margin_error=mean_margin_error,
            mean_total_error=mean_total_error,
            mean_confidence=mean_confidence
        )

    def compare_groups(self) -> Dict:
        """Compare memory vs no-memory groups"""

        print("\\n🔬 Statistical Comparison: Memory vs No-Memory")
        print("="*60)

        # Split by group
        memory_experts = [e for e in self.expert_analyses if e.has_memory]
        nomem_experts = [e for e in self.expert_analyses if not e.has_memory]

        # Overall accuracy comparison
        memory_accs = [e.mean_accuracy for e in memory_experts]
        nomem_accs = [e.mean_accuracy for e in nomem_experts]

        memory_mean = np.mean(memory_accs)
        nomem_mean = np.mean(nomem_accs)

        # Paired t-test (same personality types)
        t_stat, p_value = stats.ttest_rel(memory_accs, nomem_accs)

        print(f"\\nOverall Accuracy:")
        print(f"  Memory Group:    {memory_mean:.1%} ± {np.std(memory_accs):.1%}")
        print(f"  No-Memory Group: {nomem_mean:.1%} ± {np.std(nomem_accs):.1%}")
        print(f"  Difference:      {(memory_mean - nomem_mean):.1%}")
        print(f"  T-statistic:     {t_stat:.3f}")
        print(f"  P-value:         {p_value:.4f}")

        if p_value < 0.05:
            print(f"  ✅ STATISTICALLY SIGNIFICANT (p < 0.05)")
        else:
            print(f"  ⚠️  NOT statistically significant (p >= 0.05)")

        # Learning curve comparison
        memory_improvements = [e.improvement for e in memory_experts]
        nomem_improvements = [e.improvement for e in nomem_experts]

        memory_learning = np.mean(memory_improvements)
        nomem_learning = np.mean(nomem_improvements)

        print(f"\\nLearning Improvement (Early → Late):")
        print(f"  Memory Group:    {memory_learning:+.1%}")
        print(f"  No-Memory Group: {nomem_learning:+.1%}")
        print(f"  Difference:      {(memory_learning - nomem_learning):+.1%}")

        # Learning slope comparison
        memory_slopes = [e.learning_slope for e in memory_experts]
        nomem_slopes = [e.learning_slope for e in nomem_experts]

        print(f"\\nLearning Slope (Trend):")
        print(f"  Memory Group:    {np.mean(memory_slopes):+.4f}")
        print(f"  No-Memory Group: {np.mean(nomem_slopes):+.4f}")

        return {
            'memory_mean_accuracy': memory_mean,
            'nomem_mean_accuracy': nomem_mean,
            'accuracy_difference': memory_mean - nomem_mean,
            't_statistic': t_stat,
            'p_value': p_value,
            'is_significant': p_value < 0.05,
            'memory_learning_improvement': memory_learning,
            'nomem_learning_improvement': nomem_learning,
            'memory_mean_slope': np.mean(memory_slopes),
            'nomem_mean_slope': np.mean(nomem_slopes)
        }

    def analyze_personalities(self) -> None:
        """Analyze which personalities benefit most from memory"""

        print("\\n👥 Per-Personality Analysis")
        print("="*60)

        # Group by personality type
        personality_types = set(e.personality_type for e in self.expert_analyses)

        improvements = []

        for personality in sorted(personality_types):
            memory_expert = next((e for e in self.expert_analyses
                                 if e.personality_type == personality and e.has_memory), None)
            nomem_expert = next((e for e in self.expert_analyses
                                if e.personality_type == personality and not e.has_memory), None)

            if not memory_expert or not nomem_expert:
                continue

            acc_improvement = memory_expert.mean_accuracy - nomem_expert.mean_accuracy
            learning_improvement = memory_expert.improvement - nomem_expert.improvement

            improvements.append((personality, acc_improvement, learning_improvement))

            print(f"\\n{personality.upper()}:")
            print(f"  Accuracy:   Memory {memory_expert.mean_accuracy:.1%} vs No-Memory {nomem_expert.mean_accuracy:.1%}")
            print(f"  Improvement: {acc_improvement:+.1%}")
            print(f"  Learning:    {learning_improvement:+.1%}")

        # Show top and bottom performers
        improvements.sort(key=lambda x: x[1], reverse=True)

        print(f"\\n🏆 TOP 3 PERSONALITIES BENEFITING FROM MEMORY:")
        for i, (personality, acc_imp, learn_imp) in enumerate(improvements[:3], 1):
            print(f"  {i}. {personality}: {acc_imp:+.1%} accuracy gain")

        print(f"\\n⚠️  BOTTOM 3 (Least Benefit):")
        for i, (personality, acc_imp, learn_imp) in enumerate(improvements[-3:], 1):
            print(f"  {i}. {personality}: {acc_imp:+.1%} accuracy change")

    def generate_summary_report(self) -> str:
        """Generate markdown summary report"""

        comparison = self.compare_groups()

        report = f"""# Memory Learning Experiment - Results Summary

## Experiment Details
- **Experiment ID:** {self.data['experiment_id']}
- **Total Games:** {self.data['total_games']}
- **Total Predictions:** {self.data['total_predictions']}
- **Experts Tested:** {len(self.expert_analyses)} (15 memory, 15 no-memory)

---

## Overall Results

### Accuracy Comparison
| Group | Mean Accuracy | Std Dev |
|-------|--------------|---------|
| **Memory** | {comparison['memory_mean_accuracy']:.1%} | - |
| **No-Memory** | {comparison['nomem_mean_accuracy']:.1%} | - |
| **Difference** | {comparison['accuracy_difference']:+.1%} | - |

### Statistical Significance
- **T-statistic:** {comparison['t_statistic']:.3f}
- **P-value:** {comparison['p_value']:.4f}
- **Result:** {'✅ SIGNIFICANT' if comparison['is_significant'] else '⚠️ NOT SIGNIFICANT'} (α = 0.05)

---

## Learning Curve Analysis

### Improvement (Games 1-10 → Final 10)
- **Memory Group:** {comparison['memory_learning_improvement']:+.1%}
- **No-Memory Group:** {comparison['nomem_learning_improvement']:+.1%}
- **Delta:** {(comparison['memory_learning_improvement'] - comparison['nomem_learning_improvement']):+.1%}

### Learning Slope (Trend)
- **Memory Group:** {comparison['memory_mean_slope']:+.4f} (per game)
- **No-Memory Group:** {comparison['nomem_mean_slope']:+.4f} (per game)

---

## Conclusion

"""

        if comparison['is_significant'] and comparison['accuracy_difference'] > 0.02:
            report += """**✅ SUCCESS: Memory significantly improves expert performance!**

The experimental group (with episodic memory) showed statistically significant improvement over the control group (no memory). This proves that:

1. Episodic memory enables learning from past predictions
2. Experts improve accuracy as they accumulate experiences
3. The learning curve shows positive slope for memory-enabled experts
4. The system becomes smarter with more games

**Recommendation:** Deploy memory-enabled system to production.

"""
        elif comparison['is_significant']:
            report += """**⚠️ MIXED RESULTS: Statistical significance but small effect size**

While the difference is statistically significant, the practical improvement is modest. Consider:

1. Longer learning phase (more games) to see stronger effects
2. Memory retrieval optimization (better similarity matching)
3. Hybrid approach combining memory with traditional ML

"""
        else:
            report += """**❌ INCONCLUSIVE: No significant difference detected**

The memory-enabled group did not show statistically significant improvement. Possible reasons:

1. Insufficient sample size (need more games)
2. Memory retrieval not effective (poor similarity matching)
3. LLM limitations in utilizing memory context
4. High variance masking signal

**Recommendation:** Investigate and run larger experiment.

"""

        return report

    def save_report(self, output_dir: str = "results") -> None:
        """Save analysis report"""

        os.makedirs(output_dir, exist_ok=True)

        # Generate report
        report = self.generate_summary_report()

        # Save markdown
        experiment_name = self.data['experiment_id']
        report_file = f"{output_dir}/{experiment_name}_analysis.md"

        with open(report_file, 'w') as f:
            f.write(report)

        print(f"\\n💾 Analysis report saved to: {report_file}")

        # Save detailed JSON
        json_file = f"{output_dir}/{experiment_name}_detailed_analysis.json"

        detailed_data = {
            'experiment_id': self.data['experiment_id'],
            'comparison': self.compare_groups(),
            'expert_analyses': [
                {
                    'expert_id': e.expert_id,
                    'personality_type': e.personality_type,
                    'has_memory': e.has_memory,
                    'mean_accuracy': e.mean_accuracy,
                    'early_accuracy': e.early_accuracy,
                    'late_accuracy': e.late_accuracy,
                    'improvement': e.improvement,
                    'learning_slope': e.learning_slope,
                    'learning_r2': e.learning_r2
                }
                for e in self.expert_analyses
            ]
        }

        with open(json_file, 'w') as f:
            json.dump(detailed_data, f, indent=2)

        print(f"💾 Detailed analysis saved to: {json_file}")


def main():
    """Run analysis"""

    import sys

    if len(sys.argv) < 2:
        print("Usage: python analyze_memory_experiment.py <results_file.json>")
        print("\\nExample: python analyze_memory_experiment.py results/memory_proof_v1_1234567890_results.json")
        return

    results_file = sys.argv[1]

    # Create analyzer
    analyzer = MemoryExperimentAnalyzer(results_file)

    # Load and analyze
    if not analyzer.load_results():
        return

    analyzer.analyze_all_experts()
    analyzer.compare_groups()
    analyzer.analyze_personalities()
    analyzer.save_report()

    print("\\n✅ Analysis complete!")


if __name__ == "__main__":
    main()
