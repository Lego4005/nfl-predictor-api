#!/usr/bin/env python3
"""
Load Historical NFL Games CSV to Supabase Database
Handles upserts, NULL conversions, and data type transformations for historical games data
"""

import os
import sys
import pandas as pd
import numpy as np
from datetime import datetime
import logging
from typing import Optional, Dict, Any, List
import json

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # dotenv is optional

# Add src to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

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
    # Try both VITE_ and non-VITE prefixed environment variables
    supabase_url = os.getenv('SUPABASE_URL') or os.getenv('VITE_SUPABASE_URL')
    supabase_key = os.getenv('SUPABASE_ANON_KEY') or os.getenv('VITE_SUPABASE_ANON_KEY')
    
    if not supabase_url or not supabase_key:
        logger.error("❌ Missing SUPABASE_URL or SUPABASE_ANON_KEY environment variables")
        logger.info("Please set these in your .env file:")
        logger.info("SUPABASE_URL=your_supabase_project_url")
        logger.info("SUPABASE_ANON_KEY=your_supabase_anon_key")
        logger.info("(or use VITE_ prefixed versions)")
        return None
    
    try:
        supabase: Client = create_client(supabase_url, supabase_key)
        logger.info("✅ Connected to Supabase")
        return supabase
    except Exception as e:
        logger.error(f"❌ Failed to connect to Supabase: {e}")
        return None


def clean_numeric_value(value) -> Optional[float]:
    """
    Convert numeric values from CSV, handling empty strings and NaN
    Returns None for missing values, which becomes NULL in Postgres
    """
    if pd.isna(value) or value == '' or value == 'NA':
        return None
    try:
        return float(value)
    except (ValueError, TypeError):
        return None


def clean_integer_value(value) -> Optional[int]:
    """
    Convert integer values from CSV, handling empty strings and NaN
    """
    if pd.isna(value) or value == '' or value == 'NA':
        return None
    try:
        return int(float(value))  # Convert through float first to handle decimal strings
    except (ValueError, TypeError):
        return None


def clean_string_value(value) -> Optional[str]:
    """
    Convert string values, handling empty strings and NaN
    """
    if pd.isna(value) or value == '' or value == 'NA':
        return None
    return str(value).strip()


def clean_boolean_value(value) -> Optional[bool]:
    """
    Convert boolean values, handling various representations
    """
    if pd.isna(value) or value == '' or value == 'NA':
        return None
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    if isinstance(value, str):
        return value.lower() in ('true', 't', 'yes', 'y', '1')
    return None


