#!/usr/bin/env python3
"""
Process Complete 2020 Season

Runs all 2020 regular season games th training loop,
generates predictions for all 15 experts, stores predictions/outcomes/memories,
and tracks expert performance evolution over the season.
"""

import sys
import logging
import asyncio
import json
from datetime import datetime
from pathlib import Path
sys.path.append('src')

from training.training_loop_orchestrator import TrainingLoopOrchestrator
from training.post_game_analyzer import PostGameAnalyzer

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('2020_season_processing.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class Season2020Processor:
    """Processes the complete 2020 NFL season for expert training"""

    def __init__(self, output_dir: str = "2020_season_results"):
        """Initialize the season processor"""
        self.orchestrator = TrainingLoopOrchestrator()
        self.analyzer = PostGameAnalyzer()
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)

        # Results tracking
        self.season_results = {
            'season': 2020,
            'start_time': None,
            'end_time': None,
            'total_games': 0,
            'processed_games': 0,
            'total_predictions': 0,
            'expert_performance': {},
            'game_analyses': [],
            'learning_memories': {}
        }

        logger.info("✅ Season 2020 Processor initialized")

    async def process_complete_season(self) -> dict:
        """Process the complete 2020 NFL regular season"""
        logger.info("🚀 Starting complete 2020 season processing...")

        self.season_results['start_time'] = datetime.now().isoformat()

        try:
            # Initialize Neo4j connection
            await self.orchestrator.initialize_neo4j()

            # Process the complete season (no game limit)
            logger.info("📊 Processing all 2020 regular season games...")
            training_session = await self.orchestrator.process_season(2020)

            # Store training session results
            self.season_results.update({
                'total_games': training_session.games_processed,
                'processed_games': training_session.games_processed,
                'total_predictions': training_session.total_predictions,
                'expert_performance': self.orchestrator.get_expert_performance_summary()
            })

            # Analyze all games for learning insights
            await self._analyze_all_games()

            # Generate comprehensive season report
            await self._generate_season_report()

            # Save all results
            await self._save_results()

            self.season_results['end_time'] = datetime.now().isoformat()

            logger.info("✅ Complete 2020 season processing finished!")
            return self.season_results

        except Exception as e:
            logger.error(f"❌ Season processing failed: {e}")
            self.season_results['end_time'] = datetime.now().isoformat()
            self.season_results['error'] = str(e)
            raise

    async def _analyze_all_games(self):
        """Analyze all processed games for learning insights"""
        logger.info("📊 Analyzing all games for learning insights...")

        # Load predictions and outcomes from checkpoint files
        predictions_file = Path("training_checkpoints/predictions_2020.jsonl")
        outcomes_file = Path("training_checkpoints/outcomes_2020.jsonl")

        if not predictions_file.exists() or not outcomes_file.exists():
            logger.warning("⚠️ Prediction/outcome files not found - skipping detailed analysis")
            return

        # Load all predictions and outcomes
        predictions_data = []
        outcomes_data = []

        with open(predictions_file, 'r') as f:
            for line in f:
                predictions_data.append(json.loads(line))

        with open(outcomes_file, 'r') as f:
            for line in f:
                outcomes_data.append(json.loads(line))

        logger.info(f"📈 Loaded {len(predictions_data)} prediction records and {len(outcomes_data)} outcome records")

        # Store for analysis
        self.season_results['predictions_data'] = predictions_data
        self.season_results['outcomes_data'] = outcomes_data

    async def _generate_season_report(self):
        """Generate comprehensive season analysis report"""
        logger.info("📋 Generating comprehensive season report...")

        performance = self.season_results['expert_performance']

        # Calculate season-wide statistics
        total_experts = len(performance)
        avg_accuracy = sum(expert['accuracy'] for expert in performance.values()) / total_experts

        # Find best and worst performers
        best_expert = max(performance.items(), key=lambda x: x[1]['accuracy'])
        worst_expert = min(performance.items(), key=lambda x: x[1]['accuracy'])

        # Find most and least confident experts
        most_confident = max(performance.items(), key=lambda x: x[1]['avg_confidence'])
        least_confident = min(performance.items(), key=lambda x: x[1]['avg_confidence'])

        season_report = {
            'season_overview': {
                'season': 2020,
                'total_games': self.season_results['total_games'],
                'total_predictions': self.season_results['total_predictions'],
                'total_experts': total_experts,
                'average_accuracy': avg_accuracy,
                'processing_duration': self._calculate_duration()
            },
            'expert_rankings': {
                'by_accuracy': sorted(performance.items(), key=lambda x: x[1]['accuracy'], reverse=True),
                'by_confidence': sorted(performance.items(), key=lambda x: x[1]['avg_confidence'], reverse=True)
            },
            'notable_performers': {
                'best_expert': {
                    'id': best_expert[0],
                    'accuracy': best_expert[1]['accuracy'],
                    'games': best_expert[1]['games_processed']
                },
                'worst_expert': {
                    'id': worst_expert[0],
                    'accuracy': worst_expert[1]['accuracy'],
                    'games': worst_expert[1]['games_processed']
                },
                'most_confident': {
                    'id': most_confident[0],
                    'avg_confidence': most_confident[1]['avg_confidence'],
                    'accuracy': most_confident[1]['accuracy']
                },
                'least_confident': {
                    'id': least_confident[0],
                    'avg_confidence': least_confident[1]['avg_confidence'],
                    'accuracy': least_confident[1]['accuracy']
                }
            },
            'system_insights': self._generate_system_insights()
        }

        self.season_results['season_report'] = season_report

        # Log key findings
        logger.info(f"📊 Season 2020 Results Summary:")
        logger.info(f"   Games Processed: {self.season_results['total_games']}")
        logger.info(f"   Total Predictions: {self.season_results['total_predictions']}")
        logger.info(f"   Average Accuracy: {avg_accuracy:.1%}")
        logger.info(f"   Best Expert: {best_expert[0]} ({best_expert[1]['accuracy']:.1%})")
        logger.info(f"   Worst Expert: {worst_expert[0]} ({worst_expert[1]['accuracy']:.1%})")

    def _calculate_duration(self) -> str:
        """Calculate processing duration"""
        if not self.season_results['start_time'] or not self.season_results['end_time']:
            return "Unknown"

        start = datetime.fromisoformat(self.season_results['start_time'])
        end = datetime.fromisoformat(self.season_results['end_time'])
        duration = end - start

        hours = duration.total_seconds() / 3600
        return f"{hours:.2f} hours"

    def _generate_system_insights(self) -> list:
        """Generate insights about the expert system performance"""
        insights = []
        performance = self.season_results['expert_performance']

        # Accuracy distribution analysis
        accuracies = [expert['accuracy'] for expert in performance.values()]
        accuracy_range = max(accuracies) - min(accuracies)

        if accuracy_range > 0.15:  # 15% spread
            insights.append("High variance in expert performance - good differentiation achieved")
        else:
            insights.append("Low variance in expert performance - may need personality tuning")

        # Confidence vs accuracy analysis
        for expert_id, stats in performance.items():
            accuracy = stats['accuracy']
            confidence = stats['avg_confidence']

            # Check for overconfident experts
            if confidence > 0.7 and accuracy < 0.5:
                insights.append(f"{expert_id} shows overconfidence - high confidence but low accuracy")

            # Check for underconfident experts
            if confidence < 0.3 and accuracy > 0.6:
                insights.append(f"{expert_id} shows underconfidence - low confidence but high accuracy")

        # Overall system health
        avg_accuracy = sum(accuracies) / len(accuracies)
        if avg_accuracy > 0.55:
            insights.append("System shows positive predictive value above random chance")
        else:
            insights.append("System accuracy near random - may need fundamental improvements")

        return insights

    async def _save_results(self):
        """Save all results to files"""
        logger.info("💾 Saving season processing results...")

        # Save main results
        results_file = self.output_dir / "2020_season_complete_results.json"
        with open(results_file, 'w') as f:
            json.dump(self.season_results, f, indent=2, default=str)

        # Save expert performance summary
        performance_file = self.output_dir / "expert_performance_summary.json"
        with open(performance_file, 'w') as f:
            json.dump(self.season_results['expert_performance'], f, indent=2)

        # Save season report
        if 'season_report' in self.season_results:
            report_file = self.output_dir / "season_analysis_report.json"
            with open(report_file, 'w') as f:
                json.dump(self.season_results['season_report'], f, indent=2, default=str)

        logger.info(f"📁 Results saved to {self.output_dir}/")

    def get_processing_status(self) -> dict:
        """Get current processing status"""
        return {
            'season': 2020,
            'status': 'completed' if self.season_results.get('end_time') else 'in_progress',
            'games_processed': self.season_results['processed_games'],
            'total_predictions': self.season_results['total_predictions'],
            'start_time': self.season_results['start_time'],
            'end_time': self.season_results.get('end_time'),
            'duration': self._calculate_duration() if self.season_results.get('end_time') else None
        }


async def main():
    """Main execution function"""
    print("🏈 2020 NFL Season Complete Processing")
    print("=" * 60)

    processor = Season2020Processor()

    try:
        # Process the complete season
        results = await processor.process_complete_season()

        print(f"\n✅ Season processing completed successfully!")
        print(f"📊 Final Results:")
        print(f"   Games Processed: {results['total_games']}")
        print(f"   Total Predictions: {results['total_predictions']}")
        print(f"   Processing Duration: {processor._calculate_duration()}")

        if 'season_report' in results:
            report = results['season_report']
            print(f"   Average Accuracy: {report['season_overview']['average_accuracy']:.1%}")
            print(f"   Best Expert: {report['notable_performers']['best_expert']['id']} ({report['notable_performers']['best_expert']['accuracy']:.1%})")

        print(f"\n📁 Detailed results saved to: 2020_season_results/")
        print(f"📋 Check the following files:")
        print(f"   • 2020_season_complete_results.json - Complete processing results")
        print(f"   • expert_performance_summary.json - Expert performance metrics")
        print(f"   • season_analysis_report.json - Comprehensive season analysis")

    except Exception as e:
        print(f"❌ Season processing failed: {e}")
        logger.error(f"Processing failed: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
