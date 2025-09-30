#!/bin/bash
# Wait for PostgREST schema cache to refresh

echo "⏳ Waiting for PostgREST schema cache to refresh..."
echo ""

MAX_ATTEMPTS=10
ATTEMPT=1

while [ $ATTEMPT -le $MAX_ATTEMPTS ]; do
    echo "Attempt $ATTEMPT/$MAX_ATTEMPTS..."

    # Try the quick test
    if python3 -c "
from supabase import create_client
import os
import hashlib
from datetime import datetime
from dotenv import load_dotenv
load_dotenv()

supabase = create_client(os.getenv('VITE_SUPABASE_URL'), os.getenv('VITE_SUPABASE_ANON_KEY'))

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
    supabase.table('expert_episodic_memories').delete().eq('memory_id', test_id).execute()
    exit(0)  # Success
except Exception as e:
    if 'schema cache' in str(e).lower():
        exit(1)  # Cache still stale
    else:
        exit(2)  # Other error
" 2>/dev/null; then
        echo ""
        echo "✅ Schema cache is refreshed!"
        echo ""
        exit 0
    fi

    if [ $ATTEMPT -eq $MAX_ATTEMPTS ]; then
        echo ""
        echo "❌ Schema cache still not refreshed after $MAX_ATTEMPTS attempts"
        echo ""
        echo "Please restart your Supabase database:"
        echo "  1. Go to: https://supabase.com/dashboard"
        echo "  2. Navigate to: Settings → Database"
        echo "  3. Click: 'Restart database'"
        echo "  4. Wait 30 seconds"
        echo "  5. Run: bash scripts/run_memory_tests.sh"
        echo ""
        exit 1
    fi

    # Wait before next attempt
    WAIT_TIME=$((ATTEMPT * 3))
    echo "   Waiting ${WAIT_TIME} seconds before retry..."
    sleep $WAIT_TIME

    ATTEMPT=$((ATTEMPT + 1))
done