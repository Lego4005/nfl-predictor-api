#!/usr/bin/env python3
"""
Detailed Expert Analysis - ConservativeAnalyzer Deep Dive

This script provides comprehensive analysis of our backtesting infrastructure
with detailed logging, timing, and expert behavior tracking for review.
"""

import os
import sys
import time
import json
import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Any
from dataclasses import asdict

# Add project paths
sys.path.append('/home/iris/code/experimental/nfl-predictor-api/src')

# Environment setup
os.environ.setdefault('ENV', 'development')

# Configure detailed logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('/home/iris/code/experimental/nfl-predictor-api/detailed_analysis.log')
    ]
)
logger = logging.getLogger(__name__)


class DetailedAnalysisTracker:
    """Comprehensive tracking of infrastructure and expert performance"""
    
    def __init__(self):
        self.start_time = time.time()
        self.timings = {}
        self.database_queries = []
        self.expert_predictions = []
        self.errors = []
        self.memory_operations = []
        self.game_context_data = []
        
    def log_timing(self, operation: str, duration: float, details: Dict = None):
        """Log timing information"""
        self.timings[operation] = {
            'duration': duration,
            'timestamp': time.time(),
            'details': details or {}
        }
        logger.info(f"⏱️  TIMING: {operation} = {duration:.3f}s")
        
    def log_database_query(self, query_type: str, duration: float, success: bool, details: Dict = None):
        """Log database query performance"""
        query_log = {
            'type': query_type,
            'duration': duration,
            'success': success,
            'timestamp': time.time(),
            'details': details or {}
        }
        self.database_queries.append(query_log)
        
    def log_expert_prediction(self, game_info: Dict, prediction: Dict, timing: float, context: Dict = None):
        """Log expert prediction details"""
        prediction_log = {
            'game': game_info,
            'prediction': prediction,
            'timing': timing,
            'context': context or {},
            'timestamp': time.time()
        }
        self.expert_predictions.append(prediction_log)
        
    def log_error(self, error_type: str, error_msg: str, context: Dict = None):
        """Log errors for analysis"""
        error_log = {
            'type': error_type,
            'message': error_msg,
            'context': context or {},
            'timestamp': time.time()
        }
        self.errors.append(error_log)
        
    def generate_comprehensive_report(self) -> Dict:
        """Generate comprehensive analysis report"""
        total_time = time.time() - self.start_time
        
        # Database performance analysis
        db_queries = len(self.database_queries)
        successful_queries = sum(1 for q in self.database_queries if q['success'])
        avg_query_time = sum(q['duration'] for q in self.database_queries) / max(db_queries, 1)
        
        # Expert performance analysis
        total_predictions = len(self.expert_predictions)
        avg_prediction_time = sum(p['timing'] for p in self.expert_predictions) / max(total_predictions, 1)
        
        # Error analysis
        total_errors = len(self.errors)
        error_types = {}
        for error in self.errors:
            error_type = error['type']
            error_types[error_type] = error_types.get(error_type, 0) + 1
            
        return {
            'overall_performance': {
                'total_runtime': total_time,
                'total_operations': len(self.timings),
                'success_rate': (total_predictions - total_errors) / max(total_predictions, 1)
            },
            'database_performance': {
                'total_queries': db_queries,
                'successful_queries': successful_queries,
                'query_success_rate': successful_queries / max(db_queries, 1),
                'avg_query_time': avg_query_time,
                'query_details': self.database_queries
            },
            'expert_performance': {
                'total_predictions': total_predictions,
                'avg_prediction_time': avg_prediction_time,
                'prediction_details': self.expert_predictions
            },
            'error_analysis': {
                'total_errors': total_errors,
                'error_types': error_types,
                'error_details': self.errors
            },
            'timing_breakdown': self.timings
        }


