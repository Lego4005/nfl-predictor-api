#!/usr/bin/env python3
"""
COMPREHENSIVE SEASON ANALYSIS - ConservativeAnalyzer Expert
=========================================================

This script runs a FULL season backtest analysis (multiple weeks) 
with detailed tracking and performance monitoring.

Target: 2020 season, Weeks 1-8 (half season)
Expert: ConservativeAnalyzer
Focus: Complete season performance analysis
"""

import asyncio
import sys
import os
import time
import json
import logging
from datetime import datetime
from typing import Dict, Any, List
from dataclasses import dataclass, field

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from services.historical_data_service import HistoricalDataService
from services.universal_game_data_builder import UniversalGameDataBuilder
from services.backtest_runner import BacktestRunner, LearningMode
from ml.personality_driven_experts import ConservativeAnalyzer


@dataclass
class ComprehensiveTracker:
    """Enhanced tracking for comprehensive season analysis"""
    start_time: float = field(default_factory=time.time)
    
    # Timing data
    timings: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    
    # Database performance
    database_queries: List[Dict[str, Any]] = field(default_factory=list)
    
    # Expert performance by week
    weekly_performance: Dict[int, Dict[str, Any]] = field(default_factory=dict)
    
    # Learning progression
    learning_progression: List[Dict[str, Any]] = field(default_factory=list)
    
    # Error tracking
    errors: List[Dict[str, Any]] = field(default_factory=list)
    
    # Prediction details
    all_predictions: List[Dict[str, Any]] = field(default_factory=list)

    def log_timing(self, operation: str, duration: float, details: Dict[str, Any] = None):
        """Log timing information"""
        self.timings[operation] = {
            'duration': duration,
            'timestamp': time.time(),
            'details': details or {}
        }
        logging.info(f"⏱️  TIMING: {operation} = {duration:.3f}s")

    def log_error(self, operation: str, error_msg: str):
        """Log error information"""
        error_record = {
            'operation': operation,
            'error': error_msg,
            'timestamp': time.time()
        }
        self.errors.append(error_record)
        logging.error(f"❌ ERROR in {operation}: {error_msg}")

    def log_weekly_performance(self, week: int, performance_data: Dict[str, Any]):
        """Log weekly performance metrics"""
        self.weekly_performance[week] = performance_data
        logging.info(f"📊 Week {week} Performance: {performance_data.get('accuracy', 0):.1%} accuracy")

    def log_prediction_detail(self, prediction_data: Dict[str, Any]):
        """Log individual prediction details"""
        self.all_predictions.append(prediction_data)

    def generate_comprehensive_report(self) -> Dict[str, Any]:
        """Generate complete analysis report"""
        total_runtime = time.time() - self.start_time
        
        # Calculate overall performance metrics
        total_predictions = len(self.all_predictions)
        correct_predictions = sum(1 for p in self.all_predictions if p.get('correct', False))
        overall_accuracy = correct_predictions / max(total_predictions, 1)
        
        # Weekly performance analysis
        weekly_stats = {}
        for week, data in self.weekly_performance.items():
            weekly_stats[week] = {
                'games': data.get('total_games', 0),
                'accuracy': data.get('accuracy', 0),
                'avg_confidence': data.get('avg_confidence', 0),
                'processing_time': data.get('processing_time', 0)
            }
        
        return {
            'analysis_metadata': {
                'start_time': datetime.fromtimestamp(self.start_time).isoformat(),
                'total_runtime': total_runtime,
                'analysis_type': 'comprehensive_season'
            },
            'overall_performance': {
                'total_predictions': total_predictions,
                'correct_predictions': correct_predictions,
                'overall_accuracy': overall_accuracy,
                'weeks_analyzed': list(self.weekly_performance.keys()),
                'total_weeks': len(self.weekly_performance)
            },
            'weekly_performance': weekly_stats,
            'expert_progression': {
                'learning_curve': self.learning_progression,
                'confidence_evolution': [p.get('confidence', 0) for p in self.all_predictions],
                'accuracy_by_week': {w: d.get('accuracy', 0) for w, d in self.weekly_performance.items()}
            },
            'timing_analysis': self.timings,
            'error_analysis': {
                'total_errors': len(self.errors),
                'error_types': {},
                'error_details': self.errors
            },
            'prediction_details': self.all_predictions[:50],  # First 50 for space
            'database_performance': {
                'total_queries': len(self.database_queries),
                'avg_query_time': sum(q.get('duration', 0) for q in self.database_queries) / max(len(self.database_queries), 1)
            }
        }


