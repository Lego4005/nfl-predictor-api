#!/usr/bin/env python3
"""
Database Schema Verification and Setup Utility

This script verifies the current database schema and creates missing t
eded for the NFL prediction system's memory and learning capabilities.
"""

import os
import sys
import asyncio
import json
from datetime import datetime
from typing import Dict, List, Any, Optional
from supabase import create_client, Client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add src to path for imports
sys.path.append('src')

class DatabaseSchemaVerifier:
    """Verifies and sets up database schema for NFL prediction system"""

    def __init__(self):
        """Initialize database connection"""
        self.supabase_url = os.getenv('SUPABASE_URL')
        self.supabase_key = os.getenv('SUPABASE_ANON_KEY')

        if not self.supabase_url or not self.supabase_key:
            raise ValueError("SUPABASE_URL and SUPABASE_ANON_KEY must be set in environment")

        self.supabase: Client = create_client(self.supabase_url, self.supabase_key)

        # Define required tables and their schemas
        self.required_tables = {
            'expert_memories': {
                'description': 'Stores expert episodic memories with embeddings',
                'columns': [
                    'id BIGSERIAL PRIMARY KEY',
                    'memory_id TEXT UNIQUE NOT NULL',
                    'expert_id TEXT NOT NULL',
                    'memory_type TEXT NOT NULL',
                    'memory_title TEXT NOT NULL',
                    'memory_content TEXT NOT NULL',
                    'confidence_level FLOAT NOT NULL CHECK (confidence_level >= 0 AND confidence_level <= 1)',
                    'teams_involved TEXT[] NOT NULL',
                    'game_context_tags TEXT[] NOT NULL',
                    'supporting_games TEXT[] NOT NULL',
                    'contradicting_games TEXT[] NOT NULL',
                    'created_date TIMESTAMPTZ NOT NULL DEFAULT NOW()',
                    'last_reinforced TIMESTAMPTZ NOT NULL DEFAULT NOW()',
                    'reinforcement_count INTEGER NOT NULL DEFAULT 1',
                    'memory_strength FLOAT NOT NULL CHECK (memory_strength >= 0 AND memory_strength <= 1)',
                    'embedding VECTOR(1536)'
                ],
                'indexes': [
                    'CREATE INDEX IF NOT EXISTS idx_expert_memories_expert_id ON expert_memories(expert_id)',
                    'CREATE INDEX IF NOT EXISTS idx_expert_memories_memory_type ON expert_memories(memory_type)',
                    'CREATE INDEX IF NOT EXISTS idx_expert_memories_created_date ON expert_memories(created_date)',
                    'CREATE INDEX IF NOT EXISTS idx_expert_memories_teams ON expert_memories USING GIN(teams_involved)',
                    'CREATE INDEX IF NOT EXISTS idx_expert_memories_embedding ON expert_memories USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100)'
                ]
            },

            'team_memories': {
                'description': 'Team-specific memory buckets with relevance scoring',
                'columns': [
                    'id BIGSERIAL PRIMARY KEY',
                    'expert_id TEXT NOT NULL',
                    'team_name TEXT NOT NULL',
                    'memory_type TEXT NOT NULL',
                    'memory_content TEXT NOT NULL',
                    'relevance_score FLOAT NOT NULL CHECK (relevance_score >= 0 AND relevance_score <= 1)',
                    'confidence_level FLOAT NOT NULL CHECK (confidence_level >= 0 AND confidence_level <= 1)',
                    'game_context_tags TEXT[] NOT NULL',
                    'supporting_games TEXT[] NOT NULL',
                    'created_date TIMESTAMPTZ NOT NULL DEFAULT NOW()',
                    'last_updated TIMESTAMPTZ NOT NULL DEFAULT NOW()',
                    'memory_strength FLOAT NOT NULL CHECK (memory_strength >= 0 AND memory_strength <= 1)'
                ],
                'indexes': [
                    'CREATE INDEX IF NOT EXISTS idx_team_memories_expert_team ON team_memories(expert_id, team_name)',
                    'CREATE INDEX IF NOT EXISTS idx_team_memories_relevance ON team_memories(relevance_score DESC)',
                    'CREATE INDEX IF NOT EXISTS idx_team_memories_created_date ON team_memories(created_date)'
                ]
            },

            'matchup_memories': {
                'description': 'Team vs team historical insights and patterns',
                'columns': [
                    'id BIGSERIAL PRIMARY KEY',
                    'expert_id TEXT NOT NULL',
                    'matchup_key TEXT NOT NULL',
                    'team_a TEXT NOT NULL',
                    'team_b TEXT NOT NULL',
                    'memory_content TEXT NOT NULL',
                    'confidence_level FLOAT NOT NULL CHECK (confidence_level >= 0 AND confidence_level <= 1)',
                    'historical_accuracy FLOAT CHECK (historical_accuracy >= 0 AND historical_accuracy <= 1)',
                    'games_analyzed INTEGER NOT NULL DEFAULT 0',
                    'last_meeting_date TIMESTAMPTZ',
                    'created_date TIMESTAMPTZ NOT NULL DEFAULT NOW()',
                    'last_updated TIMESTAMPTZ NOT NULL DEFAULT NOW()'
                ],
                'indexes': [
                    'CREATE INDEX IF NOT EXISTS idx_matchup_memories_expert_matchup ON matchup_memories(expert_id, matchup_key)',
                    'CREATE INDEX IF NOT EXISTS idx_matchup_memories_teams ON matchup_memories(team_a, team_b)',
                    'CREATE INDEX IF NOT EXISTS idx_matchup_memories_accuracy ON matchup_memories(historical_accuracy DESC)'
                ]
            },

            'expert_predictions': {
                'description': 'Enhanced predictions with reasoning chains and memory sources',
                'columns': [
                    'id BIGSERIAL PRIMARY KEY',
                    'prediction_id TEXT UNIQUE NOT NULL',
                    'expert_id TEXT NOT NULL',
                    'game_id TEXT NOT NULL',
                    'predicted_winner TEXT NOT NULL',
                    'win_probability FLOAT NOT NULL CHECK (win_probability >= 0 AND win_probability <= 1)',
                    'confidence_level FLOAT NOT NULL CHECK (confidence_level >= 0 AND confidence_level <= 1)',
                    'reasoning_chain TEXT[] NOT NULL',
                    'memory_sources TEXT[] NOT NULL',
                    'team_weights JSONB NOT NULL',
                    'matchup_weights JSONB NOT NULL',
                    'created_date TIMESTAMPTZ NOT NULL DEFAULT NOW()',
                    'game_date TIMESTAMPTZ',
                    'home_team TEXT NOT NULL',
                    'away_team TEXT NOT NULL'
                ],
                'indexes': [
                    'CREATE INDEX IF NOT EXISTS idx_expert_predictions_expert_id ON expert_predictions(expert_id)',
                    'CREATE INDEX IF NOT EXISTS idx_expert_predictions_game_id ON expert_predictions(game_id)',
                    'CREATE INDEX IF NOT EXISTS idx_expert_predictions_teams ON expert_predictions(home_team, away_team)',
                    'CREATE INDEX IF NOT EXISTS idx_expert_predictions_created_date ON expert_predictions(created_date)'
                ]
            },

            'weight_adjustments': {
                'description': 'Tracks all weight changes with reasons and temporal analysis',
                'columns': [
                    'id BIGSERIAL PRIMARY KEY',
                    'expert_id TEXT NOT NULL',
                    'adjustment_type TEXT NOT NULL',
                    'target_entity TEXT NOT NULL',
                    'old_weight FLOAT NOT NULL',
                    'new_weight FLOAT NOT NULL',
                    'adjustment_reason TEXT NOT NULL',
                    'trigger_game_id TEXT',
                    'prediction_accuracy BOOLEAN',
                    'confidence_calibration FLOAT',
                    'created_date TIMESTAMPTZ NOT NULL DEFAULT NOW()',
                    'effectiveness_score FLOAT CHECK (effectiveness_score >= -1 AND effectiveness_score <= 1)'
                ],
                'indexes': [
                    'CREATE INDEX IF NOT EXISTS idx_weight_adjustments_expert_id ON weight_adjustments(expert_id)',
                    'CREATE INDEX IF NOT EXISTS idx_weight_adjustments_type ON weight_adjustments(adjustment_type)',
                    'CREATE INDEX IF NOT EXISTS idx_weight_adjustments_created_date ON weight_adjustments(created_date)',
                    'CREATE INDEX IF NOT EXISTS idx_weight_adjustments_effectiveness ON weight_adjustments(effectiveness_score DESC)'
                ]
            }
        }

        # Team name standardization mapping
        self.team_name_mapping = {
            'LV': 'las_vegas_raiders',
            'LAS': 'las_vegas_raiders',
            'LAR': 'los_angeles_rams',
            'LAC': 'los_angeles_chargers',
            'NO': 'new_orleans_saints',
            'NE': 'new_england_patriots',
            'TB': 'tampa_bay_buccaneers',
            'GB': 'green_bay_packers',
            'KC': 'kansas_city_chiefs',
            'SF': 'san_francisco_49ers',
            'NYG': 'new_york_giants',
            'NYJ': 'new_york_jets'
        }

    async def verify_schema(self) -> Dict[str, Any]:
        """Verify current database schema and identify missing components"""
        print("🔍 Verifying database schema...")

        verification_results = {
            'existing_tables': [],
            'missing_tables': [],
            'table_details': {},
            'pgvector_enabled': False,
            'schema_issues': []
        }

        try:
            # Check if pgvector extension is enabled
            verification_results['pgvector_enabled'] = await self._check_pgvector()

            # Check each required table
            for table_name, table_config in self.required_tables.items():
                exists = await self._check_table_exists(table_name)

                if exists:
                    verification_results['existing_tables'].append(table_name)
                    # Get table details
                    details = await self._get_table_details(table_name)
                    verification_results['table_details'][table_name] = details
                else:
                    verification_results['missing_tables'].append(table_name)

            print(f"✅ Schema verification completed")
            print(f"   Existing tables: {len(verification_results['existing_tables'])}")
            print(f"   Missing tables: {len(verification_results['missing_tables'])}")
            print(f"   pgvector enabled: {verification_results['pgvector_enabled']}")

            return verification_results

        except Exception as e:
            print(f"❌ Schema verification failed: {e}")
            verification_results['schema_issues'].append(str(e))
            return verification_results

    async def setup_missing_tables(self, verification_results: Dict[str, Any]) -> bool:
        """Create missing tables and indexes"""
        print("🔧 Setting up missing database tables...")

        if not verification_results['missing_tables']:
            print("✅ All required tables already exist")
            return True

        try:
            # Enable pgvector if not already enabled
            if not verification_results['pgvector_enabled']:
                await self._enable_pgvector()

            # Create missing tables
            for table_name in verification_results['missing_tables']:
                await self._create_table(table_name)

            print(f"✅ Successfully created {len(verification_results['missing_tables'])} missing tables")
            return True

        except Exception as e:
            print(f"❌ Failed to setup missing tables: {e}")
            return False

    async def _check_pgvector(self) -> bool:
        """Check if pgvector extension is enabled"""
        try:
            # Try to create a test vector - this will fail if pgvector is not enabled
            test_query = "SELECT '[1,2,3]'::vector(3)"
            result = await self.supabase.rpc('exec_sql', {'sql': test_query}).execute()
            return True
        except:
            return False

    async def _enable_pgvector(self):
        """Enable pgvector extension"""
        try:
            enable_query = "CREATE EXTENSION IF NOT EXISTS vector"
            await self.supabase.rpc('exec_sql', {'sql': enable_query}).execute()
            print("✅ pgvector extension enabled")
        except Exception as e:
            print(f"⚠️ Could not enable pgvector extension: {e}")
            print("   This may require database admin privileges")

    async def _check_table_exists(self, table_name: str) -> bool:
        """Check if a table exists"""
        try:
            # Try to query the table with limit 0 to check existence
            result = await self.supabase.table(table_name).select('*').limit(0).execute()
            return True
        except:
            return False

    async def _get_table_details(self, table_name: str) -> Dict[str, Any]:
        """Get details about an existing table"""
        try:
            # Get a sample row to see column structure
            result = await self.supabase.table(table_name).select('*').limit(1).execute()

            details = {
                'columns': list(result.data[0].keys()) if result.data else [],
                'row_count': 0
            }

            # Get row count
            count_result = await self.supabase.table(table_name).select('*', count='exact').execute()
            details['row_count'] = count_result.count or 0

            return details
        except Exception as e:
            return {'error': str(e)}

    async def _create_table(self, table_name: str):
        """Create a table with its schema"""
        table_config = self.required_tables[table_name]

        print(f"   Creating table: {table_name}")

        # Build CREATE TABLE statement
        columns_sql = ',\n    '.join(table_config['columns'])
        create_sql = f"""
        CREATE TABLE IF NOT EXISTS {table_name} (
            {columns_sql}
        )
        """

        try:
            # Create table
            await self.supabase.rpc('exec_sql', {'sql': create_sql}).execute()

            # Create indexes
            if 'indexes' in table_config:
                for index_sql in table_config['indexes']:
                    try:
                        await self.supabase.rpc('exec_sql', {'sql': index_sql}).execute()
                    except Exception as e:
                        print(f"   ⚠️ Index creation warning: {e}")

            print(f"   ✅ Created {table_name}")

        except Exception as e:
            print(f"   ❌ Failed to create {table_name}: {e}")
            raise

    def standardize_team_name(self, team_name: str) -> str:
        """Standardize team name to resolve naming inconsistencies"""
        if not team_name:
            return team_name

        # Convert to uppercase for mapping lookup
        team_upper = team_name.upper()

        # Check direct mapping
        if team_upper in self.team_name_mapping:
            return self.team_name_mapping[team_upper]

        # Check if it's already in standard format
        team_lower = team_name.lower()
        if '_' in team_lower:
            return team_lower

        # Default: convert to lowercase with underscores
        return team_name.lower().replace(' ', '_')

    async def validate_data_integrity(self) -> Dict[str, Any]:
        """Validate data integrity across prediction tables"""
        print("🔍 Validating data integrity...")

        integrity_results = {
            'null_predictions': 0,
            'team_name_mismatches': [],
            'accuracy_calculation_issues': [],
            'recommendations': []
        }

        try:
            # Check for null predicted_winner values
            if await self._check_table_exists('expert_predictions'):
                null_check = await self.supabase.table('expert_predictions')\
                    .select('id', count='exact')\
                    .is_('predicted_winner', 'null')\
                    .execute()

                integrity_results['null_predictions'] = null_check.count or 0

            # Check team name variations
            team_variations = await self._find_team_name_variations()
            integrity_results['team_name_mismatches'] = team_variations

            # Generate recommendations
            if integrity_results['null_predictions'] > 0:
                integrity_results['recommendations'].append(
                    f"Fix {integrity_results['null_predictions']} null predicted_winner values"
                )

            if team_variations:
                integrity_results['recommendations'].append(
                    f"Standardize {len(team_variations)} team name variations"
                )

            print(f"✅ Data integrity validation completed")
            return integrity_results

        except Exception as e:
            print(f"❌ Data integrity validation failed: {e}")
            integrity_results['error'] = str(e)
            return integrity_results

    async def _find_team_name_variations(self) -> List[Dict[str, Any]]:
        """Find team name variations across tables"""
        variations = []

        # This would need to be implemented based on actual table structure
        # For now, return empty list
        return variations

    async def generate_report(self, verification_results: Dict[str, Any],
                            integrity_results: Dict[str, Any]) -> str:
        """Generate comprehensive database schema report"""

        report = f"""
# Database Schema Verification Report
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Schema Status
- **Existing Tables**: {len(verification_results['existing_tables'])}
- **Missing Tables**: {len(verification_results['missing_tables'])}
- **pgvector Enabled**: {verification_results['pgvector_enabled']}

## Table Details
"""

        for table_name in verification_results['existing_tables']:
            details = verification_results['table_details'].get(table_name, {})
            row_count = details.get('row_count', 0)
            report += f"- **{table_name}**: {row_count} rows\n"

        if verification_results['missing_tables']:
            report += f"\n## Missing Tables\n"
            for table_name in verification_results['missing_tables']:
                config = self.required_tables[table_name]
                report += f"- **{table_name}**: {config['description']}\n"

        report += f"""
## Data Integrity
- **Null Predictions**: {integrity_results.get('null_predictions', 0)}
- **Team Name Issues**: {len(integrity_results.get('team_name_mismatches', []))}

## Recommendations
"""

        for rec in integrity_results.get('recommendations', []):
            report += f"- {rec}\n"

        return report


