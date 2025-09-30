#!/usr/bin/env python3
"""
Check actual columns in Supabase tables
"""

import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

supabase = create_client(os.getenv('VITE_SUPABASE_URL'), os.getenv('VITE_SUPABASE_ANON_KEY'))

print("🔍 Checking Actual Table Columns")
print("=" * 60)

tables_to_check = [
    'expert_episodic_memories',
    'expert_belief_revisions',
    'expert_learned_principles'
]

for table in tables_to_check:
    print(f"\n📋 {table}:")
    print("-" * 60)

    # Try inserting empty data to see what columns are required
    try:
        result = supabase.table(table).insert({}).execute()
    except Exception as e:
        error_msg = str(e)
        print(f"Error (expected): {error_msg}")

        # Parse column names from error if possible
        if "Could not find" in error_msg and "column" in error_msg:
            print("\n⚠️  Schema cache issue detected")
        elif "null value" in error_msg or "violates" in error_msg:
            print("\n✅ Table structure exists (columns validated)")

print("\n" + "=" * 60)
print("\n💡 Recommendation:")
print("   The tables exist but columns may not be in PostgREST cache.")
print("   Run: NOTIFY pgrst, 'reload schema';")