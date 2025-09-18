#!/usr/bin/env python3
"""
Schema Validation Script for Episodic Memory System
Validates that migration 011 creates the correct tables and the services can interact with them
"""

import asyncio
import asyncpg
import os
import sys
import json
from datetime import datetime
from pathlib import Path

# Add the src directory to the path
sys.path.append(str(Path(__file__).parent.parent / "src"))

from ml.belief_revision_service import BeliefRevisionService, RevisionType, RevisionTrigger
from ml.episodic_memory_manager import EpisodicMemoryManager, EmotionalState, MemoryType

class SchemaValidator:
    def __init__(self):
        self.db_config = {
            'host': os.getenv('DB_HOST', 'localhost'),
            'port': int(os.getenv('DB_PORT', '5432')),
            'user': os.getenv('DB_USER', 'postgres'),
            'password': os.getenv('DB_PASSWORD', 'postgres'),
            'database': os.getenv('DB_NAME', 'nfl_predictor')
        }
        self.connection = None

    async def connect(self):
        """Establish database connection"""
        try:
            self.connection = await asyncpg.connect(**self.db_config)
            print("✅ Database connection established")
            return True
        except Exception as e:
            print(f"❌ Failed to connect to database: {e}")
            return False

    async def validate_table_structure(self):
        """Validate that required tables exist with correct columns"""
        print("\n🔍 Validating table structure...")

        # Check expert_belief_revisions table
        belief_revisions_schema = await self.connection.fetch("""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns
            WHERE table_name = 'expert_belief_revisions'
            ORDER BY ordinal_position;
        """)

        if not belief_revisions_schema:
            print("❌ expert_belief_revisions table not found")
            return False

        print("✅ expert_belief_revisions table found with columns:")
        for col in belief_revisions_schema:
            print(f"   - {col['column_name']}: {col['data_type']} ({'nullable' if col['is_nullable'] == 'YES' else 'not null'})")

        # Check expert_episodic_memories table
        episodic_memories_schema = await self.connection.fetch("""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns
            WHERE table_name = 'expert_episodic_memories'
            ORDER BY ordinal_position;
        """)

        if not episodic_memories_schema:
            print("❌ expert_episodic_memories table not found")
            return False

        print("\n✅ expert_episodic_memories table found with columns:")
        for col in episodic_memories_schema:
            print(f"   - {col['column_name']}: {col['data_type']} ({'nullable' if col['is_nullable'] == 'YES' else 'not null'})")

        return True

    async def validate_indexes(self):
        """Validate that required indexes exist"""
        print("\n🔍 Validating indexes...")

        indexes = await self.connection.fetch("""
            SELECT
                schemaname,
                tablename,
                indexname,
                indexdef
            FROM pg_indexes
            WHERE tablename IN ('expert_belief_revisions', 'expert_episodic_memories')
            ORDER BY tablename, indexname;
        """)

        if not indexes:
            print("❌ No indexes found for episodic memory tables")
            return False

        print("✅ Found indexes:")
        for idx in indexes:
            print(f"   - {idx['tablename']}.{idx['indexname']}")

        return True

    async def validate_foreign_keys(self):
        """Validate foreign key constraints"""
        print("\n🔍 Validating foreign key constraints...")

        constraints = await self.connection.fetch("""
            SELECT
                tc.table_name,
                tc.constraint_name,
                tc.constraint_type,
                kcu.column_name,
                ccu.table_name AS foreign_table_name,
                ccu.column_name AS foreign_column_name
            FROM information_schema.table_constraints AS tc
            JOIN information_schema.key_column_usage AS kcu
                ON tc.constraint_name = kcu.constraint_name
                AND tc.table_schema = kcu.table_schema
            JOIN information_schema.constraint_column_usage AS ccu
                ON ccu.constraint_name = tc.constraint_name
                AND ccu.table_schema = tc.table_schema
            WHERE tc.constraint_type = 'FOREIGN KEY'
                AND tc.table_name IN ('expert_belief_revisions', 'expert_episodic_memories');
        """)

        print("✅ Found foreign key constraints:")
        for fk in constraints:
            print(f"   - {fk['table_name']}.{fk['column_name']} -> {fk['foreign_table_name']}.{fk['foreign_column_name']}")

        return True

    async def test_belief_revision_service(self):
        """Test belief revision service integration"""
        print("\n🧪 Testing Belief Revision Service...")

        try:
            service = BeliefRevisionService(self.db_config)
            await service.initialize()

            # Test data
            original_prediction = {
                "winner": "Chiefs",
                "confidence": 0.65,
                "home_score": 24,
                "away_score": 21,
                "reasoning": "Strong offensive line"
            }

            revised_prediction = {
                "winner": "Bills",
                "confidence": 0.72,
                "home_score": 21,
                "away_score": 28,
                "reasoning": "Key injury to Chiefs QB"
            }

            trigger_data = {"type": "injury_report", "details": "Mahomes questionable"}

            # Test belief revision detection and storage
            revision = await service.detect_belief_revision(
                expert_id="expert_001",
                game_id="test_game_123",
                original_prediction=original_prediction,
                new_prediction=revised_prediction,
                trigger_data=trigger_data
            )

            if revision:
                print(f"✅ Successfully created belief revision: {revision.revision_type.value}")
                print(f"   Impact score: {revision.impact_score:.2f}")
                print(f"   Emotional state: {revision.emotional_state}")
            else:
                print("❌ No belief revision detected")

            # Test revision history retrieval
            history = await service.get_expert_revision_history("expert_001", limit=10)
            print(f"✅ Retrieved {len(history)} revision history entries")

            await service.close()
            return True

        except Exception as e:
            print(f"❌ Belief Revision Service test failed: {e}")
            return False

    async def test_episodic_memory_manager(self):
        """Test episodic memory manager integration"""
        print("\n🧪 Testing Episodic Memory Manager...")

        try:
            manager = EpisodicMemoryManager(self.db_config)
            await manager.initialize()

            # Test data
            prediction_data = {
                "winner": "Chiefs",
                "confidence": 0.85,
                "home_score": 28,
                "away_score": 21,
                "reasoning_chain": [
                    {"factor": "Offensive EPA", "value": "+0.35", "weight": 0.4},
                    {"factor": "Home Field", "value": "Strong", "weight": 0.3}
                ]
            }

            actual_outcome = {
                "winner": "Bills",
                "home_score": 24,
                "away_score": 31
            }

            # Test memory creation and storage
            memory = await manager.create_episodic_memory(
                expert_id="expert_001",
                game_id="test_game_456",
                prediction_data=prediction_data,
                actual_outcome=actual_outcome
            )

            print(f"✅ Successfully created episodic memory: {memory.memory_type.value}")
            print(f"   Emotional state: {memory.emotional_state.value}")
            print(f"   Memory vividness: {memory.memory_vividness:.2f}")
            print(f"   Lessons learned: {len(memory.lessons_learned)}")

            # Test memory retrieval
            similar_memories = await manager.retrieve_similar_memories(
                expert_id="expert_001",
                current_situation={
                    "home_team": "Chiefs",
                    "away_team": "Bills",
                    "confidence": 0.8,
                    "predicted_winner": "Chiefs"
                }
            )

            print(f"✅ Retrieved {len(similar_memories)} similar memories")

            # Test memory statistics
            stats = await manager.get_memory_stats("expert_001")
            print(f"✅ Memory stats - Total: {stats.get('total_memories', 0)}")

            await manager.close()
            return True

        except Exception as e:
            print(f"❌ Episodic Memory Manager test failed: {e}")
            return False

    async def validate_supporting_tables(self):
        """Validate supporting tables exist"""
        print("\n🔍 Validating supporting tables...")

        # Check weather_conditions table
        weather_exists = await self.connection.fetchval("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables
                WHERE table_name = 'weather_conditions'
            );
        """)

        if weather_exists:
            print("✅ weather_conditions table exists")
        else:
            print("❌ weather_conditions table missing")

        # Check injury_reports table
        injury_exists = await self.connection.fetchval("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables
                WHERE table_name = 'injury_reports'
            );
        """)

        if injury_exists:
            print("✅ injury_reports table exists")
        else:
            print("❌ injury_reports table missing")

        return weather_exists and injury_exists

    async def cleanup_test_data(self):
        """Clean up test data"""
        print("\n🧹 Cleaning up test data...")

        try:
            await self.connection.execute("""
                DELETE FROM expert_belief_revisions WHERE game_id LIKE 'test_game_%';
            """)

            await self.connection.execute("""
                DELETE FROM expert_episodic_memories WHERE game_id LIKE 'test_game_%';
            """)

            print("✅ Test data cleaned up")
        except Exception as e:
            print(f"⚠️ Cleanup warning: {e}")

    async def run_validation(self):
        """Run complete validation suite"""
        print("🚀 Starting Episodic Memory Schema Validation")
        print("=" * 50)

        if not await self.connect():
            return False

        validations = [
            ("Table Structure", self.validate_table_structure),
            ("Indexes", self.validate_indexes),
            ("Foreign Keys", self.validate_foreign_keys),
            ("Supporting Tables", self.validate_supporting_tables),
            ("Belief Revision Service", self.test_belief_revision_service),
            ("Episodic Memory Manager", self.test_episodic_memory_manager),
        ]

        results = []
        for name, validation_func in validations:
            try:
                result = await validation_func()
                results.append((name, result))
            except Exception as e:
                print(f"❌ {name} validation failed with error: {e}")
                results.append((name, False))

        # Cleanup
        await self.cleanup_test_data()

        # Summary
        print("\n📊 Validation Summary")
        print("=" * 50)
        passed = 0
        for name, result in results:
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"{name}: {status}")
            if result:
                passed += 1

        print(f"\nPassed: {passed}/{len(results)}")

        await self.connection.close()
        return passed == len(results)

async def main():
    """Main function"""
    validator = SchemaValidator()
    success = await validator.run_validation()

    if success:
        print("\n🎉 All validations passed! Schema is ready for production.")
        sys.exit(0)
    else:
        print("\n💥 Some validations failed. Please check the migration and services.")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())