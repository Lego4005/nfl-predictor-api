#!/usr/bin/env python3
"""
Check what expert IDs exist in the database
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

def check_database_experts():
    """Check what expert IDs are in the database"""

    supabase = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_ANON_KEY'))

    print("🔍 CHECKING DATABASE EXPERT IDs")
    print("=" * 50)

    # Check personality_experts table
    try:
        response = supabase.table('personality_experts').select('*').execute()
        experts = response.data

        print(f"✅ Found {len(experts)} experts in personality_experts table:")
        print("-" * 30)

        for expert in experts:
            expert_id = expert.get('expert_id', 'N/A')
            name = expert.get('name', 'N/A')
            print(f"  {expert_id} → {name}")

        return [expert['expert_id'] for expert in experts]

    except Exception as e:
        print(f"❌ Error checking personality_experts: {e}")
        return []

def check_existing_memories():
    """Check existing memories to see what expert IDs are used"""

    supabase = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_ANON_KEY'))

    try:
        response = supabase.table('expert_episodic_memories').select('expert_id').execute()
        memories = response.data

        expert_ids = list(set([memory['expert_id'] for memory in memories]))

        print(f"\\n📊 Expert IDs with existing memories:")
        print("-" * 30)
        for expert_id in sorted(expert_ids):
            count = sum(1 for m in memories if m['expert_id'] == expert_id)
            print(f"  {expert_id} → {count} memories")

        return expert_ids

    except Exception as e:
        print(f"❌ Error checking memories: {e}")
        return []

if __name__ == "__main__":
    db_experts = check_database_experts()
    memory_experts = check_existing_memories()

    print(f"\\n🎯 SUMMARY:")
    print("-" * 30)
    print(f"Database experts: {len(db_experts)}")
    print(f"Memory experts: {len(memory_experts)}")

    if db_experts:
        print(f"\\n💡 Use these expert IDs for training:")
        for expert_id in db_experts:
            print(f"  '{expert_id}'")
    else:
        print(f"\\n⚠️ No experts found in database - need to create them first")
