#!/usr/bin/env python3
"""
Fix team data in existing memories by extracting from contextual_factors
"""
import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

def fix_team_data():
    """Extract team data from contextual_factors and update home_team/away_team columns"""

    supabase = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_ANON_KEY'))

    print("🔧 Fixing team data in existing memories...")

    # Get all memories that need team data extraction
    result = supabase.table('expert_episodic_memories').select(
        'memory_id, contextual_factors, home_team, away_team'
    ).is_('home_team', 'null').execute()

    memories_to_fix = result.data
    print(f"📊 Found {len(memories_to_fix)} memories to fix")

    fixed_count = 0

    for memory in memories_to_fix:
        memory_id = memory['memory_id']
        contextual_factors = memory.get('contextual_factors', [])

        # Extract team data
        home_team = None
        away_team = None

        for factor in contextual_factors:
            if isinstance(factor, dict):
                if factor.get('factor') == 'home_team':
                    home_team = factor.get('value')
                elif factor.get('factor') == 'away_team':
                    away_team = factor.get('value')

        # Update if we found team data
        if home_team or away_team:
            update_data = {}
            if home_team:
                update_data['home_team'] = home_team
            if away_team:
                update_data['away_team'] = away_team

            try:
                supabase.table('expert_episodic_memories').update(update_data).eq('memory_id', memory_id).execute()
                fixed_count += 1
                print(f"✅ Fixed {memory_id[:8]}... | {away_team} @ {home_team}")
            except Exception as e:
                print(f"❌ Failed to fix {memory_id[:8]}...: {e}")

    print(f"\n🎉 Fixed {fixed_count}/{len(memories_to_fix)} memories")

    # Verify the fix
    result = supabase.table('expert_episodic_memories').select(
        'memory_id, home_team, away_team, embedding_status'
    ).not_.is_('home_team', 'null').limit(5).execute()

    print(f"\n📊 Sample of fixed memories:")
    for mem in result.data:
        print(f"   {mem['memory_id'][:8]}... | {mem['away_team']} @ {mem['home_team']} | {mem['embedding_status']}")

if __name__ == "__main__":
    fix_team_data()
