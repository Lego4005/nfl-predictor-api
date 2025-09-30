#!/usr/bin/env python3
"""Check what tables and columns actually exist in Supabase"""

import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

SUPABASE_URL = os.getenv('VITE_SUPABASE_URL')
SUPABASE_KEY = os.getenv('VITE_SUPABASE_ANON_KEY')

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

print("🔍 Checking Supabase Schema\n")

# Try to query expert_episodic_memories to see what columns exist
try:
    result = supabase.table('expert_episodic_memories').select('*').limit(1).execute()
    print("✅ Table 'expert_episodic_memories' exists")

    if result.data and len(result.data) > 0:
        print(f"\nColumns in table:")
        for key in result.data[0].keys():
            print(f"  • {key}")
    else:
        print("\n📋 Table is empty - trying to get schema from error...")

        # Try to insert with a field we know exists
        try:
            test_insert = supabase.table('expert_episodic_memories').insert({
                'test': 'value'
            }).execute()
        except Exception as e:
            error_str = str(e)
            print(f"\n❌ Insert error (expected): {error_str[:200]}")

except Exception as e:
    error_str = str(e)
    if 'does not exist' in error_str.lower():
        print("❌ Table 'expert_episodic_memories' does NOT exist")
        print("\n⚠️  Migration 011_expert_episodic_memory_system.sql needs to be applied!")
    else:
        print(f"❌ Error: {error_str}")

# Check other tables
print("\n\n🔍 Checking other tables:")

for table in ['expert_reasoning_chains', 'expert_belief_revisions', 'expert_learned_principles']:
    try:
        result = supabase.table(table).select('id').limit(1).execute()
        print(f"✅ {table}: exists")
    except Exception as e:
        if 'does not exist' in str(e).lower():
            print(f"❌ {table}: DOES NOT EXIST")
        else:
            print(f"⚠️  {table}: {str(e)[:100]}")

print("\n\n💡 RECOMMENDATION:")
print("Run migration: supabase/migrations/011_expert_episodic_memory_system.sql")
print("Or apply via Supabase Dashboard: SQL Editor → New Query → Paste migration → Run")