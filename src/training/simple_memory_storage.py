#!/usr/bin/env python3
"""
Simpy Storage System

File-based memory storage for expert learning experiences before implementing
vector databases. Stores and retrieves prediction memories for expert improvement.
"""

import sys
import logging
import json
import os
from datetime import datetime, date
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from pathlib import Path
sys.path.append('src')

from training.expert_configuration import ExpertType

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class MemoryRecord:
    """Individual memory record for an expert"""
    memory_id: str
    expert_id: str
    game_id: str
    game_date: str
    teams: str
    week: int
    season: int

    # Prediction details
    prediction: Dict[str, Any]
    outcome: Dict[str, Any]
    was_correct: bool

    # Learning metadata
    confidence_calibration: float
    validated_factors: List[str]
    contradicted_factors: List[str]
    reasoning_quality: float
    memory_strength: float
    tags: List[str]

    # Timestamps
    created_at: str
    last_accessed: Optional[str] = None
    access_count: int = 0

class SimpleMemoryStorage:
    """File-based memory storage system for expert learning"""

    def __init__(self, storage_dir: str = "expert_memories"):
        """Initialize memory storage system"""
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(exist_ok=True)

        # Create subdirectories for each expert
        for expert_type in ExpertType:
            expert_dir = self.storage_dir / expert_type.value
            expert_dir.mkdir(exist_ok=True)

        logger.info(f"✅ Simple Memory Storage initialized at {self.storage_dir}")

    def store_memory(self, expert_id: str, memory_data: Dict[str, Any]) -> str:
        """Store a memory for an expert"""
        try:
            # Generate unique memory ID
            memory_id = f"{memory_data['game_id']}_{expert_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

            # Create memory record
            memory_record = MemoryRecord(
                memory_id=memory_id,
                expert_id=expert_id,
                game_id=memory_data['game_id'],
                game_date=memory_data['game_date'],
                teams=memory_data['teams'],
                week=memory_data['week'],
                season=memory_data['season'],
                prediction=memory_data['prediction'],
                outcome=memory_data['outcome'],
                was_correct=memory_data['was_correct'],
                confidence_calibration=memory_data['confidence_calibration'],
                validated_factors=memory_data['validated_factors'],
                contradicted_factors=memory_data['contradicted_factors'],
                reasoning_quality=memory_data['reasoning_quality'],
                memory_strength=memory_data['memory_strength'],
                tags=memory_data['tags'],
                created_at=memory_data['created_at']
            )

            # Save to expert's directory
            expert_dir = self.storage_dir / expert_id
            memory_file = expert_dir / f"{memory_id}.json"

            with open(memory_file, 'w') as f:
                json.dump(asdict(memory_record), f, indent=2)

            logger.debug(f"💾 Stored memory {memory_id} for {expert_id}")
            return memory_id

        except Exception as e:
            logger.error(f"❌ Failed to store memory for {expert_id}: {e}")
            raise

    def store_multiple_memories(self, memories: Dict[str, Dict[str, Any]]) -> Dict[str, str]:
        """Store memories for multiple experts"""
        memory_ids = {}

        for expert_id, memory_data in memories.items():
            try:
                memory_id = self.store_memory(expert_id, memory_data)
                memory_ids[expert_id] = memory_id
            except Exception as e:
                logger.warning(f"⚠️ Failed to store memory for {expert_id}: {e}")
                continue

        logger.info(f"💾 Stored {len(memory_ids)} memories across experts")
        return memory_ids

    def retrieve_memories(self, expert_id: str, limit: Optional[int] = None,
                         tags: Optional[List[str]] = None) -> List[MemoryRecord]:
        """Retrieve memories for an expert"""
        try:
            expert_dir = self.storage_dir / expert_id

            if not expert_dir.exists():
                logger.warning(f"⚠️ No memories found for {expert_id}")
                return []

            memories = []

            # Load all memory files
            for memory_file in expert_dir.glob("*.json"):
                try:
                    with open(memory_file, 'r') as f:
                        memory_data = json.load(f)

                    memory_record = MemoryRecord(**memory_data)

                    # Filter by tags if specified
                    if tags:
                        if not any(tag in memory_record.tags for tag in tags):
                            continue

                    memories.append(memory_record)

                except Exception as e:
                    logger.warning(f"⚠️ Failed to load memory {memory_file}: {e}")
                    continue

            # Sort by memory strength (most important first) then by date (most recent first)
            memories.sort(key=lambda m: (m.memory_strength, m.created_at), reverse=True)

            # Apply limit
            if limit:
                memories = memories[:limit]

            # Update access tracking
            for memory in memories:
                self._update_access_tracking(memory)

            logger.debug(f"🔍 Retrieved {len(memories)} memories for {expert_id}")
            return memories

        except Exception as e:
            logger.error(f"❌ Failed to retrieve memories for {expert_id}: {e}")
            return []

    def retrieve_similar_memories(self, expert_id: str, game_context: Dict[str, Any],
                                limit: int = 5) -> List[MemoryRecord]:
        """Retrieve memories similar to current game context"""
        try:
            all_memories = self.retrieve_memories(expert_id)

            if not all_memories:
                return []

            # Simple similarity scoring based on game characteristics
            scored_memories = []

            for memory in all_memories:
                similarity_score = self._calculate_similarity(memory, game_context)
                scored_memories.append((memory, similarity_score))

            # Sort by similarity score
            scored_memories.sort(key=lambda x: x[1], reverse=True)

            # Return top similar memories
            similar_memories = [memory for memory, score in scored_memories[:limit]]

            logger.debug(f"🔍 Found {len(similar_memories)} similar memories for {expert_id}")
            return similar_memories

        except Exception as e:
            logger.error(f"❌ Failed to retrieve similar memories for {expert_id}: {e}")
            return []

    def _calculate_similarity(self, memory: MemoryRecord, game_context: Dict[str, Any]) -> float:
        """Calculate similarity between memory and current game context"""
        similarity_score = 0.0

        # Same week bonus
        if memory.week == game_context.get('week', 0):
            similarity_score += 0.3

        # Same season bonus
        if memory.season == game_context.get('season', 0):
            similarity_score += 0.2

        # Division game match
        if 'division_game' in memory.tags and game_context.get('division_game', False):
            similarity_score += 0.2

        # Weather conditions match
        weather = game_context.get('weather')
        if weather:
            if weather.get('temperature', 70) < 40 and 'cold_weather' in memory.tags:
                similarity_score += 0.2
            if weather.get('wind_speed', 0) > 15 and 'windy_conditions' in memory.tags:
                similarity_score += 0.2

        # Team involvement (same teams)
        current_teams = f"{game_context.get('away_team', '')}@{game_context.get('home_team', '')}"
        if memory.teams == current_teams:
            similarity_score += 0.4
        elif (game_context.get('home_team', '') in memory.teams or
              game_context.get('away_team', '') in memory.teams):
            similarity_score += 0.2

        # Recency bonus (more recent memories are more relevant)
        try:
            memory_date = datetime.fromisoformat(memory.created_at)
            days_ago = (datetime.now() - memory_date).days
            recency_bonus = max(0, 1.0 - (days_ago / 365))  # Decay over a year
            similarity_score += recency_bonus * 0.1
        except:
            pass

        return min(similarity_score, 1.0)

    def _update_access_tracking(self, memory: MemoryRecord):
        """Update access tracking for a memory"""
        try:
            memory.access_count += 1
            memory.last_accessed = datetime.now().isoformat()

            # Save updated memory
            expert_dir = self.storage_dir / memory.expert_id
            memory_file = expert_dir / f"{memory.memory_id}.json"

            with open(memory_file, 'w') as f:
                json.dump(asdict(memory), f, indent=2)

        except Exception as e:
            logger.warning(f"⚠️ Failed to update access tracking for {memory.memory_id}: {e}")

    def get_memory_statistics(self, expert_id: str) -> Dict[str, Any]:
        """Get statistics about stored memories for an expert"""
        try:
            memories = self.retrieve_memories(expert_id)

            if not memories:
                return {'total_memories': 0}

            # Calculate statistics
            total_memories = len(memories)
            correct_memories = sum(1 for m in memories if m.was_correct)
            accuracy = correct_memories / total_memories if total_memories > 0 else 0

            avg_confidence_calibration = sum(m.confidence_calibration for m in memories) / total_memories
            avg_memory_strength = sum(m.memory_strength for m in memories) / total_memories
            avg_reasoning_quality = sum(m.reasoning_quality for m in memories) / total_memories

            # Tag distribution
            all_tags = []
            for memory in memories:
                all_tags.extend(memory.tags)

            tag_counts = {}
            for tag in all_tags:
                tag_counts[tag] = tag_counts.get(tag, 0) + 1

            # Season distribution
            season_counts = {}
            for memory in memories:
                season_counts[memory.season] = season_counts.get(memory.season, 0) + 1

            return {
                'total_memories': total_memories,
                'accuracy': accuracy,
                'correct_memories': correct_memories,
                'avg_confidence_calibration': avg_confidence_calibration,
                'avg_memory_strength': avg_memory_strength,
                'avg_reasoning_quality': avg_reasoning_quality,
                'tag_distribution': dict(sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)[:10]),
                'season_distribution': season_counts,
                'date_range': {
                    'earliest': min(m.created_at for m in memories),
                    'latest': max(m.created_at for m in memories)
                }
            }

        except Exception as e:
            logger.error(f"❌ Failed to get statistics for {expert_id}: {e}")
            return {'error': str(e)}

    def cleanup_old_memories(self, expert_id: str, max_memories: int = 1000):
        """Clean up old memories to prevent storage bloat"""
        try:
            memories = self.retrieve_memories(expert_id)

            if len(memories) <= max_memories:
                logger.debug(f"No cleanup needed for {expert_id}: {len(memories)} memories")
                return

            # Sort by importance (memory strength + access count + recency)
            def importance_score(memory):
                recency_days = (datetime.now() - datetime.fromisoformat(memory.created_at)).days
                recency_score = max(0, 1.0 - (recency_days / 365))
                return memory.memory_strength + (memory.access_count * 0.1) + (recency_score * 0.2)

            memories.sort(key=importance_score, reverse=True)

            # Keep top memories, remove the rest
            memories_to_keep = memories[:max_memories]
            memories_to_remove = memories[max_memories:]

            expert_dir = self.storage_dir / expert_id

            for memory in memories_to_remove:
                memory_file = expert_dir / f"{memory.memory_id}.json"
                if memory_file.exists():
                    memory_file.unlink()

            logger.info(f"🧹 Cleaned up {len(memories_to_remove)} old memories for {expert_id}")

        except Exception as e:
            logger.error(f"❌ Failed to cleanup memories for {expert_id}: {e}")

    def get_system_statistics(self) -> Dict[str, Any]:
        """Get overall system statistics"""
        try:
            total_memories = 0
            expert_stats = {}

            for expert_type in ExpertType:
                expert_id = expert_type.value
                stats = self.get_memory_statistics(expert_id)
                expert_stats[expert_id] = stats
                total_memories += stats.get('total_memories', 0)

            return {
                'total_memories': total_memories,
                'total_experts': len(ExpertType),
                'avg_memories_per_expert': total_memories / len(ExpertType) if len(ExpertType) > 0 else 0,
                'expert_statistics': expert_stats
            }

        except Exception as e:
            logger.error(f"❌ Failed to get system statistics: {e}")
            return {'error': str(e)}