def ensure_nfl_games_table(supabase: Client) -> bool:
    """Create the nfl_games table if it doesn't exist"""
    logger.info("🔍 Checking if nfl_games table exists...")
    
    try:
        # Try a simple select to see if table exists
        response = supabase.table('nfl_games').select('id').limit(1).execute()
        logger.info("✅ Table nfl_games already exists")
        return True
    except Exception as e:
        logger.warning(f"⚠️ Table may not exist or needs creation: {e}")
        
        # Create the table with comprehensive schema
        logger.info("🔨 Creating nfl_games table...")
        
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS nfl_games (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            game_id VARCHAR(100) UNIQUE NOT NULL,
            season INTEGER,
            week INTEGER, 
            game_type VARCHAR(20),
            game_date DATE,
            game_datetime TIMESTAMP WITH TIME ZONE,
            
            -- Teams
            home_team VARCHAR(10),
            away_team VARCHAR(10),
            home_score INTEGER,
            away_score INTEGER,
            
            -- Game Details
            overtime BOOLEAN DEFAULT false,
            stadium VARCHAR(100),
            roof VARCHAR(20),
            surface VARCHAR(20),
            weather_temperature INTEGER,
            weather_wind_mph INTEGER,
            
            -- Rest and Preparation
            away_rest INTEGER,
            home_rest INTEGER,
            
            -- Betting Lines
            spread_line DECIMAL(5,2),
            away_spread_odds INTEGER,
            home_spread_odds INTEGER,
            total_line DECIMAL(5,2),
            over_odds INTEGER,
            under_odds INTEGER,
            away_moneyline INTEGER,
            home_moneyline INTEGER,
            
            -- Personnel
            away_qb_id VARCHAR(20),
            away_qb_name VARCHAR(100),
            home_qb_id VARCHAR(20),
            home_qb_name VARCHAR(100),
            away_coach VARCHAR(100),
            home_coach VARCHAR(100),
            
            -- Additional Game Info
            div_game BOOLEAN DEFAULT false,
            result INTEGER,
            total INTEGER,
            location VARCHAR(10),
            weekday VARCHAR(15),
            referee VARCHAR(100),
            
            -- Legacy IDs and References
            old_game_id VARCHAR(50),
            gsis VARCHAR(50),
            nfl_detail_id VARCHAR(50),
            pfr VARCHAR(50),
            pff VARCHAR(50),
            espn VARCHAR(50),
            ftn VARCHAR(50),
            stadium_id VARCHAR(50),
            
            -- Metadata
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        );
        
        -- Create indexes for performance
        CREATE INDEX IF NOT EXISTS idx_nfl_games_game_id ON nfl_games(game_id);
        CREATE INDEX IF NOT EXISTS idx_nfl_games_season_week ON nfl_games(season, week);
        CREATE INDEX IF NOT EXISTS idx_nfl_games_teams ON nfl_games(home_team, away_team);
        CREATE INDEX IF NOT EXISTS idx_nfl_games_date ON nfl_games(game_date);
        """
        
        try:
            supabase.postgrest.rpc('exec_sql', {'sql': create_table_sql}).execute()
            logger.info("✅ Created nfl_games table successfully")
            return True
        except Exception as create_error:
            logger.error(f"❌ Failed to create table: {create_error}")
            logger.info("Please create the table manually in Supabase SQL Editor:")
            logger.info(create_table_sql)
            return False


def process_csv_data(csv_path: str) -> Optional[pd.DataFrame]:
    """Load and process the CSV data"""
    logger.info(f"📊 Loading CSV data from {csv_path}")
    
    try:
        df = pd.read_csv(csv_path)
        logger.info(f"✅ Loaded {len(df)} rows from CSV")
        logger.info(f"📋 Columns: {list(df.columns)}")
        
        # Handle NaN values by converting to None (for proper NULL insertion)
        df = df.replace({np.nan: None})
        
        # Show data range
        if 'season' in df.columns:
            logger.info(f"📈 Season range: {df['season'].min()} - {df['season'].max()}")
        
        if 'gameday' in df.columns:
            logger.info(f"📅 Date range: {df['gameday'].min()} - {df['gameday'].max()}")
        
        logger.info(f"✅ Processed CSV data - {len(df)} rows ready for upload")
        return df
        
    except Exception as e:
        logger.error(f"❌ Error processing CSV: {e}")
        return None


def convert_csv_row_to_record(row: pd.Series) -> Dict[str, Any]:
    """Convert a CSV row to a database record with proper data types"""
    
    # Parse date and datetime
    game_date = clean_string_value(row.get('gameday'))
    game_datetime = None
    if game_date and clean_string_value(row.get('gametime')):
        try:
            game_datetime = f"{game_date}T{row['gametime']}"
        except:
            game_datetime = game_date
    
    record = {
        'game_id': clean_string_value(row.get('game_id')),
        'season': clean_integer_value(row.get('season')),
        'week': clean_integer_value(row.get('week')),
        'game_type': clean_string_value(row.get('game_type')),
        'game_date': game_date,
        'game_datetime': game_datetime,
        
        # Teams
        'home_team': clean_string_value(row.get('home_team')),
        'away_team': clean_string_value(row.get('away_team')),
        'home_score': clean_integer_value(row.get('home_score')),
        'away_score': clean_integer_value(row.get('away_score')),
        
        # Game Details
        'overtime': clean_boolean_value(row.get('overtime', 0)),
        'stadium': clean_string_value(row.get('stadium')),
        'roof': clean_string_value(row.get('roof')),
        'surface': clean_string_value(row.get('surface')),
        'weather_temperature': clean_integer_value(row.get('temp')),
        'weather_wind_mph': clean_integer_value(row.get('wind')),
        
        # Rest and Preparation
        'away_rest': clean_integer_value(row.get('away_rest')),
        'home_rest': clean_integer_value(row.get('home_rest')),
        
        # Betting Lines
        'spread_line': clean_numeric_value(row.get('spread_line')),
        'away_spread_odds': clean_integer_value(row.get('away_spread_odds')),
        'home_spread_odds': clean_integer_value(row.get('home_spread_odds')),
        'total_line': clean_numeric_value(row.get('total_line')),
        'over_odds': clean_integer_value(row.get('over_odds')),
        'under_odds': clean_integer_value(row.get('under_odds')),
        'away_moneyline': clean_integer_value(row.get('away_moneyline')),
        'home_moneyline': clean_integer_value(row.get('home_moneyline')),
        
        # Personnel
        'away_qb_id': clean_string_value(row.get('away_qb_id')),
        'away_qb_name': clean_string_value(row.get('away_qb_name')),
        'home_qb_id': clean_string_value(row.get('home_qb_id')),
        'home_qb_name': clean_string_value(row.get('home_qb_name')),
        'away_coach': clean_string_value(row.get('away_coach')),
        'home_coach': clean_string_value(row.get('home_coach')),
        
        # Additional Game Info
        'div_game': clean_boolean_value(row.get('div_game', 0)),
        'result': clean_integer_value(row.get('result')),
        'total': clean_integer_value(row.get('total')),
        'location': clean_string_value(row.get('location')),
        'weekday': clean_string_value(row.get('weekday')),
        'referee': clean_string_value(row.get('referee')),
        
        # Legacy IDs
        'old_game_id': clean_string_value(row.get('old_game_id')),
        'gsis': clean_string_value(row.get('gsis')),
        'nfl_detail_id': clean_string_value(row.get('nfl_detail_id')),
        'pfr': clean_string_value(row.get('pfr')),
        'pff': clean_string_value(row.get('pff')),
        'espn': clean_string_value(row.get('espn')),
        'ftn': clean_string_value(row.get('ftn')),
        'stadium_id': clean_string_value(row.get('stadium_id')),
        
        # Metadata
        'updated_at': datetime.now().isoformat()
    }
    
    # Remove None values to let database defaults handle them
    return {k: v for k, v in record.items() if v is not None}


def upload_to_supabase(supabase: Client, df: pd.DataFrame, batch_size: int = 100) -> bool:
    """Upload data to Supabase in batches using upsert"""
    logger.info(f"🚀 Starting upload to Supabase (batch size: {batch_size})")
    
    try:
        total_records = len(df)
        uploaded_count = 0
        failed_count = 0
        
        # Process in batches
        for i in range(0, total_records, batch_size):
            batch_df = df.iloc[i:i + batch_size]
            batch_num = (i // batch_size) + 1
            total_batches = (total_records + batch_size - 1) // batch_size
            
            logger.info(f"📤 Processing batch {batch_num}/{total_batches} ({len(batch_df)} records)")
            
            # Convert batch to records
            batch_records = []
            for _, row in batch_df.iterrows():
                record = convert_csv_row_to_record(row)
                if record.get('game_id'):  # Only include records with valid game_id
                    batch_records.append(record)
            
            if not batch_records:
                logger.warning(f"⚠️ No valid records in batch {batch_num}")
                continue
            
            try:
                # Use upsert to handle duplicates
                response = supabase.table('nfl_games').upsert(
                    batch_records,
                    on_conflict='game_id'
                ).execute()
                
                if response.data:
                    uploaded_count += len(batch_records)
                    logger.info(f"✅ Successfully uploaded batch {batch_num}")
                else:
                    logger.warning(f"⚠️ No data returned for batch {batch_num}")
                    
            except Exception as e:
                logger.error(f"❌ Failed to upload batch {batch_num}: {e}")
                failed_count += len(batch_records)
                
                # Show a sample record for debugging
                if batch_records:
                    logger.error(f"Sample record from failed batch: {json.dumps(batch_records[0], default=str, indent=2)}")
        
        logger.info(f"\n📊 Upload Summary:")
        logger.info(f"   ✅ Successfully uploaded: {uploaded_count} records")
        logger.info(f"   ❌ Failed to upload: {failed_count} records")
        if total_records > 0:
            logger.info(f"   📈 Success rate: {(uploaded_count / total_records) * 100:.1f}%")
        
        return failed_count == 0
        
    except Exception as e:
        logger.error(f"❌ Error during upload: {e}")
        return False


def verify_upload(supabase: Client) -> bool:
    """Verify the upload was successful"""
    logger.info("🔍 Verifying upload...")
    
    try:
        # Get count of records
        response = supabase.table('nfl_games').select('id', count='exact').execute()
        record_count = response.count
        
        logger.info(f"✅ Found {record_count} games in database")
        
        # Get sample of data to verify structure
        sample_response = supabase.table('nfl_games').select('*').limit(5).execute()
        
        if sample_response.data:
            logger.info("📋 Sample games:")
            for i, game in enumerate(sample_response.data[:3]):
                home_team = game.get('home_team', 'UNK')
                away_team = game.get('away_team', 'UNK')
                week = game.get('week', '?')
                season = game.get('season', '?')
                home_score = game.get('home_score', '?')
                away_score = game.get('away_score', '?')
                logger.info(f"   {i+1}. {away_team} @ {home_team} ({away_score}-{home_score}) - Week {week} {season}")
        
        # Get statistics by season
        stats_response = supabase.table('nfl_games').select('season, home_score').not_.is_('home_score', 'null').execute()
        
        if stats_response.data:
            seasons = {}
            completed_games = 0
            for game in stats_response.data:
                season = game.get('season')
                if season:
                    seasons[season] = seasons.get(season, 0) + 1
                    if game.get('home_score') is not None:
                        completed_games += 1
            
            logger.info(f"\n📈 Games by season:")
            for season in sorted(seasons.keys()):
                logger.info(f"   {season}: {seasons[season]} games")
            
            logger.info(f"\n🏈 Game status:")
            logger.info(f"   Completed games (with scores): {completed_games}")
            logger.info(f"   Total games: {record_count}")
        
        return record_count > 0
        
    except Exception as e:
        logger.error(f"❌ Error verifying upload: {e}")
        return False


def main():
    """Main function to orchestrate the upload process"""
    logger.info("🏈 NFL Historical Games Data Loader")
    logger.info("=" * 50)
    
    # Path to the CSV file - update this to match your file location
    csv_path = "/home/iris/code/experimental/nfl-predictor-api/data/historical/games/games.csv"
    
    # Check if CSV file exists
    if not os.path.exists(csv_path):
        logger.error(f"❌ CSV file not found: {csv_path}")
        logger.info("Please update the csv_path variable in the script")
        return False
    
    # Load Supabase client
    supabase = load_supabase_client()
    if not supabase:
        return False
    
    # Ensure table exists
    if not ensure_nfl_games_table(supabase):
        return False
    
    # Process CSV data
    df = process_csv_data(csv_path)
    if df is None:
        return False
    
    # Upload to Supabase
    success = upload_to_supabase(supabase, df)
    if not success:
        logger.error("❌ Upload failed")
        return False
    
    # Verify upload
    verify_success = verify_upload(supabase)
    
    if verify_success:
        logger.info("\n🎉 Successfully loaded historical NFL games data!")
        logger.info("   Your database is now ready for predictions and analysis!")
    else:
        logger.error("❌ Upload verification failed")
        return False
    
    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)