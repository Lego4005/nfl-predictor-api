#!/usr/bin/env python3
"""
Verification script for pgvectSW indexes and search_expert_memories RPC
This script validates the first task in the expert council betting system spec.
"""

import os
import sys
import asyncio
import json
from typing import Dict, List, Any, Optional
from datetime import datetime

try:
    from supabase import create_client, Client
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Please ensure you have the required dependencies installed:")
    print("pip install supabase")
    sys.exit(1)

class PgVectorVerifier:
    """Verifies pgvector setup, HNSW indexes, and RPC functions"""

    def __init__(self):
        self.supabase_url = os.getenv('SUPABASE_URL')
        self.supabase_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY') or os.getenv('SUPABASE_ANON_KEY')

        if not self.supabase_url or not self.supabase_key:
            raise ValueError("Missing SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY/SUPABASE_ANON_KEY environment variables")

        self.supabase: Client = create_client(self.supabase_url, self.supabase_key)
        self.results = {}

    async def verify_pgvector_extension(self) -> bool:
        """Check if pgvector extension is installed"""
        try:
            result = self.supabase.rpc('sql', {
                'query': "SELECT extname FROM pg_extension WHERE extname = 'vector';"
            }).execute()

            if result.data and len(result.data) > 0:
                self.results['pgvector_extension'] = {
                    'status': 'success',
                    'message': 'pgvector extension is installed'
                }
                return True
            else:
                self.results['pgvector_extension'] = {
                    'status': 'error',
                    'message': 'pgvector extension not found'
                }
                return False
        except Exception as e:
            self.results['pgvector_extension'] = {
                'status': 'error',
                'message': f'Error checking pgvector extension: {str(e)}'
            }
            return False

    async def verify_hnsw_indexes(self) -> bool:
        """Check if HNSW indexes are present on memory tables"""
        try:
            # Query for HNSW indexes on memory-related tables
            query = """
            SELECT
                schemaname,
                tablename,
                indexname,
                indexdef
            FROM pg_indexes
            WHERE tablename IN ('expert_episodic_memories', 'team_knowledge', 'matchup_memories')
            AND indexdef LIKE '%hnsw%'
            ORDER BY tablename, indexname;
            """

            result = self.supabase.rpc('sql', {'query': query}).execute()

            if result.data and len(result.data) > 0:
                indexes = result.data
                self.results['hnsw_indexes'] = {
                    'status': 'success',
                    'message': f'Found {len(indexes)} HNSW indexes',
                    'indexes': indexes
                }

                # Check for specific required indexes
                required_indexes = [
                    'idx_mem_combined_hnsw',
                    'idx_mem_context_hnsw',
                    'idx_tk_hnsw',
                    'idx_mm_hnsw'
                ]

                found_indexes = [idx['indexname'] for idx in indexes]
                missing_indexes = [idx for idx in required_indexes if idx not in found_indexes]

                if missing_indexes:
                    self.results['hnsw_indexes']['status'] = 'warning'
                    self.results['hnsw_indexes']['missing_indexes'] = missing_indexes

                return True
            else:
                self.results['hnsw_indexes'] = {
                    'status': 'error',
                    'message': 'No HNSW indexes found on memory tables'
                }
                return False

        except Exception as e:
            self.results['hnsw_indexes'] = {
                'status': 'error',
                'message': f'Error checking HNSW indexes: {str(e)}'
            }
            return False

    async def verify_search_expert_memories_rpc(self) -> bool:
        """Check if search_expert_memories RPC function exists and works"""
        try:
            # First check if the function exists
            function_check_query = """
            SELECT
                proname as function_name,
                pg_get_function_arguments(oid) as arguments,
                pg_get_function_result(oid) as return_type
            FROM pg_proc
            WHERE proname = 'search_expert_memories';
            """

            result = self.supabase.rpc('sql', {'query': function_check_query}).execute()

            if not result.data or len(result.data) == 0:
                self.results['search_expert_memories_rpc'] = {
                    'status': 'error',
                    'message': 'search_expert_memories RPC function not found'
                }
                return False

            function_info = result.data[0]

            # Test the function with a sample query
            # First get a sample embedding from existing data
            sample_embedding_query = """
            SELECT combined_embedding
            FROM expert_episodic_memories
            WHERE combined_embedding IS NOT NULL
            LIMIT 1;
            """

            embedding_result = self.supabase.rpc('sql', {'query': sample_embedding_query}).execute()

            if embedding_result.data and len(embedding_result.data) > 0:
                # Test the RPC function
                test_result = self.supabase.rpc('search_expert_memories', {
                    'p_expert_id': 'test_expert',
                    'p_query_embedding': embedding_result.data[0]['combined_embedding'],
                    'p_match_threshold': 0.7,
                    'p_match_count': 5,
                    'p_alpha': 0.8
                }).execute()

                self.results['search_expert_memories_rpc'] = {
                    'status': 'success',
                    'message': 'search_expert_memories RPC function exists and is callable',
                    'function_info': function_info,
                    'test_result_count': len(test_result.data) if test_result.data else 0
                }
                return True
            else:
                # Function exists but no test data
                self.results['search_expert_memories_rpc'] = {
                    'status': 'warning',
                    'message': 'search_expert_memories RPC function exists but no embedding data for testing',
                    'function_info': function_info
                }
                return True

        except Exception as e:
            self.results['search_expert_memories_rpc'] = {
                'status': 'error',
                'message': f'Error testing search_expert_memories RPC: {str(e)}'
            }
            return False

    async def verify_embedding_tables(self) -> bool:
        """Check if memory tables exist with embedding columns"""
        try:
            tables_to_check = [
                'expert_episodic_memories',
                'team_knowledge',
                'matchup_memories'
            ]

            table_results = {}

            for table in tables_to_check:
                # Check if table exists and has embedding columns
                query = f"""
                SELECT
                    column_name,
                    data_type,
                    is_nullable
                FROM information_schema.columns
                WHERE table_name = '{table}'
                AND column_name LIKE '%embedding%'
                ORDER BY column_name;
                """

                result = self.supabase.rpc('sql', {'query': query}).execute()

                if result.data:
                    table_results[table] = {
                        'status': 'success',
                        'embedding_columns': result.data
                    }
                else:
                    table_results[table] = {
                        'status': 'error',
                        'message': f'No embedding columns found in {table}'
                    }

            # Check embedding coverage
            for table in tables_to_check:
                if table_results[table]['status'] == 'success':
                    coverage_query = f"""
                    SELECT
                        COUNT(*) as total_rows,
                        COUNT(CASE WHEN combined_embedding IS NOT NULL THEN 1 END) as with_embeddings,
                        ROUND(
                            COUNT(CASE WHEN combined_embedding IS NOT NULL THEN 1 END)::numeric /
                            NULLIF(COUNT(*), 0) * 100, 2
                        ) as embedding_coverage_percent
                    FROM {table};
                    """

                    coverage_result = self.supabase.rpc('sql', {'query': coverage_query}).execute()

                    if coverage_result.data:
                        table_results[table]['coverage'] = coverage_result.data[0]

            self.results['embedding_tables'] = {
                'status': 'success',
                'message': 'Embedding table verification completed',
                'tables': table_results
            }

            return True

        except Exception as e:
            self.results['embedding_tables'] = {
                'status': 'error',
                'message': f'Error checking embedding tables: {str(e)}'
            }
            return False

    async def verify_performance(self) -> bool:
        """Test performance of vector search"""
        try:
            # Get a sample embedding for performance testing
            sample_query = """
            SELECT combined_embedding
            FROM expert_episodic_memories
            WHERE combined_embedding IS NOT NULL
            LIMIT 1;
            """

            embedding_result = self.supabase.rpc('sql', {'query': sample_query}).execute()

            if not embedding_result.data:
                self.results['performance'] = {
                    'status': 'warning',
                    'message': 'No embedding data available for performance testing'
                }
                return True

            # Test performance with EXPLAIN ANALYZE
            performance_query = f"""
            EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON)
            SELECT * FROM search_expert_memories(
                p_expert_id := 'test_expert',
                p_query_embedding := '{embedding_result.data[0]["combined_embedding"]}',
                p_match_threshold := 0.7,
                p_match_count := 10,
                p_alpha := 0.8
            );
            """

            start_time = datetime.now()
            perf_result = self.supabase.rpc('sql', {'query': performance_query}).execute()
            end_time = datetime.now()

            execution_time_ms = (end_time - start_time).total_seconds() * 1000

            if perf_result.data:
                # Extract execution time from EXPLAIN output
                explain_data = perf_result.data[0]['QUERY PLAN'][0]
                actual_time = explain_data.get('Actual Total Time', 0)

                self.results['performance'] = {
                    'status': 'success' if actual_time < 100 else 'warning',
                    'message': f'Vector search performance test completed',
                    'execution_time_ms': actual_time,
                    'client_time_ms': execution_time_ms,
                    'target_ms': 100,
                    'meets_target': actual_time < 100
                }

                return True
            else:
                self.results['performance'] = {
                    'status': 'error',
                    'message': 'Performance test failed - no results returned'
                }
                return False

        except Exception as e:
            self.results['performance'] = {
                'status': 'error',
                'message': f'Error during performance testing: {str(e)}'
            }
            return False

    async def run_verification(self) -> Dict[str, Any]:
        """Run all verification checks"""
        print("🔍 Starting pgvector and HNSW verification...")

        checks = [
            ("pgvector extension", self.verify_pgvector_extension),
            ("HNSW indexes", self.verify_hnsw_indexes),
            ("search_expert_memories RPC", self.verify_search_expert_memories_rpc),
            ("embedding tables", self.verify_embedding_tables),
            ("performance", self.verify_performance)
        ]

        for check_name, check_func in checks:
            print(f"  Checking {check_name}...")
            try:
                await check_func()
                status = self.results.get(check_name.replace(' ', '_'), {}).get('status', 'unknown')
                if status == 'success':
                    print(f"  ✅ {check_name}: OK")
                elif status == 'warning':
                    print(f"  ⚠️  {check_name}: Warning")
                else:
                    print(f"  ❌ {check_name}: Error")
            except Exception as e:
                print(f"  ❌ {check_name}: Exception - {str(e)}")
                self.results[check_name.replace(' ', '_')] = {
                    'status': 'error',
                    'message': f'Exception during check: {str(e)}'
                }

        return self.results

    def print_summary(self):
        """Print a summary of all verification results"""
        print("\n" + "="*60)
        print("PGVECTOR VERIFICATION SUMMARY")
        print("="*60)

        total_checks = len(self.results)
        success_count = sum(1 for r in self.results.values() if r.get('status') == 'success')
        warning_count = sum(1 for r in self.results.values() if r.get('status') == 'warning')
        error_count = sum(1 for r in self.results.values() if r.get('status') == 'error')

        print(f"Total checks: {total_checks}")
        print(f"✅ Success: {success_count}")
        print(f"⚠️  Warnings: {warning_count}")
        print(f"❌ Errors: {error_count}")

        print("\nDetailed Results:")
        print("-" * 40)

        for check_name, result in self.results.items():
            status_icon = {
                'success': '✅',
                'warning': '⚠️ ',
                'error': '❌'
            }.get(result.get('status'), '❓')

            print(f"{status_icon} {check_name.replace('_', ' ').title()}")
            print(f"   {result.get('message', 'No message')}")

            # Print additional details for specific checks
            if check_name == 'hnsw_indexes' and 'indexes' in result:
                print(f"   Found indexes: {len(result['indexes'])}")
                for idx in result['indexes']:
                    print(f"     - {idx['indexname']} on {idx['tablename']}")

            if check_name == 'embedding_tables' and 'tables' in result:
                for table_name, table_info in result['tables'].items():
                    if 'coverage' in table_info:
                        coverage = table_info['coverage']
                        print(f"   {table_name}: {coverage['with_embeddings']}/{coverage['total_rows']} rows ({coverage['embedding_coverage_percent']}%)")

            if check_name == 'performance' and 'execution_time_ms' in result:
                time_ms = result['execution_time_ms']
                target_ms = result.get('target_ms', 100)
                meets_target = result.get('meets_target', False)
                status_text = "PASS" if meets_target else "SLOW"
                print(f"   Execution time: {time_ms:.2f}ms (target: <{target_ms}ms) [{status_text}]")

            print()

        # Overall assessment
        if error_count == 0:
            if warning_count == 0:
                print("🎉 ALL CHECKS PASSED! pgvector setup is ready for production.")
            else:
                print("✅ Setup is functional with minor warnings. Review warnings above.")
        else:
            print("❌ SETUP INCOMPLETE. Please address the errors above before proceeding.")

        return error_count == 0

async def main():
    """Main verification function"""
    try:
        verifier = PgVectorVerifier()
        results = await verifier.run_verification()

        # Print summary
        success = verifier.print_summary()

        # Save results to file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        results_file = f"pgvector_verification_{timestamp}.json"

        with open(results_file, 'w') as f:
            json.dump({
                'timestamp': timestamp,
                'results': results,
                'summary': {
                    'total_checks': len(results),
                    'success_count': sum(1 for r in results.values() if r.get('status') == 'success'),
                    'warning_count': sum(1 for r in results.values() if r.get('status') == 'warning'),
                    'error_count': sum(1 for r in results.values() if r.get('status') == 'error'),
                    'overall_success': success
                }
            }, f, indent=2, default=str)

        print(f"\n📄 Detailed results saved to: {results_file}")

        # Exit with appropriate code
        sys.exit(0 if success else 1)

    except Exception as e:
        print(f"❌ Verification failed with exception: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