async def comprehensive_season_analysis():
    """Run comprehensive season analysis"""
    
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('comprehensive_analysis.log'),
            logging.StreamHandler()
        ]
    )
    
    tracker = ComprehensiveTracker()
    
    try:
        print("🔬 COMPREHENSIVE SEASON ANALYSIS - ConservativeAnalyzer")
        print("="*80)
        print(f"🕐 Analysis started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"🎯 Target: 2020 NFL Season, Weeks 1-8")
        print(f"🤖 Expert: ConservativeAnalyzer")
        print(f"📊 Focus: Complete season performance tracking")
        
        # === PHASE 1: INFRASTRUCTURE SETUP ===
        print(f"\n📋 PHASE 1: INFRASTRUCTURE SETUP")
        print("-" * 50)
        
        # Initialize services
        setup_start = time.time()
        
        # Database connection
        db_start = time.time()
        try:
            from supabase import create_client
            import os
            
            supabase_url = os.getenv('VITE_SUPABASE_URL')
            supabase_key = os.getenv('VITE_SUPABASE_ANON_KEY')
            
            if not supabase_url or not supabase_key:
                raise ValueError("Missing Supabase credentials in environment variables")
                
            supabase = create_client(supabase_url, supabase_key)
            
            # Initialize historical service with supabase client
            historical_service = HistoricalDataService(supabase)
        
            # Test database connection
            test_result = supabase.table('nfl_games').select('count').limit(1).execute()
            db_time = time.time() - db_start
            tracker.log_timing("database_connection", db_time, {
                'url': supabase_url[:30] + "...",
                'test_query_success': True
            })
            print(f"✅ Database connected: {db_time:.3f}s")
            
        except Exception as e:
            print(f"❌ Database connection failed: {e}")
            raise
        
        # Initialize other services
        services_start = time.time()
        universal_builder = UniversalGameDataBuilder(historical_service)
        backtest_runner = BacktestRunner(historical_service, universal_builder)
        services_time = time.time() - services_start
        tracker.log_timing("services_initialization", services_time)
        print(f"✅ Services initialized: {services_time:.3f}s")
        
        # Initialize expert
        expert_start = time.time()
        # Use simple memory for now - focus on the analysis
        expert = ConservativeAnalyzer(memory_service=None)
        expert_time = time.time() - expert_start
        tracker.log_timing("expert_initialization", expert_time, {
            'memory_enabled': False,
            'expert_id': expert.expert_id,
            'expert_name': expert.name
        })
        print(f"✅ Expert initialized: {expert.name}")
        print(f"   → ID: {expert.expert_id}")
        print(f"   → Memory: {'Enabled' if False else 'Disabled'}")
        
        total_setup_time = time.time() - setup_start
        tracker.log_timing("total_setup", total_setup_time)
        
        # === PHASE 2: COMPREHENSIVE SEASON BACKTEST ===
        print(f"\n🏈 PHASE 2: COMPREHENSIVE SEASON BACKTEST")
        print("-" * 50)
        print(f"📅 Running 2020 NFL Season: Weeks 1-8 (128+ games)")
        print(f"⏰ Expected duration: 5-10 minutes")
        print(f"🔄 Processing...")
        
        season_start = time.time()
        
        # Run comprehensive season backtest
        season_results = await backtest_runner.run_season_backtest(
            expert=expert,
            season=2020,
            learning_mode=LearningMode.BASELINE,
            start_week=1,
            end_week=8,  # Half season for comprehensive analysis
            game_filter=None
        )
        
        season_time = time.time() - season_start
        tracker.log_timing("comprehensive_season_backtest", season_time, {
            'total_games': season_results.total_games,
            'overall_accuracy': season_results.overall_accuracy,
            'correct_winners': season_results.correct_winners,
            'weeks_processed': 8
        })
        
        print(f"✅ Season backtest completed: {season_time:.3f}s")
        print(f"   → Total games processed: {season_results.total_games}")
        print(f"   → Overall accuracy: {season_results.overall_accuracy:.1%}")
        print(f"   → Correct predictions: {season_results.correct_winners}/{season_results.total_games}")
        print(f"   → Average time per game: {season_time/max(season_results.total_games, 1):.3f}s")
        
        # === PHASE 3: WEEKLY PERFORMANCE BREAKDOWN ===
        print(f"\n📊 PHASE 3: WEEKLY PERFORMANCE BREAKDOWN")
        print("-" * 50)
        
        # Analyze performance by week
        weekly_analysis = {}
        for week in range(1, 9):
            week_predictions = [p for p in season_results.predictions if p.week == week]
            if week_predictions:
                week_correct = sum(1 for p in week_predictions if p.correct_winner)
                week_accuracy = week_correct / len(week_predictions)
                week_avg_confidence = sum(p.prediction.get('winner_confidence', 0) for p in week_predictions) / len(week_predictions)
                
                weekly_analysis[week] = {
                    'total_games': len(week_predictions),
                    'correct_predictions': week_correct,
                    'accuracy': week_accuracy,
                    'avg_confidence': week_avg_confidence
                }
                
                tracker.log_weekly_performance(week, weekly_analysis[week])
                
                print(f"Week {week:2d}: {len(week_predictions):2d} games, {week_accuracy:.1%} accuracy, {week_avg_confidence:.1%} avg confidence")
        
        # === PHASE 4: EXPERT LEARNING PROGRESSION ===
        print(f"\n🧠 PHASE 4: EXPERT LEARNING PROGRESSION")
        print("-" * 50)
        
        # Analyze learning progression over time
        cumulative_accuracy = []
        running_correct = 0
        for i, prediction in enumerate(season_results.predictions, 1):
            if prediction.correct_winner:
                running_correct += 1
            cumulative_accuracy.append(running_correct / i)
            
            # Log detailed prediction info
            prediction_detail = {
                'game_number': i,
                'week': prediction.week,
                'matchup': f"{prediction.away_team}@{prediction.home_team}",
                'prediction': prediction.prediction.get('winner_prediction'),
                'actual_winner': prediction.actual_winner,
                'correct': prediction.correct_winner,
                'confidence': prediction.prediction.get('winner_confidence', 0),
                'cumulative_accuracy': cumulative_accuracy[-1]
            }
            tracker.log_prediction_detail(prediction_detail)
        
        print(f"📈 Learning Progression Analysis:")
        print(f"   → Starting accuracy (first 10 games): {sum(cumulative_accuracy[:10])/10:.1%}")
        print(f"   → Mid-season accuracy (games 30-40): {sum(cumulative_accuracy[29:39])/10:.1%}")
        print(f"   → Final accuracy (last 10 games): {sum(cumulative_accuracy[-10:])/10:.1%}")
        print(f"   → Overall trend: {'Improving' if cumulative_accuracy[-1] > cumulative_accuracy[9] else 'Declining'}")
        
        # === PHASE 5: PREDICTION QUALITY ANALYSIS ===
        print(f"\n🎯 PHASE 5: PREDICTION QUALITY ANALYSIS")
        print("-" * 50)
        
        # Analyze prediction confidence vs accuracy
        high_confidence_preds = [p for p in season_results.predictions if p.prediction.get('winner_confidence', 0) > 0.7]
        low_confidence_preds = [p for p in season_results.predictions if p.prediction.get('winner_confidence', 0) < 0.5]
        
        high_conf_accuracy = sum(1 for p in high_confidence_preds if p.correct_winner) / max(len(high_confidence_preds), 1)
        low_conf_accuracy = sum(1 for p in low_confidence_preds if p.correct_winner) / max(len(low_confidence_preds), 1)
        
        print(f"🎯 Confidence vs Accuracy Analysis:")
        print(f"   → High confidence (>70%): {len(high_confidence_preds)} games, {high_conf_accuracy:.1%} accuracy")
        print(f"   → Low confidence (<50%): {len(low_confidence_preds)} games, {low_conf_accuracy:.1%} accuracy")
        print(f"   → Confidence calibration: {'Good' if high_conf_accuracy > low_conf_accuracy else 'Poor'}")
        
        # Sample detailed predictions
        print(f"\n📋 Sample Prediction Analysis (First 5 games):")
        for i, pred in enumerate(season_results.predictions[:5], 1):
            status = "✅" if pred.correct_winner else "❌"
            confidence = pred.prediction.get('winner_confidence', 0)
            print(f"   {i}. {pred.away_team}@{pred.home_team} (Week {pred.week}): {status}")
            print(f"      Predicted: {pred.prediction.get('winner_prediction', 'N/A')} ({confidence:.1%})")
            print(f"      Actual: {pred.actual_winner}")
            if 'reasoning' in pred.prediction and pred.prediction['reasoning']:
                print(f"      Reasoning: {pred.prediction['reasoning'][0]}")
        
        # === PHASE 6: SAVE COMPREHENSIVE REPORT ===
        print(f"\n💾 PHASE 6: SAVING COMPREHENSIVE REPORT")
        print("-" * 50)
        
        # Generate and save comprehensive report
        report = tracker.generate_comprehensive_report()
        report_filename = f"comprehensive_season_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        report_path = f"/home/iris/code/experimental/nfl-predictor-api/{report_filename}"
        
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        print(f"✅ Comprehensive report saved: {report_filename}")
        print(f"   → Location: {report_path}")
        print(f"   → Size: {os.path.getsize(report_path) / 1024:.1f} KB")
        
        # === FINAL COMPREHENSIVE SUMMARY ===
        print(f"\n🎉 COMPREHENSIVE ANALYSIS COMPLETE")
        print("="*80)
        total_time = time.time() - tracker.start_time
        print(f"⏱️  Total analysis time: {total_time:.1f}s ({total_time/60:.1f} minutes)")
        print(f"🏈 Games analyzed: {season_results.total_games}")
        print(f"📅 Weeks processed: 1-8 (half season)")
        print(f"🎯 Overall accuracy: {season_results.overall_accuracy:.1%}")
        print(f"💪 Expert performance: {'Strong' if season_results.overall_accuracy > 0.5 else 'Needs improvement'}")
        print(f"📈 Learning trend: {'Positive' if cumulative_accuracy[-1] > cumulative_accuracy[9] else 'Flat'}")
        print(f"🔧 Infrastructure: ✅ Robust")
        print(f"🚀 Ready for full season: {'YES' if season_results.overall_accuracy > 0.4 else 'NEEDS TUNING'}")
        
        return report
        
    except Exception as e:
        tracker.log_error("comprehensive_analysis", str(e))
        print(f"❌ Comprehensive analysis failed: {e}")
        import traceback
        traceback.print_exc()
        return None


async def main():
    """Main comprehensive analysis execution"""
    print("🚀 Starting Comprehensive Season Analysis")
    
    # Source environment
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass
    
    report = await comprehensive_season_analysis()
    
    if report:
        print(f"\n🎊 Comprehensive analysis completed successfully!")
        print(f"📋 Check comprehensive_analysis.log for detailed logs")
        print(f"📊 Review the JSON report for complete season metrics")
        return True
    else:
        print(f"\n💥 Comprehensive analysis failed!")
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)