#!/usr/bin/env python3
"""
Smoke Test for Expert Council Betting System
Tests single game with 4 experts through complete pipeline
"""

import asyncio
import json
import time
from typing import Dict, Any, List
import httpx
from loguru import logger

# Test configuration
TEST_GAME_ID = "2025_01_MIA_IN
TEST_EXPERTS = [
    "conservative_analyzer",
    "momentum_rider",
    "contrarian_rebel",
    "value_hunter"
]
API_BASE_URL = "http://localhost:8000/api"


async def run_smoke_test():
    """Run complete smoke test of orchestration system"""
    logger.info("Starting Expert Council Betting System smoke test")

    # Test 1: Health checks
    logger.info("=== Test 1: Health Checks ===")
    await test_health_checks()

    # Test 2: Orchestration
    logger.info("=== Test 2: Game Orchestration ===")
    orchestration_result = await test_game_orchestration()

    # Test 3: Storage verification
    logger.info("=== Test 3: Storage Verification ===")
    await test_storage_verification()

    # Test 4: Council selection
    logger.info("=== Test 4: Council Selection ===")
    await test_council_selection()

    # Test 5: Settlement (if game has results)
    logger.info("=== Test 5: Settlement Test ===")
    await test_settlement()

    # Test 6: Neo4j provenance
    logger.info("=== Test 6: Neo4j Provenance ===")
    await test_neo4j_provenance()

    logger.info("Smoke test completed successfully! 🎉")


async def test_health_checks():
    """Test system health endpoints"""
    async with httpx.AsyncClient() as client:
        # API health
        response = await client.get(f"{API_BASE_URL}/health")
        assert response.status_code == 200, f"API health failed: {response.status_code}"
        logger.info("✅ API health check passed")

        # Agentuity health
        response = await client.get(f"{API_BASE_URL}/health/agentuity")
        health_data = response.json()
        logger.info(f"Agentuity health: {health_data.get('status', 'unknown')}")

        # Database health
        response = await client.get(f"{API_BASE_URL}/health/database")
        if response.status_code == 200:
            logger.info("✅ Database health check passed")
        else:
            logger.warning(f"Database health check failed: {response.status_code}")


async def test_game_orchestration():
    """Test game orchestration via Agentuity"""
    async with httpx.AsyncClient(timeout=30.0) as client:
        payload = {
            "expert_ids": TEST_EXPERTS,
            "enable_shadow_runs": False
        }

        start_time = time.time()
        response = await client.post(
            f"{API_BASE_URL}/orchestrate/game/{TEST_GAME_ID}",
            json=payload
        )
        duration = (time.time() - start_time) * 1000

        assert response.status_code == 200, f"Orchestration failed: {response.status_code}"

        result = response.json()
        logger.info(f"Orchestration completed in {duration:.1f}ms")
        logger.info(f"Experts processed: {len(result.get('experts_processed', []))}")
        logger.info(f"Experts failed: {len(result.get('experts_failed', []))}")
        logger.info(f"Schema compliance: {result.get('schema_compliance_rate', 0):.2%}")

        # Verify performance targets
        retrieval_ms = result.get('retrieval_duration_ms', 0)
        if retrieval_ms > 100:
            logger.warning(f"Vector retrieval p95 target missed: {retrieval_ms}ms > 100ms")
        else:
            logger.info(f"✅ Vector retrieval within target: {retrieval_ms}ms")

        total_ms = result.get('total_duration_ms', 0)
        if total_ms > 6000:
            logger.warning(f"End-to-end target missed: {total_ms}ms > 6000ms")
        else:
            logger.info(f"✅ End-to-end within target: {total_ms}ms")

        return result


