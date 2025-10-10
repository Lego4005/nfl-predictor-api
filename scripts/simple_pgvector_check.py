#!/usr/bin/env python3
"""
Simple verification script for pgvector setup and search_expert_memories RPC
"""

import os
import sys
from datetime import datetime

try:
    from supabase import create_client, Client
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Please install: pip install supabase")
    sys.exit(1)

def main():
    # Load environment variables
    supabase_url = os.getenv('SUPABASE_URL')
    supabase_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY') or os.getenv('SUPABASE_ANON_KEY')

    if not supabase_url or not supabase_key:
        print("❌ Missing SUPABASE_URL or SUPABASE_ANON_KEY environment variables")
        sys.exit(1)

    print("🔍 Verifying pgvector setup and search_expert_memories RPC...")
    print(f"📡 Connecting to: {supabase_url}")

    try:
        supabase: Client = create_client(supabase_url, supabase_key)

        # Test 1: Check if expert_episodic_memories table exists
        print("\n1️⃣ Checking expert_episodic_memories table...")
        try:
            result = supabase.table('expert_episodic_memories').select('id').limit(1).execute()
            print("   ✅ expert_episodic_memories table exists")
            table_exists = True
        except Exception as e:
            print(f"   ❌ expert_episodic_memories table error: {str(e)}")
            table_exists = False

        # Test 2: Check if search_expert_memories RPC function exists
        print("\n2️⃣ Checking search_expert_memories RPC function...")
        try:
            # Create a dummy embedding vector (1536 dimensions of zeros)
            dummy_embedding = [0.0] * 1536

            result = supabase.rpc('search_expert_memories', {
                'p_expert_id': 'test_expert',
                'p_query_embedding': dummy_embedding,
                'p_match_threshold': 0.7,
                'p_match_count': 5,
                'p_alpha': 0.8
            }).execute()

            print("   ✅ search_expert_memories RPC function exists and is callable")
            print(f"   📊 Test query returned {len(result.data) if result.data else 0} results")
            rpc_exists = True
        except Exception as e:
            print(f"   ❌ search_expert_memories RPC error: {str(e)}")
            rpc_exists = False

        # Test 3: Check for vector columns in the table
        print("\n3️⃣ Checking for vector embedding columns...")
        if table_exists:
            try:
                # Try to select vector columns
                result = supabase.table('expert_episodic_memories').select(
                    'id, combined_embedding, game_context_embedding'
                ).limit(1).execute()

                if result.data:
                    row = result.data[0] if result.data else {}
                    has_combined = 'combined_embedding' in row
                    has_context = 'game_context_embedding' in row

                    print(f"   ✅ Vector columns found: combined_embedding={has_combined}, game_context_embedding={has_context}")
                    vector_columns = True
                else:
                    print("   ⚠️  No data in expert_episodic_memories table")
                    vector_columns = True  # Columns exist but no data
            except Exception as e:
                print(f"   ❌ Vector columns error: {str(e)}")
                vector_columns = False
        else:
            vector_columns = False

        # Test 4: Check embedding coverage
        print("\n4️⃣ Checking embedding coverage...")
        if table_exists:
            try:
                # Count total rows and rows with embeddings
                all_rows = supabase.table('expert_episodic_memories').select('id').execute()
                embedded_rows = supabase.table('expert_episodic_memories').select('id').not_.is_('combined_embedding', 'null').execute()

                total_count = len(all_rows.data) if all_rows.data else 0
                embedded_count = len(embedded_rows.data) if embedded_rows.data else 0

                if total_count > 0:
                    coverage_pct = (embedded_count / total_count) * 100
                    print(f"   📊 Embedding coverage: {embedded_count}/{total_count} rows ({coverage_pct:.1f}%)")

                    if coverage_pct >= 80:
                        print("   ✅ Good embedding coverage")
                        embedding_coverage = True
                    elif coverage_pct >= 50:
                        print("   ⚠️  Moderate embedding coverage")
                        embedding_coverage = True
                    else:
                        print("   ❌ Low embedding coverage")
                        embedding_coverage = False
                else:
                    print("   ⚠️  No data in expert_episodic_memories table")
                    embedding_coverage = True  # No data to embed yet
            except Exception as e:
                print(f"   ❌ Embedding coverage error: {str(e)}")
                embedding_coverage = False
        else:
            embedding_coverage = False

        # Test 5: Performance test (if RPC works)
        print("\n5️⃣ Testing search performance...")
        if rpc_exists:
            try:
                import time

                dummy_embedding = [0.1] * 1536  # Slightly different vector

                start_time = time.time()
                result = supabase.rpc('search_expert_memories', {
                    'p_expert_id': 'test_expert',
                    'p_query_embedding': dummy_embedding,
                    'p_match_threshold': 0.5,
                    'p_match_count': 10,
                    'p_alpha': 0.8
                }).execute()
                end_time = time.time()

                execution_time_ms = (end_time - start_time) * 1000

                print(f"   ⏱️  Search execution time: {execution_time_ms:.2f}ms")

                if execution_time_ms < 100:
                    print("   ✅ Excellent performance (< 100ms)")
                    performance_ok = True
                elif execution_time_ms < 500:
                    print("   ⚠️  Acceptable performance (< 500ms)")
                    performance_ok = True
                else:
                    print("   ❌ Slow performance (> 500ms)")
                    performance_ok = False
            except Exception as e:
                print(f"   ❌ Performance test error: {str(e)}")
                performance_ok = False
        else:
            performance_ok = False

        # Summary
        print("\n" + "="*60)
        print("VERIFICATION SUMMARY")
        print("="*60)

        checks = [
            ("Table exists", table_exists),
            ("RPC function works", rpc_exists),
            ("Vector columns present", vector_columns),
            ("Embedding coverage", embedding_coverage),
            ("Performance acceptable", performance_ok)
        ]

        passed = sum(1 for _, status in checks if status)
        total = len(checks)

        for check_name, status in checks:
            icon = "✅" if status else "❌"
            print(f"{icon} {check_name}")

        print(f"\n📊 Overall: {passed}/{total} checks passed")

        if passed == total:
            print("🎉 ALL CHECKS PASSED! pgvector setup is ready.")
            return True
        elif passed >= 3:
            print("⚠️  MOSTLY READY with some issues to address.")
            return True
        else:
            print("❌ SETUP INCOMPLETE. Major issues need to be resolved.")
            return False

    except Exception as e:
        print(f"❌ Connection error: {str(e)}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
