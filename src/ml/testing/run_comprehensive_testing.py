"""
Comprehensive System Testing Integration Script
Main entry point for executing the comprehensive testing framework
according to the design document specifications.
"""

import asyncio
import argparse
import logging
from datetime import datetime
from pathlib import Path
import sys
import os

# Add the src directory to the path so we can import our modules
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from .test_suite_orchestrator import TestSuiteOrchestrator, TestSuiteConfiguration
from .automated_monitoring import setup_monitoring_system
from .comprehensive_system_testing import ComprehensiveSystemTester

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('comprehensive_testing.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

async def main():
    """Main execution function"""
    
    parser = argparse.ArgumentParser(description='NFL Predictor Comprehensive System Testing')
    parser.add_argument('--mode', choices=['full', 'performance', 'council', 'data', 'learning', 'monitoring'], 
                       default='full', help='Testing mode to run')
    parser.add_argument('--output-dir', default='test_reports', help='Output directory for reports')
    parser.add_argument('--config-file', help='Configuration file path')
    parser.add_argument('--supabase-url', help='Supabase URL')
    parser.add_argument('--supabase-key', help='Supabase API key')
    parser.add_argument('--generate-html', action='store_true', default=True, help='Generate HTML report')
    parser.add_argument('--generate-json', action='store_true', default=True, help='Generate JSON report')
    parser.add_argument('--start-monitoring', action='store_true', help='Start continuous monitoring')
    
    args = parser.parse_args()
    
    logger.info("=== NFL Predictor Comprehensive System Testing ===")
    logger.info(f"Mode: {args.mode}")
    logger.info(f"Output Directory: {args.output_dir}")
    logger.info(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        # Initialize Supabase client if credentials provided
        supabase_client = None
        if args.supabase_url and args.supabase_key:
            try:
                from supabase import create_client
                supabase_client = create_client(args.supabase_url, args.supabase_key)
                logger.info("Supabase client initialized")
            except ImportError:
                logger.warning("Supabase client not available - continuing without database integration")
        
        # Setup configuration
        config = TestSuiteConfiguration(
            include_performance_tests=args.mode in ['full', 'performance'],
            include_council_tests=args.mode in ['full', 'council'],
            include_data_quality_tests=args.mode in ['full', 'data'],
            include_learning_tests=args.mode in ['full', 'learning'],
            include_gap_analysis=args.mode in ['full'],
            generate_html_report=args.generate_html,
            generate_json_report=args.generate_json,
            output_directory=args.output_dir
        )
        
        # Create output directory
        Path(args.output_dir).mkdir(exist_ok=True)
        
        # Initialize orchestrator
        orchestrator = TestSuiteOrchestrator(supabase_client)
        
        if args.mode == 'monitoring' or args.start_monitoring:
            # Start monitoring system
            logger.info("Setting up monitoring system...")
            monitor = await setup_monitoring_system()
            
            logger.info("Monitoring system started. Press Ctrl+C to stop.")
            try:
                while True:
                    await asyncio.sleep(60)
                    health_status = monitor.get_current_health_status()
                    logger.info(f"System Health: {health_status['status']} (Score: {health_status['health_score']:.3f})")
            except KeyboardInterrupt:
                logger.info("Stopping monitoring system...")
                await monitor.stop_monitoring()
        
        else:
            # Run comprehensive testing
            logger.info("Starting comprehensive test suite execution...")
            
            # Mock data for demonstration - in production, this would come from actual systems
            mock_experts = {
                'weather_wizard': type('MockExpert', (), {
                    'expert_id': 'weather_wizard', 
                    'personality': 'Weather Specialist',
                    'specializations': ['weather_impact', 'outdoor_games']
                }),
                'sharp_bettor': type('MockExpert', (), {
                    'expert_id': 'sharp_bettor', 
                    'personality': 'Market Analyst',
                    'specializations': ['line_movement', 'market_analysis']
                }),
                'analytics_guru': type('MockExpert', (), {
                    'expert_id': 'analytics_guru', 
                    'personality': 'Statistics Expert',
                    'specializations': ['advanced_metrics', 'efficiency_stats']
                }),
                'injury_analyst': type('MockExpert', (), {
                    'expert_id': 'injury_analyst', 
                    'personality': 'Medical Specialist',
                    'specializations': ['injury_impact', 'player_availability']
                }),
                'road_warrior': type('MockExpert', (), {
                    'expert_id': 'road_warrior', 
                    'personality': 'Travel Impact Expert',
                    'specializations': ['away_team_performance', 'travel_impact']
                })
            }
            
            mock_historical_data = {
                'predictions': {expert_id: [] for expert_id in mock_experts.keys()},
                'results': [],
                'espn_data': [
                    {'game_id': f'game_{i}', 'home_team': f'Team_{i}', 'timestamp': datetime.now().isoformat()}
                    for i in range(10)
                ],
                'sportsdata': [],
                'betting_data': [
                    {'game_id': f'game_{i}', 'spread': -3.5, 'timestamp': datetime.now().isoformat()}
                    for i in range(10)
                ],
                'weather_data': [],
                'news_data': []
            }
            
            mock_system_metrics = {
                'frontend': {
                    'render_time': 0.08,
                    'interaction_latency': 0.03,
                    'bundle_size': 1500,
                    'error_rate': 0.005
                },
                'backend': {
                    'api_response_time': 0.15,
                    'throughput': 800,
                    'error_rate': 0.008,
                    'availability': 0.998
                },
                'ai': {
                    'prediction_generation_time': 0.04,
                    'overall_accuracy': 0.68,
                    'model_latency': 0.03,
                    'memory_usage': 600
                }
            }
            
            # Execute comprehensive test suite
            report = await orchestrator.execute_comprehensive_test_suite(
                config, mock_experts, mock_historical_data, mock_system_metrics
            )
            
            # Print summary
            logger.info("=== Test Execution Summary ===")
            logger.info(f"Report ID: {report.report_id}")
            logger.info(f"Total Tests: {report.total_tests}")
            logger.info(f"Passed Tests: {report.total_passed}")
            logger.info(f"Failed Tests: {report.total_failed}")
            logger.info(f"Overall Success Rate: {report.overall_success_rate:.1%}")
            logger.info(f"Expert Performance Score: {report.expert_performance_score:.3f}")
            logger.info(f"Data Quality Score: {report.data_quality_score:.3f}")
            logger.info(f"System Integration Score: {report.system_integration_score:.3f}")
            
            if report.html_report_path:
                logger.info(f"HTML Report: {report.html_report_path}")
            if report.json_report_path:
                logger.info(f"JSON Report: {report.json_report_path}")
            
            # Print recommendations
            if report.recommendations:
                logger.info("=== Recommendations ===")
                for i, rec in enumerate(report.recommendations, 1):
                    logger.info(f"{i}. {rec}")
            
            # Print identified issues
            if report.identified_issues:
                logger.warning("=== Identified Issues ===")
                for i, issue in enumerate(report.identified_issues, 1):
                    logger.warning(f"{i}. {issue}")
            
            # Determine exit code based on results
            if report.overall_success_rate >= 0.8:
                logger.info("✅ Testing completed successfully")
                exit_code = 0
            elif report.overall_success_rate >= 0.6:
                logger.warning("⚠️  Testing completed with warnings")
                exit_code = 1
            else:
                logger.error("❌ Testing completed with critical issues")
                exit_code = 2
            
            return exit_code
    
    except Exception as e:
        logger.error(f"Testing execution failed: {e}")
        import traceback
        traceback.print_exc()
        return 3

def run_quick_test():
    """Quick test function for development/debugging"""
    async def quick_test():
        logger.info("Running quick comprehensive test...")
        
        orchestrator = TestSuiteOrchestrator()
        config = TestSuiteConfiguration(output_directory="quick_test_reports")
        
        # Minimal mock data
        experts = {'test_expert': type('MockExpert', (), {'expert_id': 'test_expert'})}
        historical_data = {'predictions': {}, 'results': []}
        system_metrics = {'frontend': {}, 'backend': {}, 'ai': {}}
        
        report = await orchestrator.execute_comprehensive_test_suite(
            config, experts, historical_data, system_metrics
        )
        
        print(f"Quick test completed: {report.overall_success_rate:.1%} success rate")
        return report
    
    return asyncio.run(quick_test())

if __name__ == "__main__":
    # Check if running in quick test mode
    if len(sys.argv) > 1 and sys.argv[1] == "--quick-test":
        run_quick_test()
    else:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)