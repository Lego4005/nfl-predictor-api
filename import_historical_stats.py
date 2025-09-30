#!/usr/bin/env python3
"""
Script to import historical player stats CSV to Supabase
"""

import csv
import os
import sys
from datetime import datetime
from decimal import Decimal
from supabase import create_client, Client

# Supabase configuration
SUPABASE_URL = "https://vaypgzvivahnfegnlinn.supabase.co"
SUPABASE_KEY = os.environ.get("SUPABASE_ANON_KEY")

def get_supabase_client():
    """Initialize Supabase client"""
    if not SUPABASE_KEY:
        print("Error: SUPABASE_ANON_KEY environment variable not set")
        sys.exit(1)
    
    return create_client(SUPABASE_URL, SUPABASE_KEY)

def clean_numeric_value(value):
    """Clean and convert numeric values, handling empty strings"""
    if not value or value.strip() == '' or value.strip() == 'nan':
        return 0.0
    try:
        return float(value)
    except (ValueError, TypeError):
        return 0.0

def clean_date_value(date_str):
    """Parse date string to timestamp and return as ISO string"""
    if not date_str or date_str.strip() == '':
        return None
    try:
        # Parse ISO format date: 2025-08-26T16:08:25.754797
        dt = datetime.fromisoformat(date_str.replace('T', ' ').split('.')[0])
        # Return as ISO format string for JSON serialization
        return dt.isoformat()
    except (ValueError, TypeError):
        return None

def process_csv_file(file_path):
    """Process CSV file and prepare data for Supabase"""
    print(f"Processing CSV file: {file_path}")
    
    try:
        records = []
        
        with open(file_path, 'r', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            
            for index, row in enumerate(reader):
                # Clean snap_percentage - handle empty values
                snap_percentage = row.get('snap_percentage', '').strip()
                if snap_percentage == '' or snap_percentage == 'nan':
                    snap_percentage = None
                
                record = {
                    'player_id': str(row['player_id']),
                    'player_name': str(row['player_name']),
                    'team': str(row['team']),
                    'opponent': str(row['opponent']),
                    'date': clean_date_value(str(row['date'])),
                    'week': int(clean_numeric_value(row['week'])),
                    'season': int(clean_numeric_value(row['season'])),
                    'position': str(row['position']),
                    'passing_yards': clean_numeric_value(row['passing_yards']),
                    'passing_tds': clean_numeric_value(row['passing_tds']),
                    'passing_attempts': clean_numeric_value(row['passing_attempts']),
                    'passing_completions': clean_numeric_value(row['passing_completions']),
                    'rushing_yards': clean_numeric_value(row['rushing_yards']),
                    'rushing_tds': clean_numeric_value(row['rushing_tds']),
                    'rushing_attempts': clean_numeric_value(row['rushing_attempts']),
                    'receiving_yards': clean_numeric_value(row['receiving_yards']),
                    'receiving_tds': clean_numeric_value(row['receiving_tds']),
                    'receptions': clean_numeric_value(row['receptions']),
                    'targets': clean_numeric_value(row['targets']),
                    'snap_count': clean_numeric_value(row['snap_count']),
                    'snap_percentage': snap_percentage
                }
                records.append(record)
                
                # Progress indicator
                if (index + 1) % 1000 == 0:
                    print(f"Processed {index + 1} records...")
        
        print(f"Found {len(records)} rows in CSV")
        return records
        
    except Exception as e:
        print(f"Error processing CSV file: {e}")
        return []

def upload_to_supabase(records, batch_size=1000):
    """Upload records to Supabase in batches"""
    supabase = get_supabase_client()
    
    total_records = len(records)
    print(f"Uploading {total_records} records to Supabase in batches of {batch_size}")
    
    successful_inserts = 0
    failed_inserts = 0
    
    for i in range(0, total_records, batch_size):
        batch = records[i:i + batch_size]
        batch_num = (i // batch_size) + 1
        total_batches = (total_records + batch_size - 1) // batch_size
        
        try:
            print(f"Uploading batch {batch_num}/{total_batches} ({len(batch)} records)...")
            
            # Insert batch
            result = supabase.table('historical_player_stats').insert(batch).execute()
            
            if result.data:
                successful_inserts += len(batch)
                print(f"✓ Batch {batch_num} uploaded successfully")
            else:
                failed_inserts += len(batch)
                print(f"✗ Batch {batch_num} failed - no data returned")
                
        except Exception as e:
            failed_inserts += len(batch)
            print(f"✗ Batch {batch_num} failed: {e}")
            
            # Log some sample records for debugging
            if len(batch) > 0:
                print(f"Sample record from failed batch: {batch[0]}")
    
    print(f"\nUpload complete!")
    print(f"Successful inserts: {successful_inserts}")
    print(f"Failed inserts: {failed_inserts}")
    print(f"Total processed: {successful_inserts + failed_inserts}")
    
    return successful_inserts, failed_inserts

def main():
    """Main function"""
    csv_file_path = '/home/iris/code/experimental/nfl-predictor-api/data/historical/players/historical_player_stats.csv'
    
    if not os.path.exists(csv_file_path):
        print(f"Error: CSV file not found at {csv_file_path}")
        sys.exit(1)
    
    print("Starting historical player stats import...")
    print(f"CSV file: {csv_file_path}")
    print(f"Target database: {SUPABASE_URL}")
    
    # Process CSV file
    records = process_csv_file(csv_file_path)
    
    if not records:
        print("No records to upload. Exiting.")
        sys.exit(1)
    
    # Upload to Supabase
    successful, failed = upload_to_supabase(records)
    
    if failed > 0:
        print(f"\nWarning: {failed} records failed to upload")
        sys.exit(1)
    else:
        print(f"\nSuccess! All {successful} records uploaded successfully")

if __name__ == "__main__":
    main()