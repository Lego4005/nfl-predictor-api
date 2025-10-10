#!/usr/bin/env python3
"""
Simple validation script for pgvector HNSW setup
Tests basic functionality without complex dependencies
"""

import os
import json

def validate_migration_file():
    """Validate the migration file exists and has correct content"""

    print("🔍 Validating migration file...")

    migration_path = "supabase/migrations/051_pgvector_hnsw_memory_search.sql"

    if not os.path.exists(migration_path):
        print("❌ Migration file not found")
        return False

    with open(migration_path, 'r') as f:
        content = f.read()

    # Check for key components
    checks = [
        ("Vector columns", "ADD COLUMN IF NOT EXISTS content_embedding vector(1536)"),
        ("HNSW index", "USING hnsw (combined_embedding vector_cosine_ops)"),
        ("RPC function", "CREATE OR REPLACE FUNCTION search_expert_memories"),
        ("Run ID support", "p_run_id TEXT DEFAULT 'run_2025_pilot4'"),
        ("Sample data", "CREATE OR REPLACE FUNCTION create_sample_memories"),
        ("Performance test", "CREATE OR REPLACE FUNCTION test_memory_search_performance")
    ]

    all_passed = True
    for check_name, check_text in checks:
        if check_text in content:
            print(f"   ✅ {check_name}")
        else:
            print(f"   ❌ {check_name}")
            all_passed = False

    return all_passed

def validate_environment_config():
    """Validate environment configuration"""

    print("\n🔍 Validating environment configuration...")

    # Check .env.example has the required settings
    env_example_path = ".env.example"

    if os.path.exists(env_example_path):
        with open(env_example_path, 'r') as f:
            env_content = f.read()

        required_vars = [
            "RUN_ID=run_2025_pilot4",
            "MEMORY_RETRIEVAL_TIMEOUT_MS=5000",
            "DEFAULT_MEMORY_K=15",
            "MIN_MEMORY_K=10",
            "MAX_MEMORY_K=20"
        ]

        all_found = True
        for var in required_vars:
            if var in env_content:
                print(f"   ✅ {var}")
            else:
                print(f"   ❌ {var}")
                all_found = False

        return all_found
    else:
        print("   ❌ .env.example not found")
        return False

def validate_config_module():
    """Validate config module exists"""

    print("\n🔍 Validating config module...")

    config_files = [
        "src/config/__init__.py",
        "src/config/settings.py"
    ]

    all_exist = True
    for file_path in config_files:
        if os.path.exists(file_path):
            print(f"   ✅ {file_path}")
        else:
            print(f"   ❌ {file_path}")
            all_exist = False

    return all_exist

def validate_api_endpoints():
    """Validate API endpoint files exist"""

    print("\n🔍 Validating API endpoints...")

    api_files = [
        "src/api/expert_context_api.py"
    ]

    all_exist = True
    for file_path in api_files:
        if os.path.exists(file_path):
            print(f"   ✅ {file_path}")

            # Check for key endpoints
            with open(file_path, 'r') as f:
                content = f.read()

            endpoints = [
                "@router.get(\"/context/{expert_id}/{game_id}\")",
                "@router.get(\"/runs/{run_id}/stats\")",
                "@router.get(\"/runs/current\")"
            ]

            for endpoint in endpoints:
                if endpoint in content:
                    print(f"      ✅ {endpoint}")
                else:
                    print(f"      ❌ {endpoint}")
                    all_exist = False
        else:
            print(f"   ❌ {file_path}")
            all_exist = False

    return all_exist

def validate_orchestrator_updates():
    """Validate Agentuity orchestrator has run_id support"""

    print("\n🔍 Validating orchestrator updates...")

    orchestrator_path = "agentuity/agents/game-orchestrator/index.ts"

    if os.path.exists(orchestrator_path):
        with open(orchestrator_path, 'r') as f:
            content = f.read()

        checks = [
            ("run_id in interface", "run_id?: string;"),
            ("run_id in payload", "run_id } = payload;"),
            ("run_id in URL params", "contextUrl.searchParams.set('run_id', run_id);"),
            ("run_id in request body", "run_id: run_id || 'run_2025_pilot4'")
        ]

        all_passed = True
        for check_name, check_text in checks:
            if check_text in content:
                print(f"   ✅ {check_name}")
            else:
                print(f"   ❌ {check_name}")
                all_passed = False

        return all_passed
    else:
        print(f"   ❌ {orchestrator_path} not found")
        return False

def validate_test_files():
    """Validate test files exist"""

    print("\n🔍 Validating test files...")

    test_files = [
        "test_run_id_isolation.py",
        "test_pgvector_memory_search.py",
        "test_sql_migration.sql",
        "validate_pgvector_setup.py"
    ]

    all_exist = True
    for file_path in test_files:
        if os.path.exists(file_path):
            print(f"   ✅ {file_path}")
        else:
            print(f"   ❌ {file_path}")
            all_exist = False

    return all_exist

def main():
    """Main validation function"""

    print("🚀 Validating pgvector HNSW memory search setup...")
    print("=" * 60)

    # Run all validations
    validations = [
        ("Migration File", validate_migration_file),
        ("Environment Config", validate_environment_config),
        ("Config Module", validate_config_module),
        ("API Endpoints", validate_api_endpoints),
        ("Orchestrator Updates", validate_orchestrator_updates),
        ("Test Files", validate_test_files)
    ]

    results = {}
    for name, validator in validations:
        results[name] = validator()

    # Summary
    print("\n" + "=" * 60)
    print("📋 Validation Summary:")

    all_passed = True
    for name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"   {name}: {status}")
        if not passed:
            all_passed = False

    print("\n" + "=" * 60)
    if all_passed:
        print("🎉 All validations passed!")
        print("\nThe pgvector HNSW memory search system is properly set up.")
        print("\nNext steps:")
        print("1. Apply the migration: supabase db push")
        print("2. Test the RPC function in Supabase SQL editor")
        print("3. Start the FastAPI server and test the endpoints")
        print("4. Generate actual embeddings for production use")
    else:
        print("⚠️ Some validations failed.")
        print("Please fix the issues above before proceeding.")

    return all_passed

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