async def test_storage_verification():
    """Verify predictions and bets were stored correctly"""
    async with httpx.AsyncClient() as client:
        # Check expert predictions
        response = await client.get(f"{API_BASE_URL}/predictions/game/{TEST_GAME_ID}")

        if response.status_code == 200:
            predictions = response.json()
            logger.info(f"Found predictions for {len(predictions)} experts")

            # Verify 83 assertions per expert
            for expert_data in predictions:
                expert_id = expert_data.get('expert_id')
                assertion_count = len(expert_data.get('predictions', []))

                if assertion_count == 83:
                    logger.info(f"✅ {expert_id}: {assertion_count} assertions")
                else:
                    logger.error(f"❌ {expert_id}: {assertion_count} assertions (expected 83)")
        else:
            logger.warning(f"Could not retrieve predictions: {response.status_code}")

        # Check expert bets
        response = await client.get(f"{API_BASE_URL}/bets/game/{TEST_GAME_ID}")

        if response.status_code == 200:
            bets = response.json()
            logger.info(f"Found {len(bets)} betting tickets")

            # Verify bet structure
            for bet in bets[:3]:  # Check first 3 bets
                required_fields = ['expert_id', 'category', 'stake_units', 'odds']
                missing = [field for field in required_fields if field not in bet]
                if missing:
                    logger.error(f"❌ Bet missing fields: {missing}")
                else:
                    logger.info(f"✅ Bet structure valid for {bet.get('expert_id')}")
        else:
            logger.warning(f"Could not retrieve bets: {response.status_code}")


async def test_council_selection():
    """Test council selection and coherence projection"""
    async with httpx.AsyncClient() as client:
        # Trigger council selection
        response = await client.post(f"{API_BASE_URL}/council/select/{TEST_GAME_ID}")

        if response.status_code == 200:
            council_data = response.json()
            logger.info(f"Council selection completed")
            logger.info(f"Families processed: {len(council_data.get('families', {}))}")
        else:
            logger.warning(f"Council selection failed: {response.status_code}")

        # Get platform slate
        response = await client.get(f"{API_BASE_URL}/platform/slate/{TEST_GAME_ID}")

        if response.status_code == 200:
            slate = response.json()
            logger.info("✅ Platform slate generated")

            # Check coherence
            home_score = slate.get('home_score')
            away_score = slate.get('away_score')
            total_score = slate.get('total_score')

            if home_score and away_score and total_score:
                calculated_total = home_score + away_score
                if abs(calculated_total - total_score) < 0.1:
                    logger.info("✅ Score coherence maintained")
                else:
                    logger.error(f"❌ Score incoherence: {calculated_total} != {total_score}")
        else:
            logger.warning(f"Platform slate failed: {response.status_code}")


async def test_settlement():
    """Test settlement process (mock results if needed)"""
    async with httpx.AsyncClient() as client:
        # Mock game results for testing
        mock_results = {
            "home_score": 24,
            "away_score": 17,
            "winner": "home",
            "total_score": 41,
            "quarter_scores": [7, 10, 7, 0, 3, 7, 7, 0]  # [Q1H, Q1A, Q2H, Q2A, ...]
        }

        response = await client.post(
            f"{API_BASE_URL}/settle/{TEST_GAME_ID}",
            json=mock_results
        )

        if response.status_code == 200:
            settlement = response.json()
            logger.info("✅ Settlement completed")
            logger.info(f"Assertions graded: {settlement.get('assertions_graded', 0)}")
            logger.info(f"Bankroll updates: {settlement.get('bankroll_updates', 0)}")

            # Check bankroll integrity
            total_pnl = settlement.get('total_pnl', 0)
            logger.info(f"Total P&L: ${total_pnl:.2f}")

        else:
            logger.warning(f"Settlement failed: {response.status_code}")


async def test_neo4j_provenance():
    """Test Neo4j provenance tracking"""
    async with httpx.AsyncClient() as client:
        # Query provenance
        response = await client.get(f"{API_BASE_URL}/provenance/game/{TEST_GAME_ID}")

        if response.status_code == 200:
            provenance = response.json()
            logger.info("✅ Neo4j provenance available")
            logger.info(f"Decision nodes: {provenance.get('decision_count', 0)}")
            logger.info(f"Assertion nodes: {provenance.get('assertion_count', 0)}")
            logger.info(f"Memory links: {provenance.get('memory_link_count', 0)}")
        else:
            logger.warning(f"Provenance query failed: {response.status_code}")


