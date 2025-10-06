#!/usr/bin/env python3
"""
Simple CSV to Supabase Loader for Historical NFL Games
Uses built-in csv module instead of pandas
"""

import os
import sys
import csv
import json
from datetime import datetime
import logging
from typing import Optional, Dict, Any, List

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # dotenv is optional

try:
    from supabase import create_client, Client
except ImportError:
    print("❌ Please install supabase: pip install supabase")
    sys.exit(1)

# Configure logging
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def load_supabase_client() -> Optional[Client]:
    """Load Supabase client with environment variables"""
    supabase_url = os.getenv('SUPABASE_URL') or os.getenv('VITE_SUPABASE_URL')
    supabase_key = os.getenv('SUPABASE_ANON_KEY') or os.getenv('VITE_SUPABASE_ANON_KEY')
    
    if not supabase_url or not supabase_key:
        logger.error("❌ Missing SUPABASE_URL or SUPABASE_ANON_KEY environment variables")
        return None
    
    try:
        supabase: Client = create_client(supabase_url, supabase_key)
        logger.info("✅ Connected to Supabase")
        return supabase
    except Exception as e:
        logger.error(f"❌ Failed to connect to Supabase: {e}")
        return None


def clean_value(value: str, data_type: str = 'string') -> Any:
    """Clean and convert values based on type"""
    if not value or value.strip() == '' or value.strip().upper() == 'NA':
        return None
    
    value = value.strip()
    
    try:
        if data_type == 'integer':
            return int(float(value))  # Convert through float to handle "1.0"
        elif data_type == 'float':
            return float(value)
        elif data_type == 'boolean':
            return value.lower() in ('true', 't', 'yes', 'y', '1', '1.0')
        else:
            return value
    except (ValueError, TypeError):
        return None


def check_table_exists(supabase: Client) -> bool:
    """Check if nfl_games table exists"""
    try:
        response = supabase.table('nfl_games').select('game_id').limit(1).execute()
        logger.info("✅ Table nfl_games exists")
        return True
    except Exception as e:
        logger.warning(f"⚠️ Table check failed: {e}")
        logger.error("❌ Please create the nfl_games table first!")
        logger.info("The table should already exist based on your schema")
        return False


def convert_row_to_record(row: Dict[str, str]) -> Dict[str, Any]:
    """Convert CSV row to database record with exact schema match"""
    
    # Parse date and time
    game_date = clean_value(row.get('gameday', ''))
    game_time = clean_value(row.get('gametime', ''))
    game_datetime = None
    if game_date and game_time:
        try:
            game_datetime = f"{game_date} {game_time}"
        except:
            game_datetime = game_date
    
    # Build record with ALL required columns to match table schema
    record = {
        # Primary identifiers
        'game_id': clean_value(row.get('game_id', '')),
        'season': clean_value(row.get('season', ''), 'integer'),
        'week': clean_value(row.get('week', ''), 'integer'),
        'game_type': clean_value(row.get('game_type', '')),
        'game_date': game_date,
        'game_time': game_time,
        'game_datetime': game_datetime,
        
        # Teams and scores
        'home_team': clean_value(row.get('home_team', '')),
        'away_team': clean_value(row.get('away_team', '')),
        'home_score': clean_value(row.get('home_score', ''), 'integer'),
        'away_score': clean_value(row.get('away_score', ''), 'integer'),
        
        # Game characteristics
        'overtime': clean_value(row.get('overtime', '0'), 'boolean'),
        'stadium': clean_value(row.get('stadium', '')),
        'roof': clean_value(row.get('roof', '')),
        'surface': clean_value(row.get('surface', '')),
        
        # Weather data
        'weather_temperature': clean_value(row.get('temp', ''), 'integer'),
        'weather_wind_mph': clean_value(row.get('wind', ''), 'integer'),
        'weather_humidity': None,  # Not in CSV
        'weather_description': None,  # Not in CSV
        
        # Rest and preparation
        'away_rest': clean_value(row.get('away_rest', ''), 'integer'),
        'home_rest': clean_value(row.get('home_rest', ''), 'integer'),
        
        # Betting lines
        'spread_line': clean_value(row.get('spread_line', ''), 'float'),
        'away_spread_odds': clean_value(row.get('away_spread_odds', ''), 'integer'),
        'home_spread_odds': clean_value(row.get('home_spread_odds', ''), 'integer'),
        'total_line': clean_value(row.get('total_line', ''), 'float'),
        'over_odds': clean_value(row.get('over_odds', ''), 'integer'),
        'under_odds': clean_value(row.get('under_odds', ''), 'integer'),
        'away_moneyline': clean_value(row.get('away_moneyline', ''), 'integer'),
        'home_moneyline': clean_value(row.get('home_moneyline', ''), 'integer'),
        
        # Personnel
        'away_qb_id': clean_value(row.get('away_qb_id', '')),
        'away_qb_name': clean_value(row.get('away_qb_name', '')),
        'home_qb_id': clean_value(row.get('home_qb_id', '')),
        'home_qb_name': clean_value(row.get('home_qb_name', '')),
        'away_coach': clean_value(row.get('away_coach', '')),
        'home_coach': clean_value(row.get('home_coach', '')),
        
        # Game info
        'div_game': clean_value(row.get('div_game', '0'), 'boolean'),
        'result': clean_value(row.get('result', ''), 'integer'),
        'total': clean_value(row.get('total', ''), 'integer'),
        'location': clean_value(row.get('location', '')),
        'weekday': clean_value(row.get('weekday', '')),
        'referee': clean_value(row.get('referee', '')),
        
        # Cross-reference IDs
        'old_game_id': clean_value(row.get('old_game_id', '')),
        'gsis': clean_value(row.get('gsis', '')),
        'nfl_detail_id': clean_value(row.get('nfl_detail_id', '')),
        'pfr': clean_value(row.get('pfr', '')),
        'pff': clean_value(row.get('pff', '')),
        'espn': clean_value(row.get('espn', '')),
        'ftn': clean_value(row.get('ftn', '')),
        'stadium_id': clean_value(row.get('stadium_id', '')),
        
        # Metadata - let database handle these
        'created_at': None,
        'updated_at': None
    }
    
    # Keep None values to ensure all records have same structure
    return record


