#!/usr/bin/env python3
"""
Cleanup Incorrect Training Memories

Remove memories that were incorrectly created from 2024 data (should be test data, not training data).
Keep only proper training memories from 2020-2023 historical data.
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import logging
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class MemoryCleanup:
    """Clean up incorrect training memories"""

    def __init__(self):
        self.supabase = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_ANON_KEY'))

    def analyze_existing_memories(self):
        """Analyze what memories currently exist"""

        logger.info("🔍 ANALYZING EXISTING MEMORIES")
        logger.info("=" * 50)

        try:
            # Get all memories
            response = self.supabase.table('expert_episodic_memories').select('*').execute()
            memories = response.data

            logger.info(f"📊 Total memories found: {len(memories)}")

            # Analyze by expert
            expert_counts = {}
            memory_types = {}
            game_ids = {}

            for memory in memories:
                expert_id = memory.get('expert_id', 'unknown')
                memory_type = memory.get('memory_type', 'unknown')
                game_id = memory.get('game_id', 'unknown')

                # Count by expert
                expert_counts[expert_id] = expert_counts.get(expert_id, 0) + 1

                # Count by memory type
                memory_types[memory_type] = memory_types.get(memory_type, 0) + 1

                # Analyze game IDs to identify incorrect 2024 training data
                if game_id.startswith('historical_2024'):
                    game_ids[game_id] = game_ids.get(game_id, 0) + 1

            logger.info("\\n📋 Memories by Expert:")
            for expert_id, count in sorted(expert_counts.items()):
                logger.info(f"   {expert_id}: {count} memories")

            logger.info("\\n📋 Memories by Type:")
            for mem_type, count in sorted(memory_types.items()):
                logger.info(f"   {mem_type}: {count} memories")

            # Identify incorrect 2024 training memories
            incorrect_2024_memories = [m for m in memories if m.get('game_id', '').startswith('historical_2024')]

            logger.info(f"\\n⚠️  INCORRECT 2024 TRAINING MEMORIES: {len(incorrect_2024_memories)}")

            if incorrect_2024_memories:
                logger.info("   These should be DELETED (2024 is test data, not training):")
                for memory in incorrect_2024_memories[:10]:  # Show first 10
                    game_id = memory.get('game_id', 'unknown')
                    expert_id = memory.get('expert_id', 'unknown')
                    logger.info(f"   - {expert_id}: {game_id}")

                if len(incorrect_2024_memories) > 10:
                    logger.info(f"   ... and {len(incorrect_2024_memories) - 10} more")

            return memories, incorrect_2024_memories

        except Exception as e:
            logger.error(f"❌ Error analyzing memories: {e}")
            return [], []

    def cleanup_incorrect_memories(self, dry_run: bool = True):
        """Clean up incorrect 2024 training memories"""

        logger.info(f"\\n🧹 CLEANUP INCORRECT MEMORIES (DRY RUN: {dry_run})")
        logger.info("=" * 50)

        try:
            # Find incorrect memories
            response = self.supabase.table('expert_episodic_memories').select('memory_id, expert_id, game_id').execute()
            all_memories = response.data

            # Identify memories to delete
            to_delete = []

            for memory in all_memories:
                game_id = memory.get('game_id', '')

                # Delete memories from 2024 training (incorrect)
                if game_id.startswith('historical_2024'):
                    to_delete.append(memory)

                # Also delete any test memories from previous runs
                elif game_id.startswith('test_2024'):
                    to_delete.append(memory)

            logger.info(f"🎯 Found {len(to_delete)} memories to delete:")
            logger.info("   - historical_2024_* (incorrect training on test data)")
            logger.info("   - test_2024_* (old test predictions)")

            if not to_delete:
                logger.info("✅ No incorrect memories found - database is clean!")
                return

            # Show what will be deleted
            expert_delete_counts = {}
            for memory in to_delete:
                expert_id = memory.get('expert_id', 'unknown')
                expert_delete_counts[expert_id] = expert_delete_counts.get(expert_id, 0) + 1

            logger.info("\\n📊 Memories to delete by expert:")
            for expert_id, count in sorted(expert_delete_counts.items()):
                logger.info(f"   {expert_id}: {count} memories")

            if dry_run:
                logger.info("\\n🔍 DRY RUN - No actual deletion performed")
                logger.info("   Run with dry_run=False to actually delete these memories")
                return len(to_delete)

            # Actually delete the memories
            logger.info("\\n🗑️  DELETING INCORRECT MEMORIES...")

            deleted_count = 0
            for memory in to_delete:
                memory_id = memory['memory_id']

                try:
                    self.supabase.table('expert_episodic_memories').delete().eq('memory_id', memory_id).execute()
                    deleted_count += 1

                    if deleted_count % 10 == 0:
                        logger.info(f"   Deleted {deleted_count}/{len(to_delete)} memories...")

                except Exception as e:
                    logger.error(f"❌ Failed to delete memory {memory_id}: {e}")

            logger.info(f"\\n✅ CLEANUP COMPLETE!")
            logger.info(f"   Deleted: {deleted_count} incorrect memories")
            logger.info(f"   Database is now ready for proper 2020-2023 training")

            return deleted_count

        except Exception as e:
            logger.error(f"❌ Error during cleanup: {e}")
            return 0

    def verify_cleanup(self):
        """Verify cleanup was successful"""

        logger.info("\\n🔍 VERIFYING CLEANUP")
        logger.info("=" * 30)

        try:
            # Check for any remaining incorrect memories
            response = self.supabase.table('expert_episodic_memories').select('game_id').execute()
            memories = response.data

            incorrect_remaining = [m for m in memories if m.get('game_id', '').startswith('historical_2024')]
            test_remaining = [m for m in memories if m.get('game_id', '').startswith('test_2024')]

            if not incorrect_remaining and not test_remaining:
                logger.info("✅ Cleanup successful - no incorrect memories remain")
                logger.info("✅ Database ready for proper 2020-2023 training")
            else:
                logger.warning(f"⚠️  Still found {len(incorrect_remaining)} incorrect training memories")
                logger.warning(f"⚠️  Still found {len(test_remaining)} old test memories")

            # Show remaining memory count
            total_remaining = len(memories)
            logger.info(f"📊 Total memories remaining: {total_remaining}")

        except Exception as e:
            logger.error(f"❌ Error verifying cleanup: {e}")

def main():
    """Main cleanup execution"""

    cleanup = MemoryCleanup()

    # Step 1: Analyze current state
    memories, incorrect_memories = cleanup.analyze_existing_memories()

    if not incorrect_memories:
        logger.info("\\n✅ No cleanup needed - database is already clean!")
        return

    # Step 2: Ask user for confirmation
    logger.info(f"\\n⚠️  Found {len(incorrect_memories)} incorrect memories to delete")
    logger.info("   These are 2024 memories that should be test data, not training data")

    user_input = input("\\nProceed with cleanup? (y/n): ")

    if user_input.lower() in ['y', 'yes']:
        # Step 3: Perform cleanup
        deleted_count = cleanup.cleanup_incorrect_memories(dry_run=False)

        # Step 4: Verify cleanup
        cleanup.verify_cleanup()

        logger.info(f"\\n🎉 Cleanup complete! Deleted {deleted_count} incorrect memories")
        logger.info("✅ Ready to run proper 2020-2023 training")
    else:
        logger.info("\\n❌ Cleanup cancelled by user")

if __name__ == "__main__":
    main()