async def main():
    """Main verification and setup process"""
    print("🗄️ NFL Prediction System - Database Schema Verification")
    print("=" * 60)

    try:
        # Initialize verifier
        verifier = DatabaseSchemaVerifier()

        # Verify current schema
        verification_results = await verifier.verify_schema()

        # Validate data integrity
        integrity_results = await verifier.validate_data_integrity()

        # Generate report
        report = await verifier.generate_report(verification_results, integrity_results)

        # Save report
        with open('database_schema_report.md', 'w') as f:
            f.write(report)

        print(f"\n📊 Report saved to: database_schema_report.md")

        # Ask user if they want to setup missing tables
        if verification_results['missing_tables']:
            print(f"\n🔧 Found {len(verification_results['missing_tables'])} missing tables:")
            for table in verification_results['missing_tables']:
                print(f"   - {table}")

            setup_choice = input("\nSetup missing tables? (y/n): ").lower().strip()

            if setup_choice == 'y':
                success = await verifier.setup_missing_tables(verification_results)
                if success:
                    print("✅ Database schema setup completed successfully!")
                else:
                    print("❌ Database schema setup failed")
                    return 1
            else:
                print("⚠️ Skipping table setup - some features may not work correctly")
        else:
            print("✅ All required tables exist - schema is complete!")

        return 0

    except Exception as e:
        print(f"❌ Database schema verification failed: {e}")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
