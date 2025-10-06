#!/usr/bin/env python3
"""
Enhanced Historical Processing Runner

This script runs the enhanced historical processor to build expert knowledge
through chronological game processing with full memory capabilities.

Usage:
    python run_enhanced_historical_processing.py --season 2024
    python run_enhanced_historical_processing.py --seasons 2023-2024
    python run_enhanced_historical_processing.py --test
"""

import asyncio
import logging
import os
import sys
import argparse
from datetime import datetime

# Add src to path
sys.path.append('src')

from supabase import create_client
from services.enhanced_historical_processor import EnhancedHistoricalProcessor

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('enhanced_historical_processing.log')
    ]
)
logger = logging.getLogger(__name__)


async def run_single_season(processor: EnhancedHistoricalProcessor, season: int) -> None:
    """Run processing for a single season"""
    logger.info(f"🚀 Starting enhanced processing for {season} season")

    try:
        result = await processor.process_season_chronologically(season)

        logger.info(f"✅ Completed {season} season processing:")
        logger.info(f"   - Games processed: {result.processed_games}/{result.total_games}")
        logger.info(f"   - Processing time: {(datetime.now() - result.start_time).total_seconds() / 60:.1f} minutes")
        logger.info(f"   - Games per minute: {result.games_per_minute:.1f}")
        logger.info(f"   - Errors: {len(result.errors)}")

        if result.errors:
            logger.warning(f"Errors encountered: {result.errors[:5]}")  # Show first 5 errors

        # Get final summary
        summary = await processor.get_processing_summary()
        logger.info(f"📊 Expert Learning Summary:")

        for expert_id, stats in summary['expert_statistics'].items():
            logger.info(f"   {expert_id}: {stats['predictions_made']} predictions, "
                       f"{stats['team_knowledge_records']} team patterns, "
                       f"{stats['vector_memories']} vector memories")

    except Exception as e:
        logger.error(f"❌ Failed to process {season} season: {str(e)}")
        raise


async def run_multiple_seasons(processor: EnhancedHistoricalProcessor,
                              start_season: int, end_season: int) -> None:
    """Run processing for multiple seasons"""
    logger.info(f"🚀 Starting enhanced processing for seasons {start_season}-{end_season}")

    try:
        results = await processor.process_multiple_seasons(start_season, end_season)

        total_games = sum(result.processed_games for result in results.values())
        total_errors = sum(len(result.errors) for result in results.values())

        logger.info(f"✅ Completed multi-season processing:")
        logger.info(f"   - Seasons processed: {len(results)}")
        logger.info(f"   - Total games: {total_games}")
        logger.info(f"   - Total errors: {total_errors}")

        # Get final summary
        summary = await processor.get_processing_summary()
        logger.info(f"📊 Final Expert Knowledge Summary:")

        memory_totals = summary['memory_layers']
        logger.info(f"   - Structured memories: {memory_totals['structured_memory']}")
        logger.info(f"   - Semantic memories: {memory_totals['semantic_memory']}")
        logger.info(f"   - Graph relationships: {memory_totals['graph_relationships']}")

    except Exception as e:
        logger.error(f"❌ Failed multi-season processing: {str(e)}")
        raise


async def run_test_processing(processor: EnhancedHistoricalProcessor) -> None:
    """Run a small test to validate the system works"""
    logger.info("🧪 Running test processing (2024 Week 1 only)")

    try:
        # Process just Week 1 of 2024 as a test
        result = await processor.process_season_chronologically(
            season=2024,
            start_week=1,
            end_week=1
        )

        logger.info(f"✅ Test completed:")
        logger.info(f"   - Games processed: {result.processed_games}")
        logger.info(f"   - Processing time: {(datetime.now() - result.start_time).total_seconds():.1f} seconds")
        logger.info(f"   - Errors: {len(result.errors)}")

        if result.processed_games > 0:
            logger.info("🎉 Enhanced historical processing system is working!")

            # Show sample expert stats
            summary = await processor.get_processing_summary()
            sample_expert = list(summary['expert_statistics'].keys())[0]
            stats = summary['expert_statistics'][sample_expert]

            logger.info(f"📊 Sample expert ({sample_expert}) learned:")
            logger.info(f"   - Predictions made: {stats['predictions_made']}")
            logger.info(f"   - Team knowledge: {stats['team_knowledge_records']}")
            logger.info(f"   - Vector memories: {stats['vector_memories']}")
        else:
            logger.warning("⚠️ No games were processed - check data availability")

    except Exception as e:
        logger.error(f"❌ Test processing failed: {str(e)}")
        raise


async def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='Enhanced Historical Processing Runner')
    parser.add_argument('--season', type=int, help='Process single season (e.g., 2024)')
    parser.add_argument('--seasons', type=str, help='Process season range (e.g., 2023-2024)')
    parser.add_argument('--test', action='store_true', help='Run test processing (Week 1 only)')
    parser.add_argument('--openai-key', type=str, help='OpenAI API key for embeddings')

    args = parser.parse_args()

    # Get Supabase credentials
    supabase_url = os.getenv('SUPABASE_URL')
    supabase_key = os.getenv('SUPABASE_ANON_KEY')
    openai_key = args.openai_key or os.getenv('OPENAI_API_KEY')

    if not supabase_url or not supabase_key:
        logger.error("❌ SUPABASE_URL and SUPABASE_ANON_KEY environment variables required")
        sys.exit(1)

    if not openai_key:
        logger.warning("⚠️ No OpenAI API key provided - vector embeddings will be disabled")

    # Create Supabase client
    supabase = create_client(supabase_url, supabase_key)

    # Initialize enhanced processor
    processor = EnhancedHistoricalProcessor(
        supabase_client=supabase,
        openai_api_key=openai_key
    )

    # Initialize services
    logger.info("🔧 Initializing Enhanced Historical Processor...")
    initialized = await processor.initialize()

    if not initialized:
        logger.error("❌ Failed to initialize processor")
        sys.exit(1)

    logger.info("✅ Processor initialized successfully")

    try:
        if args.test:
            await run_test_processing(processor)

        elif args.season:
            await run_single_season(processor, args.season)

        elif args.seasons:
            # Parse season range
            if '-' in args.seasons:
                start_season, end_season = map(int, args.seasons.split('-'))
                await run_multiple_seasons(processor, start_season, end_season)
            else:
                logger.error("❌ Invalid season range format. Use: 2023-2024")
                sys.exit(1)

        else:
            logger.error("❌ Must specify --season, --seasons, or --test")
            parser.print_help()
            sys.exit(1)

    except KeyboardInterrupt:
        logger.info("🛑 Processing interrupted by user")

    except Exception as e:
        logger.error(f"💥 Processing failed: {str(e)}")
        sys.exit(1)

    finally:
        # Cleanup
        await processor.neo4j_service.close()
        logger.info("🏁 Enhanced Historical Processing completed")


if __name__ == "__main__":
    asyncio.run(main())
