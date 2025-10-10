#!/usr/bin/env python3
"""
4-Expert Pilot Readiness Audit
5-minute sanity check before starting ingestion
"""

import os
import json
import asyncio
from pathlib import Path
import httpx

def check_file_exists(path: str, description: str) -> bool:
    """Check if required file exists"""
    if os.path.exists(path):
        print(f"✅ {description}: {path}")
        return True
    else:
        print(f"❌ {description}: {path} - NOT FOUND")
        return False

def check_service_running(url: str, service_name: str) -> bool:
    """Check if service is running"""
    try:
        import requests
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            print(f"✅ {service_name}: {url} - RUNNING")
            return True
        else:
            print(f"⚠️ {service_name}: {url} - HTTP {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ {service_name}: {url} - NOT ACCESSIBLE ({e})")
        return False

async def check_neo4j_run_scope():
    """Check Neo4j run scope setup"""
    try:
        from neo4j import GraphDatabase
        driver = GraphDatabase.driver('bolt://localhost:7688', auth=('neo4j', 'nflpredictor123'))

        with driver.session() as session:
            result = session.run('MATCH (r:Run {run_id: "run_2025_pilot4"}) RETURN r.experts AS experts')
            record = result.single()
            if record:
                experts = record['experts']
                print(f"✅ Neo4j Run Scope: run_2025_pilot4 with experts {experts}")
                return True
            else:
                print("❌ Neo4j Run Scope: run_2025_pilot4 not found")
                return False

        driver.close()
    except Exception as e:
        print(f"❌ Neo4j Run Scope: Error - {e}")
        return False

def main():
    """Run complete readiness audit"""
    print("=== 4-EXPERT PILOT READINESS AUDIT ===")
    print()

    # Track results
    checks_passed = 0
    total_checks = 0

    # 1. Core configuration files
    print("1. Configuration Files:")
    total_checks += 4
    if check_file_exists("config/category_registry.json", "Category Registry (83 categories)"): checks_passed += 1
    if check_file_exists("schemas/expert_predictions_v1.schema.json", "Expert Predictions Schema"): checks_passed += 1
    if check_file_exists("src/services/memory_retrieval_service.py", "Memory Retrieval Service"): checks_passed += 1
    if check_file_exists(".env", "Environment Configuration"): checks_passed += 1
    print()

    # 2. Environment variables
    print("2. Environment Variables:")
    total_checks += 3
    run_id = os.getenv("RUN_ID")
    if run_id:
        print(f"✅ RUN_ID: {run_id}")
        checks_passed += 1
    else:
        print("❌ RUN_ID: Not set")

    supabase_url = os.getenv("SUPABASE_URL")
    if supabase_url:
        print(f"✅ SUPABASE_URL: {supabase_url[:50]}...")
        checks_passed += 1
    else:
        print("❌ SUPABASE_URL: Not set")

    neo4j_uri = os.getenv("NEO4J_URI")
    if neo4j_uri:
        print(f"✅ NEO4J_URI: {neo4j_uri}")
        checks_passed += 1
    else:
        print("❌ NEO4J_URI: Not set")
    print()

    # 3. Services running
    print("3. Services Status:")
    total_checks += 2
    if check_service_running("http://localhost:3000/health", "Agentuity Orchestrator"): checks_passed += 1
    # Neo4j check
    try:
        import socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        result = sock.connect_ex(('localhost', 7688))
        if result == 0:
            print("✅ Neo4j Service: localhost:7688 - RUNNING")
            checks_passed += 1
        else:
            print("❌ Neo4j Service: localhost:7688 - NOT RUNNING")
        sock.close()
    except Exception as e:
        print(f"❌ Neo4j Service: Error - {e}")
    print()

    # 4. Neo4j run scope
    print("4. Neo4j Run Scope:")
    total_checks += 1
    if asyncio.run(check_neo4j_run_scope()): checks_passed += 1
    print()

    # 5. 4 Expert Agents (check if they exist in Agentuity)
    print("5. Expert Agents:")
    pilot_experts = ["conservative_analyzer", "momentum_rider", "contrarian_rebel", "value_hunter"]

    # Check if agent files exist
    for expert in pilot_experts:
        total_checks += 1
        agent_path = f"agentuity/pickiq/src/agents/{expert.replace('_', '-')}/index.ts"
        if check_file_exists(agent_path, f"{expert} Agent"): checks_passed += 1
    print()

    # 6. Category registry content
    print("6. Category Registry Content:")
    total_checks += 1
    try:
        with open("config/category_registry.json", "r") as f:
            categories = json.load(f)
            if len(categories) >= 83:
                print(f"✅ Category Registry: {len(categories)} categories (≥83 required)")
                checks_passed += 1
            else:
                print(f"⚠️ Category Registry: {len(categories)} categories (<83 required)")
    except Exception as e:
        print(f"❌ Category Registry: Error reading - {e}")
    print()

    # Summary
    print("=== READINESS SUMMARY ===")
    print(f"Checks Passed: {checks_passed}/{total_checks}")
    print(f"Success Rate: {checks_passed/total_checks:.1%}")
    print()

    if checks_passed >= total_checks * 0.8:  # 80% threshold
        print("🎉 READY FOR 4-EXPERT PILOT!")
        print("✅ Sufficient components available to start ingestion")
        print()
        print("Next Steps:")
        print("1. Start pilot API: python src/api/pilot_endpoints.py")
        print("2. Run 2020-2023 ingestion: python scripts/seed_ingest_runner.py")
        print("3. Test with 2024 Week 1-2 baselines")
        return True
    else:
        print("❌ NOT READY - Missing critical components")
        print("Fix the failed checks above before proceeding")
        return False

if __name__ == "__main__":
    main()
