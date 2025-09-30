#!/bin/bash
# Quick test to verify schema is ready

echo "🔍 Quick Schema Test"
echo ""

echo "1. Testing schema with Python..."
python3 -c "
from supabase import create_client
import os
from dotenv import load_dotenv
load_dotenv()

supabase = create_client(os.getenv('VITE_SUPABASE_URL'), os.getenv('VITE_SUPABASE_ANON_KEY'))

# Test table access
try:
    result = supabase.table('expert_episodic_memories').select('id').limit(1).execute()
    print('   ✅ expert_episodic_memories accessible')
except Exception as e:
    print(f'   ❌ expert_episodic_memories error: {e}')

try:
    result = supabase.table('expert_belief_revisions').select('id').limit(1).execute()
    print('   ✅ expert_belief_revisions accessible')
except Exception as e:
    print(f'   ❌ expert_belief_revisions error: {e}')

try:
    result = supabase.table('expert_learned_principles').select('id').limit(1).execute()
    print('   ✅ expert_learned_principles accessible')
except Exception as e:
    print(f'   ❌ expert_learned_principles error: {e}')
"

echo ""
echo "2. Testing memory storage..."
python3 -c "
from supabase import create_client
import os
import hashlib
from datetime import datetime
from dotenv import load_dotenv
load_dotenv()

supabase = create_client(os.getenv('VITE_SUPABASE_URL'), os.getenv('VITE_SUPABASE_ANON_KEY'))

# Try to insert a test memory
try:
    test_id = hashlib.md5(str(datetime.now().timestamp()).encode()).hexdigest()[:16]

    memory = {
        'memory_id': test_id,
        'expert_id': 'test_quick',
        'game_id': 'test_game_' + test_id,
        'memory_type': 'prediction_outcome',
        'emotional_state': 'satisfaction',
        'prediction_data': {'winner': 'KC', 'confidence': 0.75},
        'actual_outcome': {'winner': 'KC', 'score': '27-20'},
        'emotional_intensity': 0.8,
        'memory_vividness': 0.75
    }

    result = supabase.table('expert_episodic_memories').insert(memory).execute()
    print('   ✅ Memory storage works!')

    # Clean up
    supabase.table('expert_episodic_memories').delete().eq('memory_id', test_id).execute()

except Exception as e:
    print(f'   ❌ Memory storage failed: {e}')
    print('')
    print('   This likely means the schema cache needs to be reloaded.')
    print('   Run in Supabase SQL Editor:')
    print('     NOTIFY pgrst, \\'reload schema\\';')
"

echo ""
echo "Done!"