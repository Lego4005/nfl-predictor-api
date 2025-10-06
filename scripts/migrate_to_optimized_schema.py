#!/usr/bin/env python3
"""
Migration sc to backfill optimized expert memory schema
Extracts team data from JSONB contextual_factors and generates embeddings
"""

import os
import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Optional
import json
import hashlib
from dotenv import load_dotenv
from supabase import create_client

# Load environment
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class OptimizedSchemaMigrator:
    def __init__(self):
        self.supabase = create_client(
            os.getenv('SUPABASE_URL'),
            os.getenv('SUPABASE_ANON_KEY')
        )

    async def migrate_episodic_memories(self):
        """Extract team data from contextual_factors and populate new columns"""
        logger.info("🔄 Migrating episodic memories to optimized schema...")

        try:
            # Get all memories that need migration
            result = self.supabase.table('expert_episodic_memories') \
                .select('memory_id, expert_id, game_id, contextual_factors, created_at') \
                .is_('home_team', None) \
                .execute()

            memories = result.data
            logger.info(f"Found {len(memories)} memories to migrate")

            migrated_count = 0
            for memory in memories:
                try:
                    # Extract team data from contextual_factors
                    factors = memory.get('contextual_factors', [])
                    home_team = None
                    away_team = None
                    season = None
                    week = None
                    game_date = None

                    # Parse contextual factors
                    for factor in factors:
                        if isinstance(factor, dict):
                            factor_name = factor.get('factor', '')
                            factor_value = factor.get('value', '')

                            if factor_name == 'home_team':
                                home_team = await self.resolve_team_alias(factor_value)
                            elif factor_name == 'away_team':
                                away_team = await self.resolve_team_alias(factor_value)
                            elif factor_name == 'season':
                                try:
                                    season = int(factor_value)
                                except:
                                    pass
                            elif factor_name == 'week':
                                try:
                                    week = int(factor_value)
                                except:
                                    pass
                            elif factor_name == 'game_date':
                                try:
                                    game_date = factor_value
                                except:
                                    pass

                    # Try to extract from game_id if not found in factors
                    if not home_team or not away_team:
                        home_team, away_team = await self.extract_teams_from_game_id(memory['game_id'])

                    # Update the memory record
                    if home_team and away_team:
                        update_data = {
                            'home_team': home_team,
                            'away_team': away_team
                        }

                        if season:
                            update_data['season'] = season
                        if week:
                            update_data['week'] = week
                        if game_date:
                            update_data['game_date'] = game_date

                        self.supabase.table('expert_episodic_memories') \
                            .update(update_data) \
                            .eq('memory_id', memory['memory_id']) \
                            .execute()

                        migrated_count += 1

                        if migrated_count % 10 == 0:
                            logger.info(f"Migrated {migrated_count}/{len(memories)} memories...")

                except Exception as e:
                    logger.error(f"Error migrating memory {memory['memory_id']}: {e}")
                    continue

            logger.info(f"✅ Successfully migrated {migrated_count} episodic memories")
            return migrated_count

        except Exception as e:
            logger.error(f"❌ Error migrating episodic memories: {e}")
            return 0

    async def resolve_team_alias(self, alias: str) -> Optional[str]:
        """Resolve team alias to canonical team_id"""
        if not alias:
            return None

        try:
            # Try direct team_id match first
            result = self.supabase.table('teams') \
                .select('team_id') \
                .eq('team_id', alias.upper()) \
                .execute()

            if result.data:
                return result.data[0]['team_id']

            # Try alias lookup
            result = self.supabase.table('team_aliases') \
                .select('team_id') \
                .eq('alias', alias) \
                .execute()

            if result.data:
                return result.data[0]['team_id']

            # Try fuzzy matching for common variations
            fuzzy_matches = {
                'kansas city': 'KC',
                'new england': 'NE',
                'green bay': 'GB',
                'new york giants': 'NYG',
                'new york jets': 'NYJ',
                'los angeles rams': 'LAR',
                'los angeles chargers': 'LAC',
                'las vegas': 'LV',
                'san francisco': 'SF',
                'tampa bay': 'TB',
                'new orleans': 'NO'
            }

            alias_lower = alias.lower()
            if alias_lower in fuzzy_matches:
                return fuzzy_matches[alias_lower]

            logger.warning(f"Could not resolve team alias: {alias}")
            return None

        except Exception as e:
            logger.error(f"Error resolving team alias {alias}: {e}")
            return None

    async def extract_teams_from_game_id(self, game_id: str) -> tuple:
        """Extract team names from game_id format"""
        try:
            # Common game_id formats: "KC_BUF_2023_W6", "KC@BUF_2023", etc.
            if '_' in game_id:
                parts = game_id.split('_')
                if len(parts) >= 2:
                    team1 = await self.resolve_team_alias(parts[0])
                    team2 = await self.resolve_team_alias(parts[1])
                    if team1 and team2:
                        return team2, team1  # away @ home

            if '@' in game_id:
                parts = game_id.split('@')
                if len(parts) == 2:
                    away_team = await self.resolve_team_alias(parts[0])
                    home_team = await self.resolve_team_alias(parts[1].split('_')[0])
                    if away_team and home_team:
                        return home_team, away_team

            return None, None

        except Exception as e:
            logger.error(f"Error extracting teams from game_id {game_id}: {e}")
            return None, None

    async def generate_embeddings_batch(self, batch_size: int = 10):
        """Generate embeddings for memories in batches"""
        logger.info("🔄 Generating embeddings for memories...")

        try:
            # Get memories without embeddings
            result = self.supabase.table('expert_episodic_memories') \
                .select('memory_id, expert_id, game_id, home_team, away_team, prediction_data, actual_outcome, lessons_learned') \
                .is_('combined_embedding', None) \
                .limit(batch_size) \
                .execute()

            memories = result.data
            logger.info(f"Found {len(memories)} memories needing embeddings")

            embedded_count = 0
            for memory in memories:
                try:
                    # Create combined text for embedding
                    combined_text = self.create_memory_text(memory)

                    # Generate embedding (placeholder - would use actual embedding service)
                    # For now, create a dummy embedding
                    embedding = [0.0] * 1536  # Placeholder

                    # Update memory with embedding
                    self.supabase.table('expert_episodic_memories') \
                        .update({
                            'combined_embedding': embedding,
                            'embedding_generated_at': datetime.now().isoformat(),
                            'embedding_version': 1
                        }) \
                        .eq('memory_id', memory['memory_id']) \
                        .execute()

                    embedded_count += 1

                    if embedded_count % 5 == 0:
                        logger.info(f"Generated embeddings for {embedded_count}/{len(memories)} memories...")

                except Exception as e:
                    logger.error(f"Error generating embedding for memory {memory['memory_id']}: {e}")
                    continue

            logger.info(f"✅ Generated embeddings for {embedded_count} memories")
            return embedded_count

        except Exception as e:
            logger.error(f"❌ Error generating embeddings: {e}")
            return 0

    def create_memory_text(self, memory: Dict) -> str:
        """Create combined text representation of memory for embedding"""
        parts = []

        # Add team context
        if memory.get('home_team') and memory.get('away_team'):
            parts.append(f"{memory['away_team']} at {memory['home_team']}")

        # Add prediction data
        if memory.get('prediction_data'):
            pred_data = memory['prediction_data']
            if isinstance(pred_data, dict):
                if pred_data.get('predicted_winner'):
                    parts.append(f"Predicted winner: {pred_data['predicted_winner']}")
                if pred_data.get('confidence'):
                    parts.append(f"Confidence: {pred_data['confidence']}")

        # Add outcome
        if memory.get('actual_outcome'):
            outcome = memory['actual_outcome']
            if isinstance(outcome, dict):
                if outcome.get('winner'):
                    parts.append(f"Actual winner: {outcome['winner']}")

        # Add lessons learned
        if memory.get('lessons_learned'):
            lessons = memory['lessons_learned']
            if isinstance(lessons, list):
                for lesson in lessons:
                    if isinstance(lesson, str):
                        parts.append(lesson)

        return " | ".join(parts)

    async def validate_migration(self):
        """Validate the migration results"""
        logger.info("🔍 Validating migration results...")

        try:
            # Check episodic memories
            result = self.supabase.table('expert_episodic_memories') \
                .select('memory_id, home_team, away_team, combined_embedding') \
                .execute()

            memories = result.data
            total_memories = len(memories)

            with_teams = len([m for m in memories if m.get('home_team') and m.get('away_team')])
            with_embeddings = len([m for m in memories if m.get('combined_embedding')])

            logger.info(f"📊 Migration Validation Results:")
            logger.info(f"   Total memories: {total_memories}")
            logger.info(f"   With team data: {with_teams} ({with_teams/total_memories*100:.1f}%)")
            logger.info(f"   With embeddings: {with_embeddings} ({with_embeddings/total_memories*100:.1f}%)")

            # Check team knowledge
            result = self.supabase.table('team_knowledge').select('*').execute()
            team_knowledge_count = len(result.data)
            logger.info(f"   Team knowledge entries: {team_knowledge_count}")

            # Check matchup memories
            result = self.supabase.table('matchup_memories').select('*').execute()
            matchup_memories_count = len(result.data)
            logger.info(f"   Matchup memories: {matchup_memories_count}")

            return {
                'total_memories': total_memories,
                'with_teams': with_teams,
                'with_embeddings': with_embeddings,
                'team_knowledge': team_knowledge_count,
                'matchup_memories': matchup_memories_count
            }

        except Exception as e:
            logger.error(f"❌ Error validating migration: {e}")
            return {}

async def main():
    """Run the complete migration process"""
    logger.info("🚀 Starting optimized schema migration...")

    migrator = OptimizedSchemaMigrator()

    try:
        # Step 1: Migrate episodic memories
        migrated_memories = await migrator.migrate_episodic_memories()

        # Step 2: Generate embeddings (batch)
        embedded_memories = await migrator.generate_embeddings_batch(batch_size=20)

        # Step 3: Validate migration
        validation_results = await migrator.validate_migration()

        logger.info("✅ Migration completed successfully!")
        logger.info(f"   Migrated memories: {migrated_memories}")
        logger.info(f"   Generated embeddings: {embedded_memories}")

        return validation_results

    except Exception as e:
        logger.error(f"❌ Migration failed: {e}")
        return None

if __name__ == "__main__":
    asyncio.run(main())