def load_csv_data(csv_path: str, batch_size: int = 100) -> List[List[Dict[str, Any]]]:
    """Load CSV data and return batches"""
    logger.info(f"📊 Loading CSV data from {csv_path}")
    
    try:
        batches = []
        current_batch = []
        total_rows = 0
        
        with open(csv_path, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            logger.info(f"📋 CSV columns: {reader.fieldnames}")
            
            for row in reader:
                record = convert_row_to_record(row)
                if record.get('game_id'):  # Only include valid records
                    current_batch.append(record)
                    total_rows += 1
                    
                    if len(current_batch) >= batch_size:
                        batches.append(current_batch)
                        current_batch = []
            
            # Add remaining records
            if current_batch:
                batches.append(current_batch)
        
        logger.info(f"✅ Loaded {total_rows} valid records in {len(batches)} batches")
        return batches
        
    except Exception as e:
        logger.error(f"❌ Error loading CSV: {e}")
        return []


def upload_batches(supabase: Client, batches: List[List[Dict[str, Any]]]) -> bool:
    """Upload data batches to Supabase"""
    logger.info(f"🚀 Uploading {len(batches)} batches to Supabase")
    
    uploaded_count = 0
    failed_count = 0
    
    for i, batch in enumerate(batches):
        batch_num = i + 1
        logger.info(f"📤 Uploading batch {batch_num}/{len(batches)} ({len(batch)} records)")
        
        try:
            response = supabase.table('nfl_games').upsert(
                batch,
                on_conflict='game_id'
            ).execute()
            
            if response.data:
                uploaded_count += len(batch)
                logger.info(f"✅ Successfully uploaded batch {batch_num}")
            else:
                logger.warning(f"⚠️ No data returned for batch {batch_num}")
                
        except Exception as e:
            logger.error(f"❌ Failed to upload batch {batch_num}: {e}")
            failed_count += len(batch)
            
            # Show sample record for debugging
            if batch:
                logger.error(f"Sample record: {json.dumps(batch[0], default=str, indent=2)}")
    
    logger.info(f"\n📊 Upload Summary:")
    logger.info(f"   ✅ Successfully uploaded: {uploaded_count} records")
    logger.info(f"   ❌ Failed to upload: {failed_count} records")
    
    return failed_count == 0


def verify_upload(supabase: Client) -> None:
    """Verify the upload was successful"""
    logger.info("🔍 Verifying upload...")
    
    try:
        # Get count
        response = supabase.table('nfl_games').select('game_id', count='exact').execute()
        total_count = response.count
        logger.info(f"✅ Total games in database: {total_count}")
        
        # Get completed games
        completed_response = supabase.table('nfl_games').select('game_id', count='exact').not_.is_('home_score', 'null').execute()
        completed_count = completed_response.count
        logger.info(f"🏈 Completed games (with scores): {completed_count}")
        
        # Get sample
        sample_response = supabase.table('nfl_games').select('*').limit(3).execute()
        if sample_response.data:
            logger.info("📋 Sample games:")
            for i, game in enumerate(sample_response.data):
                home = game.get('home_team', 'UNK')
                away = game.get('away_team', 'UNK')
                week = game.get('week', '?')
                season = game.get('season', '?')
                logger.info(f"   {i+1}. {away} @ {home} - Week {week} {season}")
        
    except Exception as e:
        logger.error(f"❌ Error verifying: {e}")


def main():
    """Main function"""
    logger.info("🏈 NFL Historical Games CSV Loader")
    logger.info("=" * 40)
    
    # Configuration
    csv_path = "/home/iris/code/experimental/nfl-predictor-api/data/historical/games/games.csv"
    
    # Check file exists
    if not os.path.exists(csv_path):
        logger.error(f"❌ CSV file not found: {csv_path}")
        return False
    
    # Connect to Supabase
    supabase = load_supabase_client()
    if not supabase:
        return False
    
    # Check table exists
    if not check_table_exists(supabase):
        return False
    
    # Load and process data
    batches = load_csv_data(csv_path)
    if not batches:
        logger.error("❌ No data to upload")
        return False
    
    # Upload data
    success = upload_batches(supabase, batches)
    
    # Verify
    verify_upload(supabase)
    
    if success:
        logger.info("\n🎉 Successfully loaded historical NFL games!")
        logger.info("   Database is ready for predictions!")
    
    return success


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)