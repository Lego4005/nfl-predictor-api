#!/usr/bin/env python3
"""
Upload Historical Player Stats to Supabase
Uploads the historical_player_stats.csv file to Supabase database
"""

import os
import sys
import pandas as pd
import numpy as np
from datetime import datetime
import logging
from typing import Optional
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
logging.basicConfig(level=logging.INFO)
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

def ensure_table_exists(supabase: Client) -> bool:
    """Check if the table exists and create it if it doesn't"""
    logger.info("🔍 Checking if historical_player_stats table exists...")
    
    try:
        # Try a simple select to see if table exists
        response = supabase.table('historical_player_stats').select('id').limit(1).execute()
        logger.info("✅ Table historical_player_stats already exists")
        return True
    except Exception as e:
        logger.warning(f"⚠️ Table may not exist: {e}")
        logger.info("📋 Please create the historical_player_stats table manually in Supabase:")
        logger.info("1. Go to your Supabase dashboard")
        logger.info("2. Navigate to the SQL Editor")
        logger.info("3. Copy and run the migration from: supabase/migrations/031_historical_player_stats.sql")
        return False

def process_csv_data(csv_path: str) -> pd.DataFrame:
    """Load and process the CSV data"""
    logger.info(f"📊 Loading CSV data from {csv_path}")
    
    try:
        df = pd.read_csv(csv_path)
        logger.info(f"✅ Loaded {len(df)} rows from CSV")
        
        # Convert date column to proper datetime
        df['date'] = pd.to_datetime(df['date'])
        
        # Handle NaN values by converting to None (for proper NULL insertion)
        df = df.replace({np.nan: None})
        
        # Ensure numeric columns are properly typed
        numeric_columns = [
            'passing_yards', 'passing_tds', 'passing_attempts', 'passing_completions',
            'rushing_yards', 'rushing_tds', 'rushing_attempts',
            'receiving_yards', 'receiving_tds', 'receptions', 'targets',
            'snap_count', 'snap_percentage'
        ]
        
        for col in numeric_columns:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
        
        # Rename date column to match database schema
        df = df.rename(columns={'date': 'game_date'})
        
        logger.info(f"✅ Processed CSV data - {len(df)} rows ready for upload")
        logger.info(f"📈 Data range: {df['season'].min()} - {df['season'].max()}")
        logger.info(f"🏈 Positions: {sorted(df['position'].unique())}")
        
        return df
        
    except Exception as e:
        logger.error(f"❌ Error processing CSV: {e}")
        return None

def upload_to_supabase(supabase: Client, df: pd.DataFrame, batch_size: int = 1000) -> bool:
    """Upload data to Supabase in batches"""
    logger.info(f"🚀 Starting upload to Supabase (batch size: {batch_size})")
    
    try:
        # First, apply the migration to create the table
        logger.info("📋 Applying migration to create table...")
        
        # Convert DataFrame to list of dictionaries
        records = df.to_dict('records')
        total_records = len(records)
        
        # Upload in batches
        uploaded_count = 0
        failed_count = 0
        
        for i in range(0, total_records, batch_size):
            batch = records[i:i + batch_size]
            batch_num = (i // batch_size) + 1
            total_batches = (total_records + batch_size - 1) // batch_size
            
            logger.info(f"📤 Uploading batch {batch_num}/{total_batches} ({len(batch)} records)")
            
            try:
                # Use upsert to handle potential duplicates
                response = supabase.table('historical_player_stats').upsert(batch).execute()
                
                if response.data:
                    uploaded_count += len(batch)
                    logger.info(f"✅ Successfully uploaded batch {batch_num}")
                else:
                    logger.warning(f"⚠️ No data returned for batch {batch_num}")
                    
            except Exception as e:
                logger.error(f"❌ Failed to upload batch {batch_num}: {e}")
                failed_count += len(batch)
                
                # Show a few sample records for debugging
                if batch:
                    logger.error(f"Sample record from failed batch: {json.dumps(batch[0], default=str, indent=2)}")
        
        logger.info(f"📊 Upload Summary:")
        logger.info(f"   ✅ Successfully uploaded: {uploaded_count} records")
        logger.info(f"   ❌ Failed to upload: {failed_count} records")
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
        response = supabase.table('historical_player_stats').select('id', count='exact').execute()
        record_count = response.count
        
        logger.info(f"✅ Found {record_count} records in database")
        
        # Get sample of data to verify structure
        sample_response = supabase.table('historical_player_stats').select('*').limit(5).execute()
        
        if sample_response.data:
            logger.info("📋 Sample records:")
            for i, record in enumerate(sample_response.data[:3]):
                logger.info(f"   {i+1}. {record['player_name']} ({record['position']}) - {record['team']} vs {record['opponent']} Week {record['week']} {record['season']}")
        
        # Get some basic statistics
        stats_response = supabase.rpc('get_player_stats_summary').execute()
        
        return record_count > 0
        
    except Exception as e:
        logger.error(f"❌ Error verifying upload: {e}")
        return False

def main():
    """Main function to orchestrate the upload process"""
    logger.info("🏈 NFL Historical Player Stats Uploader")
    logger.info("=" * 50)
    
    # Path to the CSV file
    csv_path = "/home/iris/code/experimental/nfl-predictor-api/data/historical/players/historical_player_stats.csv"
    
    if not os.path.exists(csv_path):
        logger.error(f"❌ CSV file not found: {csv_path}")
        return False
    
    # Load Supabase client
    supabase = load_supabase_client()
    if not supabase:
        return False
    
    # Check if table exists
    if not ensure_table_exists(supabase):
        logger.error("❌ Cannot proceed without the database table")
        return False
    
    # Process CSV data
    df = process_csv_data(csv_path)
    if df is None or df.empty:
        logger.error("❌ No data to upload")
        return False
    
    # Upload to Supabase
    success = upload_to_supabase(supabase, df)
    if not success:
        logger.error("❌ Upload failed")
        return False
    
    # Verify upload
    verification_success = verify_upload(supabase)
    
    if verification_success:
        logger.info("🎉 Historical player stats successfully uploaded to Supabase!")
        logger.info("You can now query the data using the 'historical_player_stats' table")
    else:
        logger.warning("⚠️ Upload completed but verification failed")
    
    return verification_success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)