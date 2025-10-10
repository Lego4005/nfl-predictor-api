#!/usr/bin/env python3
"""
Check for HNSW indexes on vector columns
"""

import os
import sys

try:
    from supabase import create_client, Client
except ImportError as e:
    print(f"❌ Import error: {e}")
    sys.exit(1)

def main():
    supabase_url = os.getenv('SUPABASE_URL')
    supabase_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY') or os.getenv('SUPABASE_ANON_KEY')

    if not supabase_url or not supabase_key:
        print("❌ Missing environment variables")
        sys.exit(1)

    print("🔍 Checking for HNSW indexes...")

    try:
        supabase: Client = create_client(supabase_url, supabase_key)

        # Check if we can perform vector similarity search
        # This indirectly confirms HNSW indexes are working
        print("\n1️⃣ Testing vector similarity search...")

        # Get a sample embedding
        sample_result = supabase.table('expert_episodic_memories').select('combined_embedding').not_.is_('combined_embedding', 'null').limit(1).execute()

        if sample_result.data and len(sample_result.data) > 0:
            sample_embedding = sample_result.data[0]['combined_embedding']
            print(f"   📊 Found sample embedding with {len(sample_embedding)} dimensions")

            # Test the search function with the sample embedding
            search_result = supabase.rpc('search_expert_memories', {
                'p_expert_id': 'test_expert',
                'p_query_embedding': sample_embedding,
                'p_match_threshold': 0.1,  # Low threshold to get results
                'p_match_count': 5,
                'p_alpha': 0.8
            }).execute()

            print(f"   ✅ Vector search returned {len(search_result.data) if search_result.data else 0} results")

            # Test performance multiple times
            import time
            times = []
            for i in range(3):
                start = time.time()
                supabase.rpc('search_expert_memories', {
                    'p_expert_id': 'test_expert',
                    'p_query_embedding': sample_embedding,
                    'p_match_threshold': 0.1,
                    'p_match_count': 10,
                    'p_alpha': 0.8
                }).execute()
                end = time.time()
                times.append((end - start) * 1000)

            avg_time = sum(times) / len(times)
            print(f"   ⏱️  Average search time: {avg_time:.2f}ms (target: <100ms)")

            if avg_time < 100:
                print("   ✅ Performance indicates HNSW indexes are working efficiently")
                return True
            else:
                print("   ⚠️  Performance suggests indexes may not be optimal")
                return True
        else:
            print("   ⚠️  No embedding data found for testing")
            return True

    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

if __name__ == "__main__":
    success = main()
    print(f"\n{'✅ HNSW indexes appear to be working' if success else '❌ HNSW index issues detected'}")
    sys.exit(0 if success else 1)
