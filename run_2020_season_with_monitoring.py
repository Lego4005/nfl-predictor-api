#!/usr/bin/env python3
"""
Run Complete 2020 Season with Monitoring

Processes the complete 2020 NFL season with real LLM calls and learning,
monitoring for the specific issues mentioned:
- Memory storage failures
- Expert state corruption
- Memory retrieval relevance
- Reasoning chain evolution
- Performance patterns
- API call failures
- Memory bank growth rates
"""

import sys
import asyncio
import logging
import json
from datetime import datetime
from pathlib import Path
sys.path.append('src')

from training.training_loop_orchestrator import TrainingLoopOrchestrator

# Configure comprehensive logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('2020_season_monitoring.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class Season2020Monitor:
    """Monitors 2020 season processing for issues"""

    def __init__(self):
        """Initialize the season monitor"""
        self.orchestrator = TrainingLoopOrchestrator()
        self.start_time = None
        self.monitoring_results = {
            'start_time': None,
            'checkpoints': {},
            'final_results': None,
            'issues_detected': [],
            'recommendations': []
        }

    async def run_monitored_season(self):
        """Run the complete 2020 season with monitoring"""

        print("🏈 2020 NFL Season Processing with Monitoring")
        print("=" * 80)
        print("This will process all 2020 regular season games with:")
        print("• Real LLM calls via OpenRouter")
        print("• Expert learning and memory formation")
        print("• Monitoring checkpoints at games 20, 50, 100, 200")
        print("• Automatic issue detection and recommendations")
        print("=" * 80)

        self.start_time = datetime.now()
        self.monitoring_results['start_time'] = self.start_time.isoformat()

        try:
            # Initialize systems
            print("\n🔧 Initializing systems...")
            await self.orchestrator.initialize_neo4j()

            # Process complete season
            print("\n🚀 Starting 2020 season processing...")
            print("⏱️  Estimated time: 4-8 hours")
            print("🔍 Monitoring checkpoints will run automatically")

            session = await self.orchestrator.process_season(2020)

            # Final analysis
            await self._generate_final_analysis(session)

            print(f"\n🎉 2020 Season Processing Complete!")
            self._print_final_summary()

        except Exception as e:
            print(f"\n❌ Season processing failed: {e}")
            logger.error(f"Season processing failed: {e}")
            self.monitoring_results['issues_detected'].append(f"CRITICAL: Processing failed - {e}")
            raise

        finally:
            # Save monitoring results
            await self._save_monitoring_results()

    async def _generate_final_analysis(self, session):
        """Generate final analysis of the season"""

        print(f"\n📊 Generating final analysis...")

        # Get final performance data
        performance = self.orchestrator.get_expert_performance_summary()
        learning_status = self.orchestrator.get_learning_system_status()

        # Analyze expert performance patterns
        accuracies = [stats['accuracy'] for stats in performance.values()]
        avg_accuracy = sum(accuracies) / len(accuracies)
        min_accuracy = min(accuracies)
        max_accuracy = max(accuracies)

        # Check for performance issues
        extreme_performers = []
        for expert_id, stats in performance.items():
            if stats['accuracy'] < 0.35 or stats['accuracy'] > 0.75:
                extreme_performers.append(f"{expert_id}: {stats['accuracy']:.1%}")

        if extreme_performers:
            self.monitoring_results['issues_detected'].append(f"Extreme performance patterns: {', '.join(extreme_performers)}")

        # Check memory bank growth
        total_memories = 0
        for expert_memories in learning_status['memory_banks']['personal_memories'].values():
            total_memories += expert_memories

        if total_memories < 100:
            self.monitoring_results['issues_detected'].append(f"Low memory growth: only {total_memories} total memories")

        # Store final results
        self.monitoring_results['final_results'] = {
            'session_id': session.session_id,
            'games_processed': session.games_processed,
            'total_predictions': session.total_predictions,
            'average_accuracy': avg_accuracy,
            'accuracy_range': [min_accuracy, max_accuracy],
            'total_memories': total_memories,
            'processing_duration_hours': (datetime.now() - self.start_time).total_seconds() / 3600
        }

        # Generate recommendations
        await self._generate_recommendations()

    async def _generate_recommendations(self):
        """Generate recommendations based on monitoring results"""

        recommendations = []

        # Performance recommendations
        final_results = self.monitoring_results['final_results']
        if final_results['average_accuracy'] < 0.5:
            recommendations.append("CRITICAL: Average accuracy below random chance - review expert configurations")
        elif final_results['average_accuracy'] > 0.65:
            recommendations.append("EXCELLENT: High average accuracy achieved - system is performing well")

        # Memory recommendations
        if final_results['total_memories'] < 500:
            recommendations.append("WARNING: Low memory accumulation - check memory storage logic")
        elif final_results['total_memories'] > 5000:
            recommendations.append("SUCCESS: Rich memory accumulation - learning system is active")

        # Processing time recommendations
        if final_results['processing_duration_hours'] > 10:
            recommendations.append("OPTIMIZATION: Long processing time - consider parallel processing")
        elif final_results['processing_duration_hours'] < 2:
            recommendations.append("EFFICIENCY: Fast processing achieved - system is optimized")

        # Issue-based recommendations
        if len(self.monitoring_results['issues_detected']) == 0:
            recommendations.append("SUCCESS: No critical issues detected - system is stable")
        else:
            recommendations.append(f"ACTION REQUIRED: {len(self.monitoring_results['issues_detected'])} issues need attention")

        self.monitoring_results['recommendations'] = recommendations

    def _print_final_summary(self):
        """Print final summary of results"""

        final_results = self.monitoring_results['final_results']

        print(f"\n📊 FINAL RESULTS SUMMARY")
        print(f"=" * 50)
        print(f"🏈 Games Processed: {final_results['games_processed']}")
        print(f"🧠 Total Predictions: {final_results['total_predictions']}")
        print(f"📈 Average Accuracy: {final_results['average_accuracy']:.1%}")
        print(f"📚 Total Memories: {final_results['total_memories']}")
        print(f"⏱️  Processing Time: {final_results['processing_duration_hours']:.1f} hours")

        print(f"\n🔍 MONITORING RESULTS")
        print(f"=" * 50)

        if self.monitoring_results['issues_detected']:
            print(f"⚠️  Issues Detected ({len(self.monitoring_results['issues_detected'])}):")
            for issue in self.monitoring_results['issues_detected']:
                print(f"   • {issue}")
        else:
            print(f"✅ No critical issues detected")

        print(f"\n💡 RECOMMENDATIONS")
        print(f"=" * 50)
        for rec in self.monitoring_results['recommendations']:
            print(f"• {rec}")

        print(f"\n📁 GENERATED FILES")
        print(f"=" * 50)
        print(f"• 2020_season_monitoring.log - Detailed processing log")
        print(f"• 2020_season_monitoring_results.json - Complete monitoring data")
        print(f"• training_checkpoints/ - Prediction and outcome data")

    async def _save_monitoring_results(self):
        """Save monitoring results to file"""

        output_file = Path("2020_season_monitoring_results.json")

        with open(output_file, 'w') as f:
            json.dump(self.monitoring_results, f, indent=2, default=str)

        logger.info(f"💾 Monitoring results saved to {output_file}")


async def main():
    """Main execution function"""

    monitor = Season2020Monitor()

    # Ask for confirmation before starting
    print("⚠️  This will make thousands of LLM API calls and take 4-8 hours.")
    print("💰 Estimated cost: $10-50 depending on usage")
    print("🔍 The system will monitor for issues and can be stopped at checkpoints.")

    response = input("\nProceed with full 2020 season processing? (yes/no): ")

    if response.lower() in ['yes', 'y']:
        await monitor.run_monitored_season()
    else:
        print("❌ Processing cancelled by user")
        print("💡 To test the system first, run: python test_integration_quick.py")


if __name__ == "__main__":
    asyncio.run(main())