async def main():
    """Test the Simple Memory Storage System"""

    print("🧠 Simple Memory Storage System Test")
    print("=" * 60)

    # Initialize storage
    storage = SimpleMemoryStorage()

    # Create test memories
    test_memories = {
        'conservative_analyzer': {
            'game_id': '2020_01_HOU_KC',
            'game_date': '2020-09-10',
            'teams': 'HOU@KC',
            'week': 1,
            'season': 2020,
            'prediction': {
                'winner': 'KC',
                'probability': 0.65,
                'confidence': 0.70,
                'reasoning': ['Home field advantage', 'Statistical edge']
            },
            'outcome': {
                'home_score': 34,
                'away_score': 20,
                'winner': 'home'
            },
            'was_correct': True,
            'confidence_calibration': 0.70,
            'validated_factors': ['home_field_advantage'],
            'contradicted_factors': [],
            'reasoning_quality': 0.8,
            'memory_strength': 0.7,
            'tags': ['week_1', 'season_2020', 'correct', 'high_confidence'],
            'created_at': datetime.now().isoformat()
        },
        'contrarian_rebel': {
            'game_id': '2020_01_HOU_KC',
            'game_date': '2020-09-10',
            'teams': 'HOU@KC',
            'week': 1,
            'season': 2020,
            'prediction': {
                'winner': 'HOU',
                'probability': 0.45,
                'confidence': 0.75,
                'reasoning': ['Fade the public', 'Contrarian value']
            },
            'outcome': {
                'home_score': 34,
                'away_score': 20,
                'winner': 'home'
            },
            'was_correct': False,
            'confidence_calibration': 0.25,
            'validated_factors': [],
            'contradicted_factors': ['contrarian_approach'],
            'reasoning_quality': 0.6,
            'memory_strength': 0.8,  # High because it was a learning moment
            'tags': ['week_1', 'season_2020', 'incorrect', 'high_confidence', 'contrarian_pick'],
            'created_at': datetime.now().isoformat()
        }
    }

    print("\n💾 Storing test memories...")
    memory_ids = storage.store_multiple_memories(test_memories)
    print(f"Stored memories: {list(memory_ids.keys())}")

    # Test memory retrieval
    print("\n🔍 Testing memory retrieval...")

    # Retrieve all memories for conservative analyzer
    conservative_memories = storage.retrieve_memories('conservative_analyzer')
    print(f"Conservative Analyzer memories: {len(conservative_memories)}")

    if conservative_memories:
        memory = conservative_memories[0]
        print(f"  Sample memory: {memory.game_id} - {'✅' if memory.was_correct else '❌'} - Strength: {memory.memory_strength}")

    # Test similar memory retrieval
    print("\n🔍 Testing similar memory retrieval...")

    similar_context = {
        'home_team': 'KC',
        'away_team': 'HOU',
        'week': 1,
        'season': 2020,
        'division_game': False
    }

    similar_memories = storage.retrieve_similar_memories('conservative_analyzer', similar_context, limit=3)
    print(f"Similar memories found: {len(similar_memories)}")

    # Test memory statistics
    print("\n📊 Testing memory statistics...")

    for expert_id in ['conservative_analyzer', 'contrarian_rebel']:
        stats = storage.get_memory_statistics(expert_id)
        print(f"\n{expert_id}:")
        print(f"  Total memories: {stats.get('total_memories', 0)}")
        print(f"  Accuracy: {stats.get('accuracy', 0):.1%}")
        print(f"  Avg confidence calibration: {stats.get('avg_confidence_calibration', 0):.3f}")
        print(f"  Top tags: {list(stats.get('tag_distribution', {}).keys())[:3]}")

    # Test system statistics
    print("\n📈 System Statistics:")
    system_stats = storage.get_system_statistics()
    print(f"Total memories: {system_stats.get('total_memories', 0)}")
    print(f"Average per expert: {system_stats.get('avg_memories_per_expert', 0):.1f}")

    print("\n✅ Simple Memory Storage test complete!")
    print(f"💾 Check {storage.storage_dir}/ directory for stored memories")


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
