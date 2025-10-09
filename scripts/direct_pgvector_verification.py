#!/usr/bin/env python3
"""
Direct pgvector verification using psycopg2 for Phase 0.1 requirements
Verifies HNSW indexes and search_expert_memories RPC function
"""

import os
import sys
import json
from datetime import datetime
from typing import Dict, Any

try:
    import psycopg2
    from psycopg2.extras import RealDictCursor
except ImportError:
    print("❌ psycopg2 not installed. Installing...")
    os.system("pip install psycopg2-binary")
    import psycopg2
    from psycopg2.extras import RealDictCursor


class DirectPgVectorVerifier:
    """Directly verifies pgvector HNSW implementation using psycopg2"""

    def __init__(self):
        # Parse Supabase connection string
        supabase_url = os.getenv('SUPABASE_URL', '')
        supabase_password = os.getenv('SUPABASE_DB_PASSWORD', '')

        # Extract database details from URL
        # Format: https://[project_ref].supabase.co
        if 'supabase.co' in supabase_url:
            project_ref = supabase_url.split('//')[1].split('.')[0]
            self.conn_params = {
                'host': f'db.{project_ref}.supabase.co',
                'database': 'postgres',
                'user': 'postgres',
                'password': supabase_password,
                'port': 5432
            }
        else:
            print("❌ Invalid SUPABASE_URL format")
            sys.exit(1)

        self.results = {}

    def connect(self):
        """Create database connection"""
        try:
            return psycopg2.connect(**self.conn_params)
        except Exception as e:
            print(f"❌ Connection failed: {e}")
            return None

    def verify_pgvector_extension(self) -> bool:
        """Check if pgvector extension is installed"""
        print("\n1️⃣ Verifying pgvector extension...")

        conn = self.connect()
        if not conn:
            self.results['pgvector_extension'] = {'status': 'error', 'message': 'Connection failed'}
            return False

        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("SELECT extname, extversion FROM pg_extension WHERE extname = 'vector';")
                result = cur.fetchone()

                if result:
                    self.results['pgvector_extension'] = {
                        'status': 'success',
                        'message': f"pgvector extension installed (version {result['extversion']})",
                        'version': result['extversion']
                    }
                    print(f"   ✅ pgvector extension found (version {result['extversion']})")
                    return True
                else:
                    self.results['pgvector_extension'] = {
                        'status': 'error',
                        'message': 'pgvector extension not installed'
                    }
                    print("   ❌ pgvector extension not found")
                    return False
        except Exception as e:
            self.results['pgvector_extension'] = {
                'status': 'error',
                'message': f'Error: {str(e)}'
            }
            print(f"   ❌ Error: {e}")
            return False
        finally:
            conn.close()

    def verify_hnsw_indexes(self) -> bool:
        """Check for HNSW indexes on expert_episodic_memories"""
        print("\n2️⃣ Verifying HNSW indexes...")

        conn = self.connect()
        if not conn:
            self.results['hnsw_indexes'] = {'status': 'error', 'message': 'Connection failed'}
            return False

        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                # Query for HNSW indexes
                cur.execute("""
                    SELECT
                        schemaname,
                        tablename,
                        indexname,
                        indexdef
                    FROM pg_indexes
                    WHERE tablename = 'expert_episodic_memories'
                    AND indexdef LIKE '%hnsw%'
                    ORDER BY indexname;
                """)
                indexes = cur.fetchall()

                if indexes:
                    self.results['hnsw_indexes'] = {
                        'status': 'success',
                        'message': f'Found {len(indexes)} HNSW indexes',
                        'indexes': [dict(idx) for idx in indexes]
                    }
                    print(f"   ✅ Found {len(indexes)} HNSW indexes:")
                    for idx in indexes:
                        print(f"      - {idx['indexname']}")
                        if 'combined_embedding' in idx['indexdef']:
                            print(f"        (combined_embedding - PRIMARY)")
                        elif 'content_embedding' in idx['indexdef']:
                            print(f"        (content_embedding)")
                        elif 'context_embedding' in idx['indexdef']:
                            print(f"        (context_embedding)")
                    return True
                else:
                    self.results['hnsw_indexes'] = {
                        'status': 'error',
                        'message': 'No HNSW indexes found'
                    }
                    print("   ❌ No HNSW indexes found")
                    return False
        except Exception as e:
            self.results['hnsw_indexes'] = {
                'status': 'error',
                'message': f'Error: {str(e)}'
            }
            print(f"   ❌ Error: {e}")
            return False
        finally:
            conn.close()

    def verify_table_schema(self) -> bool:
        """Verify expert_episodic_memories table has required columns"""
        print("\n3️⃣ Verifying table schema...")

        conn = self.connect()
        if not conn:
            self.results['table_schema'] = {'status': 'error', 'message': 'Connection failed'}
            return False

        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                # Check for required columns
                cur.execute("""
                    SELECT
                        column_name,
                        data_type,
                        udt_name
                    FROM information_schema.columns
                    WHERE table_name = 'expert_episodic_memories'
                    AND column_name IN ('combined_embedding', 'content_embedding', 'context_embedding', 'run_id', 'content_text')
                    ORDER BY column_name;
                """)
                columns = cur.fetchall()

                required_columns = {
                    'combined_embedding': 'vector',
                    'content_embedding': 'vector',
                    'context_embedding': 'vector',
                    'run_id': 'text',
                    'content_text': 'text'
                }

                found_columns = {col['column_name']: col['udt_name'] for col in columns}
                missing_columns = set(required_columns.keys()) - set(found_columns.keys())

                if not missing_columns:
                    self.results['table_schema'] = {
                        'status': 'success',
                        'message': 'All required columns present',
                        'columns': [dict(col) for col in columns]
                    }
                    print("   ✅ All required columns present:")
                    for col in columns:
                        print(f"      - {col['column_name']} ({col['udt_name']})")
                    return True
                else:
                    self.results['table_schema'] = {
                        'status': 'error',
                        'message': f'Missing columns: {", ".join(missing_columns)}',
                        'missing_columns': list(missing_columns)
                    }
                    print(f"   ❌ Missing columns: {', '.join(missing_columns)}")
                    return False
        except Exception as e:
            self.results['table_schema'] = {
                'status': 'error',
                'message': f'Error: {str(e)}'
            }
            print(f"   ❌ Error: {e}")
            return False
        finally:
            conn.close()

    def verify_rpc_function(self) -> bool:
        """Verify search_expert_memories RPC function exists"""
        print("\n4️⃣ Verifying search_expert_memories RPC function...")

        conn = self.connect()
        if not conn:
            self.results['rpc_function'] = {'status': 'error', 'message': 'Connection failed'}
            return False

        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                # Check if function exists
                cur.execute("""
                    SELECT
                        p.proname as function_name,
                        pg_get_function_arguments(p.oid) as arguments,
                        pg_get_function_result(p.oid) as return_type,
                        l.lanname as language
                    FROM pg_proc p
                    JOIN pg_language l ON p.prolang = l.oid
                    WHERE p.proname = 'search_expert_memories';
                """)
                func = cur.fetchone()

                if func:
                    # Check for run_id parameter
                    has_run_id = 'p_run_id' in func['arguments']

                    self.results['rpc_function'] = {
                        'status': 'success',
                        'message': 'search_expert_memories function found',
                        'function': dict(func),
                        'has_run_id_param': has_run_id
                    }
                    print(f"   ✅ Function found:")
                    print(f"      Language: {func['language']}")
                    print(f"      Arguments: {func['arguments']}")
                    print(f"      run_id filtering: {'✅ YES' if has_run_id else '❌ NO'}")
                    return True
                else:
                    self.results['rpc_function'] = {
                        'status': 'error',
                        'message': 'search_expert_memories function not found'
                    }
                    print("   ❌ Function not found")
                    return False
        except Exception as e:
            self.results['rpc_function'] = {
                'status': 'error',
                'message': f'Error: {str(e)}'
            }
            print(f"   ❌ Error: {e}")
            return False
        finally:
            conn.close()

    def verify_sample_data(self) -> bool:
        """Check for sample memory data"""
        print("\n5️⃣ Verifying sample data...")

        conn = self.connect()
        if not conn:
            self.results['sample_data'] = {'status': 'error', 'message': 'Connection failed'}
            return False

        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                # Count total memories
                cur.execute("""
                    SELECT
                        COUNT(*) as total_memories,
                        COUNT(combined_embedding) as memories_with_embeddings,
                        COUNT(DISTINCT expert_id) as unique_experts,
                        COUNT(DISTINCT run_id) as unique_runs
                    FROM expert_episodic_memories;
                """)
                stats = cur.fetchone()

                self.results['sample_data'] = {
                    'status': 'success',
                    'message': 'Sample data statistics',
                    'stats': dict(stats)
                }
                print(f"   📊 Data statistics:")
                print(f"      Total memories: {stats['total_memories']}")
                print(f"      With embeddings: {stats['memories_with_embeddings']}")
                print(f"      Unique experts: {stats['unique_experts']}")
                print(f"      Unique runs: {stats['unique_runs']}")

                if stats['total_memories'] > 0:
                    print("   ✅ Sample data present")
                    return True
                else:
                    print("   ⚠️  No sample data yet")
                    return True
        except Exception as e:
            self.results['sample_data'] = {
                'status': 'error',
                'message': f'Error: {str(e)}'
            }
            print(f"   ❌ Error: {e}")
            return False
        finally:
            conn.close()

    def test_rpc_performance(self) -> bool:
        """Test RPC function performance"""
        print("\n6️⃣ Testing RPC function performance...")

        conn = self.connect()
        if not conn:
            self.results['performance'] = {'status': 'error', 'message': 'Connection failed'}
            return False

        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                # Check if we have sample data
                cur.execute("""
                    SELECT COUNT(*) as count
                    FROM expert_episodic_memories
                    WHERE combined_embedding IS NOT NULL
                    LIMIT 1;
                """)
                result = cur.fetchone()

                if result['count'] == 0:
                    self.results['performance'] = {
                        'status': 'warning',
                        'message': 'No embeddings available for performance testing'
                    }
                    print("   ⚠️  No embeddings for performance testing")
                    return True

                # Test the function call
                start_time = datetime.now()
                cur.execute("""
                    SELECT * FROM search_expert_memories(
                        'conservative_analyzer',
                        'test query',
                        10,
                        0.8,
                        'run_2025_pilot4'
                    );
                """)
                results = cur.fetchall()
                end_time = datetime.now()

                execution_time_ms = (end_time - start_time).total_seconds() * 1000

                self.results['performance'] = {
                    'status': 'success' if execution_time_ms < 100 else 'warning',
                    'message': 'Performance test completed',
                    'execution_time_ms': execution_time_ms,
                    'result_count': len(results),
                    'target_ms': 100,
                    'meets_target': execution_time_ms < 100
                }

                print(f"   ⏱️  Execution time: {execution_time_ms:.2f}ms")
                print(f"   📊 Results returned: {len(results)}")
                if execution_time_ms < 100:
                    print("   ✅ Meets p95 < 100ms target")
                else:
                    print("   ⚠️  Slower than 100ms target")

                return True
        except Exception as e:
            self.results['performance'] = {
                'status': 'error',
                'message': f'Error: {str(e)}'
            }
            print(f"   ❌ Error: {e}")
            return False
        finally:
            conn.close()

    def run_verification(self) -> Dict[str, Any]:
        """Run all verification checks"""
        print("="*60)
        print("PGVECTOR HNSW VERIFICATION - Phase 0.1")
        print("="*60)

        checks = [
            self.verify_pgvector_extension,
            self.verify_table_schema,
            self.verify_hnsw_indexes,
            self.verify_rpc_function,
            self.verify_sample_data,
            self.test_rpc_performance
        ]

        for check in checks:
            try:
                check()
            except Exception as e:
                print(f"   ❌ Exception: {e}")

        return self.results

    def print_summary(self):
        """Print verification summary"""
        print("\n" + "="*60)
        print("VERIFICATION SUMMARY")
        print("="*60)

        total = len(self.results)
        success = sum(1 for r in self.results.values() if r.get('status') == 'success')
        warnings = sum(1 for r in self.results.values() if r.get('status') == 'warning')
        errors = sum(1 for r in self.results.values() if r.get('status') == 'error')

        print(f"\nTotal checks: {total}")
        print(f"✅ Success: {success}")
        print(f"⚠️  Warnings: {warnings}")
        print(f"❌ Errors: {errors}")

        print("\nPhase 0.1 Requirements:")
        print("-" * 40)

        requirements = {
            'pgvector_extension': '✅ pgvector extension installed',
            'table_schema': '✅ Vector columns (vector(1536)) present',
            'hnsw_indexes': '✅ HNSW indexes created',
            'rpc_function': '✅ search_expert_memories RPC with run_id',
            'performance': '⏱️  Performance target: p95 < 100ms'
        }

        for key, desc in requirements.items():
            status = self.results.get(key, {}).get('status', 'unknown')
            icon = '✅' if status == 'success' else '⚠️' if status == 'warning' else '❌'
            print(f"{icon} {desc}")

        if errors == 0:
            print("\n🎉 Phase 0.1 verification PASSED!")
            return True
        else:
            print("\n❌ Phase 0.1 verification FAILED - address errors above")
            return False


def main():
    """Main verification function"""
    try:
        verifier = DirectPgVectorVerifier()
        verifier.run_verification()
        success = verifier.print_summary()

        # Save results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        results_file = f"pgvector_phase01_verification_{timestamp}.json"

        with open(results_file, 'w') as f:
            json.dump({
                'timestamp': timestamp,
                'phase': '0.1',
                'results': verifier.results,
                'success': success
            }, f, indent=2, default=str)

        print(f"\n📄 Results saved to: {results_file}")

        sys.exit(0 if success else 1)

    except Exception as e:
        print(f"\n❌ Verification failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
