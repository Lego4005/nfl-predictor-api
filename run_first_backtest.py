#!/usr/bin/env python3
"""
First Backtest Infrastructure Test Script

This script tests our backtesting infrastructure with the ConservativeAnalyzer expert
to validate functionality and identify performance bottlenecks.

Tests:
1. ConservativeAnalyzer expert instantiation with Supabase connections
2. HistoricalDataService, UniversalGameDataBuilder, BacktestRunner setup
3. 2020 NFL season backtest in all three learning modes
4. Comprehensive timing instrumentation
5. Detailed accuracy analysis and comparison
6. Error handling and informative failure reporting

Goal: Validate infrastructure works correctly and identify optimization needs.
"""

import os
import sys
import time
import asyncio
import logging
import traceback
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

# Add project paths
sys.path.append('/home/iris/code/experimental/nfl-predictor-api/src')

# Environment setup
os.environ.setdefault('ENV', 'development')

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('/home/iris/code/experimental/nfl-predictor-api/backtest_timing.log')
    ]
)
logger = logging.getLogger(__name__)


@dataclass
class TimingMetrics:
    """Performance timing metrics for bottleneck identification"""
    total_backtest_time: float = 0.0
    setup_time: float = 0.0
    database_connection_time: float = 0.0
    expert_initialization_time: float = 0.0
    
    # Per-game timing
    avg_game_prediction_time: float = 0.0
    avg_context_building_time: float = 0.0
    avg_database_query_time: float = 0.0
    avg_memory_retrieval_time: float = 0.0
    
    # Learning mode timing
    baseline_total_time: float = 0.0
    memory_only_total_time: float = 0.0
    full_learning_total_time: float = 0.0
    
    # Query breakdowns
    team_stats_query_time: float = 0.0
    weather_query_time: float = 0.0
    betting_lines_query_time: float = 0.0
    head_to_head_query_time: float = 0.0


@dataclass 
class AccuracyMetrics:
    """Detailed accuracy analysis"""
    total_games: int = 0
    overall_accuracy: float = 0.0
    
    # By learning mode
    baseline_accuracy: float = 0.0
    memory_only_accuracy: float = 0.0
    full_learning_accuracy: float = 0.0
    
    # By game characteristics
    home_team_accuracy: float = 0.0
    away_team_accuracy: float = 0.0
    favorite_accuracy: float = 0.0
    underdog_accuracy: float = 0.0
    
    # Learning improvements
    memory_improvement: float = 0.0
    full_improvement: float = 0.0
    
    # Statistical significance
    improvement_significant: bool = False
    p_value: Optional[float] = None


