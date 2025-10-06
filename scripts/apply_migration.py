#!/usr/bin/env python3
"""
Apply Historical Player Stats Migration to Supabase
Creates the historical_player_stats table in Supabase
"""

import os
import sys
from dotenv import load_dotenv
load_dotenv()

try:
    from supabase import create_client, Client
except ImportError:
    print("❌ Please install supabase: pip install supabase")
    sys.exit(1)

def run_migration():
    # Load environment variables
    supabase_url = os.getenv('SUPABASE_URL') or os.getenv('VITE_SUPABASE_URL')
    supabase_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY') or os.getenv('VITE_SUPABASE_ANON_KEY')
    
    if not supabase_url or not supabase_key:
        print("❌ Missing Supabase credentials")
        return False
    
    print("🔗 Connecting to Supabase...")
    supabase: Client = create_client(supabase_url, supabase_key)
    
    # Read migration file
    migration_path = "/home/iris/code/experimental/nfl-predictor-api/supabase/migrations/031_historical_player_stats.sql"
    
    try:
        with open(migration_path, 'r') as f:
            migration_sql = f.read()
        
        print("📋 Applying migration...")
        
        # Execute the migration (note: this requires service role key for DDL)
        # For now, let's try with the anon key - if it fails, user needs to run this in Supabase dashboard
        try:
            response = supabase.rpc('exec_sql', {'sql': migration_sql}).execute()
            print("✅ Migration applied successfully!")
            return True
        except Exception as e:
            print(f"⚠️ Could not apply migration automatically: {e}")
            print("📋 Please manually run the following SQL in your Supabase dashboard:")
            print("=" * 60)
            print(migration_sql)
            print("=" * 60)
            return False
            
    except Exception as e:
        print(f"❌ Error reading migration file: {e}")
        return False

if __name__ == "__main__":
    success = run_migration()
    if not success:
        print("\n💡 To apply the migration manually:")
        print("1. Go to your Supabase dashboard")
        print("2. Navigate to the SQL Editor")
        print("3. Copy and paste the migration SQL from the file above")
        print("4. Run it to create the table")
    sys.exit(0 if success else 1)