async def detailed_expert_analysis():
    """Run comprehensive expert analysis with detailed tracking"""
    
    tracker = DetailedAnalysisTracker()
    
    print("🔬 DETAILED EXPERT ANALYSIS - ConservativeAnalyzer")
    print("="*80)
    print(f"🕐 Analysis started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🎯 Target: ConservativeAnalyzer expert deep dive")
    print(f"📊 Focus: Infrastructure validation & performance bottlenecks")
    
    try:
        # === PHASE 1: INFRASTRUCTURE SETUP ===
        print(f"\n📋 PHASE 1: INFRASTRUCTURE SETUP")
        print("-" * 50)
        
        setup_start = time.time()
        
        # Database connection with timing
        db_start = time.time()
        try:
            from supabase import create_client
            
            supabase_url = os.getenv('VITE_SUPABASE_URL')
            supabase_key = os.getenv('VITE_SUPABASE_ANON_KEY')
            
            if not supabase_url or not supabase_key:
                raise ValueError("Missing Supabase credentials")
                
            supabase = create_client(supabase_url, supabase_key)
            
            # Test connection
            test_result = supabase.table('nfl_games').select('count').limit(1).execute()
            
            db_time = time.time() - db_start
            tracker.log_timing("database_connection", db_time, {
                'url': supabase_url[:30] + "...",
                'test_query_success': bool(test_result.data)
            })
            tracker.log_database_query("connection_test", db_time, True, {'result_count': len(test_result.data or [])})
            
            print(f"✅ Database connected: {db_time:.3f}s")
            
        except Exception as e:
            tracker.log_error("database_connection", str(e))
            raise
        
        # Service initialization with timing
        services_start = time.time()
        try:
            from services.historical_data_service import HistoricalDataService
            from services.universal_game_data_builder import UniversalGameDataBuilder
            from services.backtest_runner import BacktestRunner, LearningMode
            
            historical_service = HistoricalDataService(supabase)
            universal_builder = UniversalGameDataBuilder(historical_service)
            backtest_runner = BacktestRunner(historical_service, universal_builder)
            
            services_time = time.time() - services_start
            tracker.log_timing("services_initialization", services_time)
            print(f"✅ Services initialized: {services_time:.3f}s")
            
        except Exception as e:
            tracker.log_error("services_initialization", str(e))
            raise
        
        # Expert initialization with timing
        expert_start = time.time()
        try:
            from ml.personality_driven_experts import ConservativeAnalyzer
            
            # Initialize with potential memory service
            try:
                from ml.supabase_memory_services import SupabaseEpisodicMemoryManager
                memory_service = SupabaseEpisodicMemoryManager(supabase)
                expert = ConservativeAnalyzer(memory_service=memory_service)
                memory_enabled = True
                print(f"✅ Memory service enabled")
            except Exception as e:
                expert = ConservativeAnalyzer()
                memory_enabled = False
                print(f"⚠️  Memory service disabled: {e}")
            
            expert_time = time.time() - expert_start
            tracker.log_timing("expert_initialization", expert_time, {
                'memory_enabled': memory_enabled,
                'expert_id': expert.expert_id,
                'expert_name': expert.name
            })
            
            print(f"✅ Expert initialized: {expert.name}")
            print(f"   → ID: {expert.expert_id}")
            print(f"   → Personality: {expert.personality.decision_style}")
            print(f"   → Memory: {'Enabled' if memory_enabled else 'Disabled'}")
            
        except Exception as e:
            tracker.log_error("expert_initialization", str(e))
            raise
        
        setup_time = time.time() - setup_start
        tracker.log_timing("total_setup", setup_time)
        
        # === PHASE 2: SINGLE GAME ANALYSIS ===
        print(f"\n🏈 PHASE 2: SINGLE GAME DEEP DIVE")
        print("-" * 50)
        
        # Test game: Week 5, 2020 KC vs LV (known game with good data)
        game_start = time.time()
        season, week, home_team, away_team = 2020, 5, 'KC', 'LV'
        
        print(f"🎯 Analyzing: {away_team} @ {home_team}, {season} Week {week}")
        
        # Build UniversalGameData with detailed tracking
        context_start = time.time()
        try:
            universal_data = universal_builder.build_universal_game_data(
                season=season,
                week=week,
                home_team=home_team,
                away_team=away_team,
                include_current_week_stats=False
            )
            
            context_time = time.time() - context_start
            tracker.log_timing("universal_data_build", context_time)
            
            # Analyze the context data
            context_analysis = {
                'home_team': universal_data.home_team,
                'away_team': universal_data.away_team,
                'weather_available': bool(universal_data.weather),
                'weather_temp': universal_data.weather.get('temperature'),
                'weather_wind': universal_data.weather.get('wind_speed'),
                'team_stats_available': bool(universal_data.team_stats),
                'line_movement_available': bool(universal_data.line_movement),
                'public_betting_available': bool(universal_data.public_betting),
                'head_to_head_available': bool(universal_data.head_to_head),
                'recent_news_available': bool(universal_data.recent_news),
                'coaching_info_available': bool(universal_data.coaching_info)
            }
            
            tracker.game_context_data.append(context_analysis)
            
            print(f"✅ UniversalGameData built: {context_time:.3f}s")
            print(f"   → Weather: {universal_data.weather}")
            print(f"   → Team Stats Available: {bool(universal_data.team_stats)}")
            print(f"   → Line Movement: {universal_data.line_movement}")
            print(f"   → Head-to-Head Games: {len(universal_data.head_to_head)}")
            
        except Exception as e:
            tracker.log_error("universal_data_build", str(e))
            raise
        
        # Expert prediction with detailed tracking
        pred_start = time.time()
        try:
            prediction = expert.make_personality_driven_prediction(universal_data)
            pred_time = time.time() - pred_start
            
            game_info = {
                'season': season,
                'week': week,
                'home_team': home_team,
                'away_team': away_team
            }
            
            tracker.log_expert_prediction(game_info, prediction, pred_time, context_analysis)
            
            print(f"✅ Expert prediction made: {pred_time:.3f}s")
            print(f"   → Winner: {prediction.get('winner_prediction', 'N/A')}")
            print(f"   → Confidence: {prediction.get('winner_confidence', 0):.1%}")
            print(f"   → Reasoning: {len(prediction.get('reasoning', []))} factors")
            
            # Deep dive into prediction reasoning
            if 'reasoning' in prediction:
                print(f"   → Key reasoning factors:")
                for i, reason in enumerate(prediction['reasoning'][:3], 1):
                    print(f"     {i}. {reason}")
            
        except Exception as e:
            tracker.log_error("expert_prediction", str(e))
            raise
        
        # === PHASE 3: MINI BACKTEST ===
        print(f"\n🔄 PHASE 3: MINI BACKTEST (Week 1, 2020)")
        print("-" * 50)
        
        backtest_start = time.time()
        try:
            # Run just Week 1 for detailed analysis
            mini_results = await backtest_runner.run_season_backtest(
                expert=expert,
                season=2020,
                learning_mode=LearningMode.BASELINE,
                start_week=1,
                end_week=1,
                game_filter=None
            )
            
            backtest_time = time.time() - backtest_start
            tracker.log_timing("mini_backtest", backtest_time, {
                'total_games': mini_results.total_games,
                'overall_accuracy': mini_results.overall_accuracy,
                'correct_winners': mini_results.correct_winners
            })
            
            print(f"✅ Mini-backtest completed: {backtest_time:.3f}s")
            print(f"   → Total games processed: {mini_results.total_games}")
            print(f"   → Overall accuracy: {mini_results.overall_accuracy:.1%}")
            print(f"   → Correct winner predictions: {mini_results.correct_winners}/{mini_results.total_games}")
            print(f"   → Average time per game: {backtest_time/max(mini_results.total_games, 1):.3f}s")
            
            # Analyze individual game performance
            if mini_results.predictions:
                print(f"   → Individual game analysis:")
                for i, pred_record in enumerate(mini_results.predictions[:5], 1):
                    status = "✅" if pred_record.correct_winner else "❌"
                    print(f"     {i}. {pred_record.away_team}@{pred_record.home_team}: {status} "
                          f"({pred_record.prediction.get('winner_prediction', 'N/A')} "
                          f"vs actual {pred_record.actual_winner})")
            
        except Exception as e:
            tracker.log_error("mini_backtest", str(e))
            raise
        
        # === PHASE 4: PERFORMANCE ANALYSIS ===
        print(f"\n📊 PHASE 4: PERFORMANCE & BOTTLENECK ANALYSIS")
        print("-" * 50)
        
        total_time = time.time() - tracker.start_time
        
        # Generate comprehensive report
        report = tracker.generate_comprehensive_report()
        
        # Display key performance metrics
        print(f"⏱️  TIMING BREAKDOWN:")
        for operation, data in tracker.timings.items():
            print(f"   → {operation}: {data['duration']:.3f}s")
        
        print(f"\n🔍 DATABASE PERFORMANCE:")
        print(f"   → Total queries: {report['database_performance']['total_queries']}")
        print(f"   → Success rate: {report['database_performance']['query_success_rate']:.1%}")
        print(f"   → Average query time: {report['database_performance']['avg_query_time']:.3f}s")
        
        print(f"\n🤖 EXPERT PERFORMANCE:")
        print(f"   → Total predictions: {report['expert_performance']['total_predictions']}")
        print(f"   → Average prediction time: {report['expert_performance']['avg_prediction_time']:.3f}s")
        
        print(f"\n🚨 ERROR ANALYSIS:")
        print(f"   → Total errors: {report['error_analysis']['total_errors']}")
        if report['error_analysis']['error_types']:
            for error_type, count in report['error_analysis']['error_types'].items():
                print(f"   → {error_type}: {count}")
        else:
            print(f"   → No errors detected ✅")
        
        # === PHASE 5: BOTTLENECK IDENTIFICATION ===
        print(f"\n🎯 PHASE 5: BOTTLENECK IDENTIFICATION")
        print("-" * 50)
        
        bottlenecks = []
        
        # Identify slow operations
        for operation, data in tracker.timings.items():
            duration = data['duration']
            if duration > 1.0:
                bottlenecks.append((operation, duration, "Slow operation (>1s)"))
            elif 'database' in operation.lower() and duration > 0.5:
                bottlenecks.append((operation, duration, "Slow database operation (>0.5s)"))
        
        # Check database query performance
        slow_queries = [q for q in tracker.database_queries if q['duration'] > 0.1]
        if slow_queries:
            bottlenecks.append(("database_queries", len(slow_queries), f"{len(slow_queries)} slow queries (>0.1s)"))
        
        if bottlenecks:
            print("🚨 PERFORMANCE BOTTLENECKS IDENTIFIED:")
            for i, (component, metric, description) in enumerate(bottlenecks, 1):
                print(f"   {i}. {component}: {metric} - {description}")
        else:
            print("✅ No significant bottlenecks identified")
        
        # === PHASE 6: SAVE DETAILED REPORT ===
        print(f"\n💾 PHASE 6: SAVING DETAILED REPORT")
        print("-" * 50)
        
        # Save comprehensive report to file
        report_filename = f"detailed_analysis_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        report_path = f"/home/iris/code/experimental/nfl-predictor-api/{report_filename}"
        
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        print(f"✅ Detailed report saved: {report_filename}")
        print(f"   → Location: {report_path}")
        print(f"   → Size: {os.path.getsize(report_path) / 1024:.1f} KB")
        
        # === FINAL SUMMARY ===
        print(f"\n🎉 ANALYSIS COMPLETE - FINAL SUMMARY")
        print("="*80)
        print(f"⏱️  Total analysis time: {total_time:.3f}s")
        print(f"🔧 Infrastructure status: {'✅ WORKING' if report['error_analysis']['total_errors'] == 0 else '⚠️  ISSUES DETECTED'}")
        print(f"📊 Expert functionality: {'✅ FUNCTIONAL' if report['expert_performance']['total_predictions'] > 0 else '❌ FAILED'}")
        print(f"🗄️  Database performance: {'✅ GOOD' if report['database_performance']['avg_query_time'] < 0.5 else '⚠️  SLOW'}")
        print(f"🚀 Ready for full backtesting: {'YES' if len(bottlenecks) < 3 else 'OPTIMIZE FIRST'}")
        
        return report
        
    except Exception as e:
        tracker.log_error("overall_analysis", str(e))
        print(f"❌ Analysis failed: {e}")
        import traceback
        traceback.print_exc()
        return None


async def main():
    """Main analysis execution"""
    print("🚀 Starting Detailed Expert Analysis")
    
    # Source environment
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass
    
    report = await detailed_expert_analysis()
    
    if report:
        print(f"\n🎊 Analysis completed successfully!")
        print(f"📋 Check detailed_analysis.log for comprehensive logs")
        print(f"📊 Review the JSON report for complete metrics")
        return True
    else:
        print(f"\n💥 Analysis failed!")
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)