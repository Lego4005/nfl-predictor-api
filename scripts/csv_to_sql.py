#!/usr/bin/env python3
"""
Convert CSV to SQL INSERT statements for Supabase
Creates SQL file that can be run in Supabase SQL Editor
"""

import csv
import json
from datetime import datetime

def csv_to_sql_inserts(csv_path, output_path, batch_size=1000):
    """Convert CSV to SQL INSERT statements"""
    print(f"🔄 Converting {csv_path} to SQL inserts...")
    
    insert_statements = []
    insert_statements.append("-- Historical Player Stats Data Import")
    insert_statements.append("-- Generated SQL INSERT statements")
    insert_statements.append("-- Run this in your Supabase SQL Editor")
    insert_statements.append("")
    
    with open(csv_path, 'r', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        
        # Collect rows for batch processing
        rows = []
        batch_count = 0
        total_rows = 0
        
        for row in reader:
            # Clean and format the data
            player_id = row['player_id']
            player_name = row['player_name'].replace("'", "''")  # Escape single quotes
            team = row['team']
            opponent = row['opponent']
            position = row['position']
            
            # Parse date
            game_date = datetime.fromisoformat(row['date'].replace('T', ' ').replace('Z', '')).strftime('%Y-%m-%d %H:%M:%S')
            week = int(row['week'])
            season = int(row['season'])
            
            # Handle numeric values, converting empty strings to 0
            def safe_float(val):
                try:
                    return float(val) if val and val != '' else 0.0
                except:
                    return 0.0
            
            def safe_int(val):
                try:
                    return int(val) if val and val != '' else 0
                except:
                    return 0
            
            passing_yards = safe_float(row['passing_yards'])
            passing_tds = safe_float(row['passing_tds'])
            passing_attempts = safe_float(row['passing_attempts'])
            passing_completions = safe_float(row['passing_completions'])
            rushing_yards = safe_float(row['rushing_yards'])
            rushing_tds = safe_float(row['rushing_tds'])
            rushing_attempts = safe_float(row['rushing_attempts'])
            receiving_yards = safe_float(row['receiving_yards'])
            receiving_tds = safe_float(row['receiving_tds'])
            receptions = safe_float(row['receptions'])
            targets = safe_int(row['targets'])
            snap_count = safe_float(row['snap_count'])
            snap_percentage = safe_float(row['snap_percentage'])
            
            # Create the INSERT statement values
            values = f"('{player_id}', '{player_name}', '{team}', '{opponent}', '{position}', '{game_date}', {week}, {season}, {passing_yards}, {passing_tds}, {passing_attempts}, {passing_completions}, {rushing_yards}, {rushing_tds}, {rushing_attempts}, {receiving_yards}, {receiving_tds}, {receptions}, {targets}, {snap_count}, {snap_percentage})"
            
            rows.append(values)
            total_rows += 1
            
            # Process in batches
            if len(rows) >= batch_size:
                batch_count += 1
                insert_statements.append(f"-- Batch {batch_count} ({len(rows)} records)")
                insert_statements.append("INSERT INTO historical_player_stats (")
                insert_statements.append("    player_id, player_name, team, opponent, position, game_date, week, season,")
                insert_statements.append("    passing_yards, passing_tds, passing_attempts, passing_completions,")
                insert_statements.append("    rushing_yards, rushing_tds, rushing_attempts,")
                insert_statements.append("    receiving_yards, receiving_tds, receptions, targets,")
                insert_statements.append("    snap_count, snap_percentage")
                insert_statements.append(") VALUES")
                
                # Add all rows in this batch
                for i, row_values in enumerate(rows):
                    if i == len(rows) - 1:
                        insert_statements.append(f"    {row_values};")
                    else:
                        insert_statements.append(f"    {row_values},")
                
                insert_statements.append("")
                rows = []
        
        # Handle remaining rows
        if rows:
            batch_count += 1
            insert_statements.append(f"-- Batch {batch_count} ({len(rows)} records)")
            insert_statements.append("INSERT INTO historical_player_stats (")
            insert_statements.append("    player_id, player_name, team, opponent, position, game_date, week, season,")
            insert_statements.append("    passing_yards, passing_tds, passing_attempts, passing_completions,")
            insert_statements.append("    rushing_yards, rushing_tds, rushing_attempts,")
            insert_statements.append("    receiving_yards, receiving_tds, receptions, targets,")
            insert_statements.append("    snap_count, snap_percentage")
            insert_statements.append(") VALUES")
            
            for i, row_values in enumerate(rows):
                if i == len(rows) - 1:
                    insert_statements.append(f"    {row_values};")
                else:
                    insert_statements.append(f"    {row_values},")
            
            insert_statements.append("")
    
    # Add summary comment
    insert_statements.append(f"-- Import complete: {total_rows} total records in {batch_count} batches")
    
    # Write to output file
    with open(output_path, 'w', encoding='utf-8') as outfile:
        outfile.write('\\n'.join(insert_statements))
    
    print(f"✅ Created SQL file: {output_path}")
    print(f"📊 Total records: {total_rows}")
    print(f"📦 Batches: {batch_count}")
    print()
    print("To import into Supabase:")
    print("1. First run the migration: supabase/migrations/031_historical_player_stats.sql")
    print("2. Then run this SQL file in your Supabase SQL Editor")
    
    return total_rows

if __name__ == "__main__":
    csv_path = "/home/iris/code/experimental/nfl-predictor-api/data/historical/players/historical_player_stats.csv"
    output_path = "/home/iris/code/experimental/nfl-predictor-api/scripts/historical_player_stats_inserts.sql"
    
    try:
        total = csv_to_sql_inserts(csv_path, output_path, batch_size=500)
        print(f"🎉 Successfully converted {total} records to SQL inserts!")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()