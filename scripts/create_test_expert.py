#!/usr/bin/env python3
"""
Create test expert in database for testing episodic memory system
"""

import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

SUPABASE_URL = os.getenv('VITE_SUPABASE_URL')
SUPABASE_KEY = os.getenv('VITE_SUPABASE_ANON_KEY')

def create_test_expert():
    """Create test expert for memory system testing"""

    print("🔧 Creating test expert...")

    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

    # Test expert data
    expert_data = {
        'expert_id': 'test_conservative_analyzer',
        'name': 'Test Conservative Analyzer',
        'type': 'conservative',
        'description': 'Test expert for episodic memory validation',
        'personality_traits': {
            'risk_tolerance': 'low',
            'confidence_style': 'cautious',
            'analysis_depth': 'thorough'
        }
    }

    try:
        # Check if expert already exists
        existing = supabase.table('expert_models')\
            .select('expert_id')\
            .eq('expert_id', 'test_conservative_analyzer')\
            .execute()

        if existing.data and len(existing.data) > 0:
            print(f"✅ Test expert already exists: {expert_data['expert_id']}")
            return True

        # Create new expert
        result = supabase.table('expert_models').insert(expert_data).execute()

        if result.data:
            print(f"✅ Test expert created successfully: {expert_data['expert_id']}")
            print(f"   Name: {expert_data['name']}")
            print(f"   Type: {expert_data['type']}")
            return True
        else:
            print(f"❌ Failed to create test expert")
            return False

    except Exception as e:
        print(f"❌ Error creating test expert: {e}")

        # If foreign key error, suggest creating base expert
        if 'foreign key' in str(e).lower():
            print("\n💡 Tip: The expert_models table might not exist.")
            print("   Run: python3 scripts/initialize_database.py")

        return False

if __name__ == "__main__":
    success = create_test_expert()
    exit(0 if success else 1)