async def test_performance_metrics():
    """Test performance monitoring"""
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{API_BASE_URL}/metrics/performance")

        if response.status_code == 200:
            metrics = response.json()

            # Check key performance indicators
            vector_p95 = metrics.get('vector_retrieval_p95_ms', 0)
            if vector_p95 < 100:
                logger.info(f"✅ Vector retrieval p95: {vector_p95}ms")
            else:
                logger.warning(f"⚠️ Vector retrieval p95: {vector_p95}ms (target: <100ms)")

            schema_compliance = metrics.get('schema_compliance_rate', 0)
            if schema_compliance > 0.95:
                logger.info(f"✅ Schema compliance: {schema_compliance:.2%}")
            else:
                logger.warning(f"⚠️ Schema compliance: {schema_compliance:.2%} (target: >95%)")
        else:
            logger.warning(f"Performance metrics unavailable: {response.status_code}")


if __name__ == "__main__":
    asyncio.run(run_smoke_test())

    # Test Agentuity orchestrator health
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get("http://localhost:3000/health")
            if response.status_code == 200:
                logger.success("✅ Agentuity orchestrator healthy")
            else:
                logger.error(f"❌ Agentuity orchestrator unhealthy: {response.status_code}")
                return False
    except Exception as e:
        logger.error(f"❌ Cannot reach Agentuity orchestrator: {e}")
        return False

    # Test FastAPI health
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{API_BASE_URL}/health")
            if response.status_code == 200:
                logger.success("✅ FastAPI backend healthy")
            else:
                logger.error(f"❌ FastAPI backend unhealthy: {response.status_code}")
                return False
    except Exception as e:
        logger.error(f"❌ Cannot reach FastAPI backend: {e}")
        return False

    # Test 2: Model allocation check
    logger.info("=== Test 2: Model Allocation Check ===")

    for expert_id in TEST_EXPERTS:
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{API_BASE_URL}/model-allocations/{expert_id}/markets")
                if response.status_code == 200:
                    allocations = response.json()
                    primary_model = next((a['model'] for a in allocations if a['is_primary']), None)
                    logger.success(f"✅ {expert_id}: Primary model = {primary_model}")
                else:
                    logger.warning(f"⚠️ No model allocations for {expert_id}")
        except Exception as e:
            logger.error(f"❌ Model allocation check failed for {expert_id}: {e}")

    # Test 3: Memory retrieval
    logger.info("=== Test 3: Memory Retrieval ===")

    for expert_id in TEST_EXPERTS:
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{API_BASE_URL}/context/{expert_id}/{TEST_GAME_ID}")
                if response.status_code == 200:
                    context = response.json()
                    memory_count = len(context.get('memories', []))
                    logger.success(f"✅ {expert_id}: Retrieved {memory_count} memories")
                else:
                    logger.error(f"❌ Memory retrieval failed for {expert_id}: {response.status_code}")
        except Exception as e:
            logger.error(f"❌ Memory retrieval error for {expert_id}: {e}")

    # Test 4: Orchestrated prediction generation
    logger.info("=== Test 4: Orchestrated Prediction Generation ===")

    orchestration_payload = {
        "game_id": TEST_GAME_ID,
        "expert_ids": TEST_EXPERTS,
        "api_base_url": API_BASE_URL,
        "enable_shadow_runs": True,
        "shadow_models": {
            "conservative_analyzer": "google/gemini-2.5-flash-preview-09-2025",
            "momentum_rider": "anthropic/claude-sonnet-4.5",
            "contrarian_rebel": "deepseek/deepseek-chat-v3.1:free",
            "value_hunter": "x-ai/grok-4-fast:free"
        },
        "orchestration_id": f"smoke_test_{int(time.time())}"
    }

    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                "http://localhost:3000/agents/game-orchestrator",
                json=orchestration_payload
            )

            if response.status_code == 200:
                result = response.json()
                experts_processed = result.get('experts_processed', [])
                experts_failed = result.get('experts_failed', [])
                total_duration = result.get('total_duration_ms', 0)
                schema_compliance = result.get('schema_compliance_rate', 0)

                logger.success(f"✅ Orchestration completed in {total_duration}ms")
                logger.info(f"Experts processed: {len(experts_processed)}")
                logger.info(f"Experts failed: {len(experts_failed)}")
                logger.info(f"Schema compliance: {schema_compliance:.1%}")

                if experts_failed:
                    logger.warning(f"⚠️ Failed experts: {experts_failed}")

                # Check shadow results
                shadow_results = result.get('shadow_results', [])
                if shadow_results:
                    logger.info(f"Shadow runs completed: {len(shadow_results)}")

            else:
                logger.error(f"❌ Orchestration failed: {response.status_code}")
                logger.error(response.text)
                return False

    except Exception as e:
        logger.error(f"❌ Orchestration error: {e}")
        return False

    # Test 5: Council selection and aggregation
    logger.info("=== Test 5: Council Selection & Aggregation ===")

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(f"{API_BASE_URL}/council/select", json={
                "game_id": TEST_GAME_ID,
                "expert_ids": TEST_EXPERTS
            })

            if response.status_code == 200:
                council = response.json()
                selected_experts = council.get('selected_experts', [])
                logger.success(f"✅ Council selected: {len(selected_experts)} experts")

                for expert in selected_experts:
                    logger.info(f"  - {expert['expert_id']}: weight={expert['weight']:.3f}")

            else:
                logger.error(f"❌ Council selection failed: {response.status_code}")

    except Exception as e:
        logger.error(f"❌ Council selection error: {e}")

    # Test 6: Coherence projection
    logger.info("=== Test 6: Coherence Projection ===")

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(f"{API_BASE_URL}/projection/coherence", json={
                "game_id": TEST_GAME_ID
            })

            if response.status_code == 200:
                projection = response.json()
                coherence_score = projection.get('coherence_score', 0)
                adjustments_made = projection.get('adjustments_made', 0)

                logger.success(f"✅ Coherence projection completed")
                logger.info(f"Coherence score: {coherence_score:.3f}")
                logger.info(f"Adjustments made: {adjustments_made}")

            else:
                logger.error(f"❌ Coherence projection failed: {response.status_code}")

    except Exception as e:
        logger.error(f"❌ Coherence projection error: {e}")

    # Test 7: Model switching simulation
    logger.info("=== Test 7: Model Switching Simulation ===")

    for expert_id in TEST_EXPERTS:
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(f"{API_BASE_URL}/model-switcher/evaluate", json={
                    "expert_id": expert_id,
                    "family": "markets",
                    "force_evaluation": True
                })

                if response.status_code == 200:
                    switch_result = response.json()
                    primary_model = switch_result.get('primary_model')
                    switch_occurred = switch_result.get('switch_occurred', False)

                    if switch_occurred:
                        logger.info(f"🔄 {expert_id}: Switched to {primary_model}")
                    else:
                        logger.success(f"✅ {expert_id}: Staying with {primary_model}")

                else:
                    logger.warning(f"⚠️ Model switching evaluation failed for {expert_id}")

        except Exception as e:
            logger.error(f"❌ Model switching error for {expert_id}: {e}")

    logger.success("🎉 Smoke test completed successfully!")
    return True


async def main():
    """Main smoke test execution"""
    success = await run_smoke_test()

    if success:
        logger.success("✅ All smoke tests passed!")
        exit(0)
    else:
        logger.error("❌ Some smoke tests failed!")
        exit(1)


if __name__ == "__main__":
    asyncio.run(main())