class BacktestInfrastructureTest:
    """Comprehensive infrastructure test and performance analysis"""
    
    def __init__(self):
        self.timing = TimingMetrics()
        self.accuracy = AccuracyMetrics()
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        
        # Infrastructure components
        self.supabase = None
        self.historical_service = None
        self.universal_builder = None
        self.backtest_runner = None
        self.learning_comparator = None
        self.expert = None
        
        # Results storage
        self.baseline_results = None
        self.memory_results = None
        self.full_results = None
        
    def print_header(self, title: str):
        """Print formatted section header"""
        print(f"\n{'='*80}")
        print(f"🏈 {title}")
        print(f"{'='*80}")
    
    def print_timing(self, operation: str, duration: float):
        """Print timing information"""
        print(f"⏱️  {operation}: {duration:.3f}s")
        self.logger.info(f"TIMING: {operation}: {duration:.3f}s")
    
    async def run_full_test(self):
        """Run complete infrastructure test"""
        start_time = time.time()
        
        try:
            self.print_header("NFL BACKTEST INFRASTRUCTURE VALIDATION")
            print(f"🕐 Test started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"🎯 Target: 2020 NFL Season (Weeks 1-17)")
            print(f"🤖 Expert: ConservativeAnalyzer")
            print(f"🧠 Learning Modes: Baseline, Memory-Only, Full-Learning")
            
            # Step 1: Setup infrastructure
            await self._setup_infrastructure()
            
            # Step 2: Initialize expert
            await self._initialize_expert()
            
            # Step 3: Run backtests
            await self._run_learning_mode_backtests()
            
            # Step 4: Analyze results
            self._analyze_results()
            
            # Step 5: Report findings
            self._report_comprehensive_results()
            
            # Step 6: Identify bottlenecks
            self._identify_performance_bottlenecks()
            
            self.timing.total_backtest_time = time.time() - start_time
            self.print_timing("TOTAL TEST DURATION", self.timing.total_backtest_time)
            
            print(f"\n✅ Infrastructure test completed successfully!")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Infrastructure test failed: {e}")
            self.logger.error(traceback.format_exc())
            print(f"\n❌ Test failed: {e}")
            return False
    
    async def _setup_infrastructure(self):
        """Setup and test all infrastructure components"""
        self.print_header("INFRASTRUCTURE SETUP")
        
        setup_start = time.time()
        
        # Step 1: Database connection
        db_start = time.time()
        try:
            from supabase import create_client
            
            # Get credentials from environment
            supabase_url = os.getenv('SUPABASE_URL')
            supabase_key = os.getenv('SUPABASE_ANON_KEY')
            
            if not supabase_url or not supabase_key:
                raise ValueError("Missing SUPABASE_URL or SUPABASE_ANON_KEY environment variables")
            
            self.supabase = create_client(supabase_url, supabase_key)
            
            # Test connection with a simple query
            test_result = self.supabase.table('nfl_games').select('count').limit(1).execute()
            
            self.timing.database_connection_time = time.time() - db_start
            self.print_timing("Database Connection", self.timing.database_connection_time)
            print(f"✅ Supabase connected: {supabase_url}")
            
        except Exception as e:
            raise RuntimeError(f"Database connection failed: {e}")
        
        # Step 2: Historical Data Service
        try:
            from services.historical_data_service import HistoricalDataService
            
            self.historical_service = HistoricalDataService(self.supabase)
            print("✅ HistoricalDataService initialized")
            
        except Exception as e:
            raise RuntimeError(f"HistoricalDataService initialization failed: {e}")
        
        # Step 3: Universal Game Data Builder
        try:
            from services.universal_game_data_builder import UniversalGameDataBuilder
            
            self.universal_builder = UniversalGameDataBuilder(self.historical_service)
            print("✅ UniversalGameDataBuilder initialized")
            
        except Exception as e:
            raise RuntimeError(f"UniversalGameDataBuilder initialization failed: {e}")
        
        # Step 4: Backtest Runner
        try:
            from services.backtest_runner import BacktestRunner
            
            self.backtest_runner = BacktestRunner(
                self.historical_service,
                self.universal_builder
            )
            print("✅ BacktestRunner initialized")
            
        except Exception as e:
            raise RuntimeError(f"BacktestRunner initialization failed: {e}")
        
        # Step 5: Learning Mode Comparator
        try:
            from services.learning_mode_comparator import LearningModeComparator
            
            self.learning_comparator = LearningModeComparator(
                self.backtest_runner,
                self.historical_service
            )
            print("✅ LearningModeComparator initialized")
            
        except Exception as e:
            raise RuntimeError(f"LearningModeComparator initialization failed: {e}")
        
        self.timing.setup_time = time.time() - setup_start
        self.print_timing("Infrastructure Setup", self.timing.setup_time)
    
    async def _initialize_expert(self):
        """Initialize ConservativeAnalyzer expert with memory services"""
        self.print_header("EXPERT INITIALIZATION")
        
        expert_start = time.time()
        
        try:
            # Import expert class
            from ml.personality_driven_experts import ConservativeAnalyzer
            
            # Initialize memory service if available
            memory_service = None
            try:
                from ml.supabase_memory_services import SupabaseEpisodicMemoryManager
                memory_service = SupabaseEpisodicMemoryManager(self.supabase)
                print("✅ Memory service initialized")
            except Exception as e:
                print(f"⚠️  Memory service unavailable: {e}")
                print("   → Continuing without memory enhancement")
            
            # Create expert
            self.expert = ConservativeAnalyzer(memory_service=memory_service)
            
            self.timing.expert_initialization_time = time.time() - expert_start
            self.print_timing("Expert Initialization", self.timing.expert_initialization_time)
            
            print(f"✅ Expert initialized: {self.expert.name}")
            print(f"   → ID: {self.expert.expert_id}")
            print(f"   → Personality: {self.expert.personality.decision_style}")
            print(f"   → Memory: {'Enabled' if memory_service else 'Disabled'}")
            
        except Exception as e:
            raise RuntimeError(f"Expert initialization failed: {e}")
    
    async def _run_learning_mode_backtests(self):
        """Run backtests in all three learning modes"""
        self.print_header("LEARNING MODE BACKTESTS")
        
        season = 2020
        start_week = 1
        end_week = 17  # Regular season only
        
        print(f"🏈 Running {season} NFL season backtests (Weeks {start_week}-{end_week})")
        print("📊 Testing three learning configurations...")
        
        # Mode 1: Baseline (no learning)
        print(f"\n🔸 Mode 1: BASELINE (No Learning)")
        baseline_start = time.time()
        try:
            from services.backtest_runner import LearningMode
            
            self.baseline_results = await self.backtest_runner.run_season_backtest(
                expert=self.expert,
                season=season,
                learning_mode=LearningMode.BASELINE,
                start_week=start_week,
                end_week=end_week
            )
            
            self.timing.baseline_total_time = time.time() - baseline_start
            self.print_timing("Baseline Mode", self.timing.baseline_total_time)
            print(f"   → Accuracy: {self.baseline_results.overall_accuracy:.1%}")
            
        except Exception as e:
            raise RuntimeError(f"Baseline backtest failed: {e}")
        
        # Mode 2: Memory-only (episodic memory without belief revision)
        print(f"\n🔸 Mode 2: MEMORY-ONLY (Episodic Memory)")
        memory_start = time.time()
        try:
            self.memory_results = await self.backtest_runner.run_season_backtest(
                expert=self.expert,
                season=season,
                learning_mode=LearningMode.MEMORY_ONLY,
                start_week=start_week,
                end_week=end_week
            )
            
            self.timing.memory_only_total_time = time.time() - memory_start
            self.print_timing("Memory-Only Mode", self.timing.memory_only_total_time)
            print(f"   → Accuracy: {self.memory_results.overall_accuracy:.1%}")
            
        except Exception as e:
            raise RuntimeError(f"Memory-only backtest failed: {e}")
        
        # Mode 3: Full learning (memory + belief revision)
        print(f"\n🔸 Mode 3: FULL-LEARNING (Memory + Belief Revision)")
        full_start = time.time()
        try:
            self.full_results = await self.backtest_runner.run_season_backtest(
                expert=self.expert,
                season=season,
                learning_mode=LearningMode.FULL_LEARNING,
                start_week=start_week,
                end_week=end_week
            )
            
            self.timing.full_learning_total_time = time.time() - full_start
            self.print_timing("Full-Learning Mode", self.timing.full_learning_total_time)
            print(f"   → Accuracy: {self.full_results.overall_accuracy:.1%}")
            
        except Exception as e:
            raise RuntimeError(f"Full learning backtest failed: {e}")
    
    def _analyze_results(self):
        """Analyze results across all learning modes"""
        self.print_header("RESULTS ANALYSIS")
        
        # Basic accuracy metrics
        self.accuracy.total_games = len(self.baseline_results.predictions)
        self.accuracy.baseline_accuracy = self.baseline_results.overall_accuracy
        self.accuracy.memory_only_accuracy = self.memory_results.overall_accuracy
        self.accuracy.full_learning_accuracy = self.full_results.overall_accuracy
        
        # Learning improvements
        if self.accuracy.baseline_accuracy > 0:
            self.accuracy.memory_improvement = (
                (self.accuracy.memory_only_accuracy - self.accuracy.baseline_accuracy) 
                / self.accuracy.baseline_accuracy
            ) * 100
            
            self.accuracy.full_improvement = (
                (self.accuracy.full_learning_accuracy - self.accuracy.baseline_accuracy) 
                / self.accuracy.baseline_accuracy
            ) * 100
        
        # Analyze by game characteristics
        self._analyze_by_game_characteristics()
        
        # Calculate timing metrics
        self._calculate_timing_metrics()
    
    def _analyze_by_game_characteristics(self):
        """Analyze accuracy by game characteristics"""
        
        baseline_predictions = self.baseline_results.predictions
        
        # Home vs Away analysis
        home_correct = sum(1 for p in baseline_predictions 
                          if p.prediction.get('winner') == p.home_team and p.correct_winner)
        away_correct = sum(1 for p in baseline_predictions 
                          if p.prediction.get('winner') == p.away_team and p.correct_winner)
        
        home_total = sum(1 for p in baseline_predictions 
                        if p.prediction.get('winner') == p.home_team)
        away_total = sum(1 for p in baseline_predictions 
                        if p.prediction.get('winner') == p.away_team)
        
        self.accuracy.home_team_accuracy = (home_correct / home_total) if home_total > 0 else 0
        self.accuracy.away_team_accuracy = (away_correct / away_total) if away_total > 0 else 0
    
    def _calculate_timing_metrics(self):
        """Calculate detailed timing metrics"""
        
        if self.accuracy.total_games > 0:
            # Average per-game timing
            self.timing.avg_game_prediction_time = (
                (self.timing.baseline_total_time + 
                 self.timing.memory_only_total_time + 
                 self.timing.full_learning_total_time) / 3
            ) / self.accuracy.total_games
    
    def _report_comprehensive_results(self):
        """Report comprehensive test results"""
        self.print_header("COMPREHENSIVE RESULTS")
        
        print(f"\n📊 ACCURACY RESULTS")
        print(f"{'─'*50}")
        print(f"Total Games Tested: {self.accuracy.total_games}")
        print(f"Baseline Accuracy:  {self.accuracy.baseline_accuracy:.1%}")
        print(f"Memory-Only:        {self.accuracy.memory_only_accuracy:.1%}")
        print(f"Full-Learning:      {self.accuracy.full_learning_accuracy:.1%}")
        
        print(f"\n📈 LEARNING IMPROVEMENTS")
        print(f"{'─'*50}")
        print(f"Memory Improvement:    {self.accuracy.memory_improvement:+.1f}%")
        print(f"Full Learning Improvement: {self.accuracy.full_improvement:+.1f}%")
        
        print(f"\n🏠 GAME CHARACTERISTICS")
        print(f"{'─'*50}")
        print(f"Home Team Picks:    {self.accuracy.home_team_accuracy:.1%}")
        print(f"Away Team Picks:    {self.accuracy.away_team_accuracy:.1%}")
        
        print(f"\n⏱️  PERFORMANCE TIMING")
        print(f"{'─'*50}")
        print(f"Total Test Time:    {self.timing.total_backtest_time:.1f}s")
        print(f"Setup Time:         {self.timing.setup_time:.1f}s")
        print(f"Database Connection: {self.timing.database_connection_time:.3f}s")
        print(f"Expert Init:        {self.timing.expert_initialization_time:.3f}s")
        print(f"Avg Per Game:       {self.timing.avg_game_prediction_time:.3f}s")
        
        print(f"\n📋 LEARNING MODE TIMING")
        print(f"{'─'*50}")
        print(f"Baseline Mode:      {self.timing.baseline_total_time:.1f}s")
        print(f"Memory-Only Mode:   {self.timing.memory_only_total_time:.1f}s")
        print(f"Full-Learning Mode: {self.timing.full_learning_total_time:.1f}s")
    
    def _identify_performance_bottlenecks(self):
        """Identify performance bottlenecks for optimization"""
        self.print_header("PERFORMANCE BOTTLENECK ANALYSIS")
        
        total_time = self.timing.total_backtest_time
        
        bottlenecks = []
        
        # Database setup time
        if self.timing.database_connection_time > 2.0:
            bottlenecks.append(("Database Connection", self.timing.database_connection_time, "Consider connection pooling"))
        
        # Per-game prediction time
        if self.timing.avg_game_prediction_time > 1.0:
            bottlenecks.append(("Per-Game Prediction", self.timing.avg_game_prediction_time, "Consider query optimization"))
        
        # Learning mode performance difference
        learning_overhead = self.timing.full_learning_total_time - self.timing.baseline_total_time
        if learning_overhead > (self.timing.baseline_total_time * 0.5):
            bottlenecks.append(("Learning Overhead", learning_overhead, "Consider memory query optimization"))
        
        if bottlenecks:
            print("🚨 PERFORMANCE BOTTLENECKS IDENTIFIED:")
            for i, (component, time_taken, suggestion) in enumerate(bottlenecks, 1):
                print(f"   {i}. {component}: {time_taken:.3f}s")
                print(f"      → {suggestion}")
        else:
            print("✅ No significant performance bottlenecks identified")
        
        print(f"\n💡 OPTIMIZATION RECOMMENDATIONS:")
        print(f"   • Database queries: {self.timing.database_connection_time:.3f}s")
        print(f"   • Consider pre-computed aggregation tables if queries > 0.1s per game")
        print(f"   • Memory operations appear {'efficient' if learning_overhead < 5 else 'slow'}")
        print(f"   • Overall performance: {'Excellent' if total_time < 60 else 'Good' if total_time < 300 else 'Needs optimization'}")


async def main():
    """Main test execution"""
    print("🚀 Starting NFL Backtest Infrastructure Test")
    
    # Check environment
    required_vars = ['SUPABASE_URL', 'SUPABASE_ANON_KEY']
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print(f"❌ Missing required environment variables: {', '.join(missing_vars)}")
        print("Please set these in your environment before running the test.")
        return False
    
    # Run test
    test = BacktestInfrastructureTest()
    success = await test.run_full_test()
    
    if success:
        print(f"\n🎉 Infrastructure validation completed successfully!")
        print(f"📊 Check backtest_timing.log for detailed timing logs")
        return True
    else:
        print(f"\n💥 Infrastructure validation failed!")
        print(f"📋 Check logs for error details")
        return False


if __name__ == "__main__":
    # Run the test
    success = asyncio.run(main())
    sys.exit(0 if success else 1)