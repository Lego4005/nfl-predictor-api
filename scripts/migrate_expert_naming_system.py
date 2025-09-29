#!/usr/bin/env python3
"""
Expert Naming System Standardization Migration Script
Executes the database migration and validates the standardized expert system
"""

import os
import sys
import asyncio
import psycopg2
from datetime import datetime
from typing import Dict, List, Optional

# Add the project root to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.database.supabase_client import get_supabase_client, get_database_url

class ExpertNamingMigrator:
    """Handles the expert naming standardization migration"""
    
    def __init__(self):
        self.supabase = get_supabase_client()
        self.db_url = get_database_url()
        self.migration_log = []
        
    def log_step(self, message: str, success: bool = True):
        """Log migration step"""
        timestamp = datetime.now().isoformat()
        status = "✅" if success else "❌"
        log_entry = f"{status} {timestamp}: {message}"
        self.migration_log.append(log_entry)
        print(log_entry)
        
    def execute_sql_file(self, file_path: str) -> bool:
        """Execute SQL migration file"""
        try:
            self.log_step(f"Executing migration file: {file_path}")
            
            with open(file_path, 'r') as file:
                sql_content = file.read()
            
            # Connect directly to PostgreSQL for complex migration
            conn = psycopg2.connect(self.db_url)
            cursor = conn.cursor()
            
            # Execute the migration
            cursor.execute(sql_content)
            conn.commit()
            
            cursor.close()
            conn.close()
            
            self.log_step(f"Successfully executed migration: {file_path}")
            return True
            
        except Exception as e:
            self.log_step(f"Error executing migration {file_path}: {str(e)}", False)
            return False
    
    def validate_expert_count(self) -> bool:
        """Validate that we have exactly 15 experts"""
        try:
            result = self.supabase.table('personality_experts').select('expert_id').execute()
            expert_count = len(result.data) if result.data else 0
            
            if expert_count == 15:
                self.log_step(f"✅ Expert count validation passed: {expert_count} experts found")
                return True
            else:
                self.log_step(f"❌ Expert count validation failed: Expected 15, found {expert_count}", False)
                return False
                
        except Exception as e:
            self.log_step(f"Error validating expert count: {str(e)}", False)
            return False
    
    def validate_expert_ids(self) -> bool:
        """Validate that all expert IDs match the standardized format"""
        expected_ids = [
            'conservative_analyzer',
            'risk_taking_gambler', 
            'contrarian_rebel',
            'value_hunter',
            'momentum_rider',
            'fundamentalist_scholar',
            'chaos_theory_believer',
            'gut_instinct_expert',
            'statistics_purist',
            'trend_reversal_specialist',
            'popular_narrative_fader',
            'sharp_money_follower',
            'underdog_champion',
            'consensus_follower',
            'market_inefficiency_exploiter'
        ]
        
        try:
            result = self.supabase.table('personality_experts').select('expert_id, name').execute()
            
            if not result.data:
                self.log_step("❌ No expert data found", False)
                return False
            
            found_ids = [expert['expert_id'] for expert in result.data]
            missing_ids = set(expected_ids) - set(found_ids)
            extra_ids = set(found_ids) - set(expected_ids)
            
            if missing_ids:
                self.log_step(f"❌ Missing expert IDs: {missing_ids}", False)
                return False
                
            if extra_ids:
                self.log_step(f"❌ Unexpected expert IDs: {extra_ids}", False)
                return False
            
            self.log_step("✅ All expert IDs match standardized format")
            
            # Log the expert mapping for verification
            for expert in result.data:
                self.log_step(f"   • {expert['expert_id']} → {expert['name']}")
            
            return True
            
        except Exception as e:
            self.log_step(f"Error validating expert IDs: {str(e)}", False)
            return False
    
    def validate_personality_traits(self) -> bool:
        """Validate that personality traits are properly structured"""
        try:
            result = self.supabase.table('personality_experts')\
                .select('expert_id, name, personality_traits')\
                .execute()
            
            if not result.data:
                self.log_step("❌ No expert data found for trait validation", False)
                return False
            
            required_traits = [
                'risk_tolerance',
                'analytics_trust', 
                'contrarian_tendency',
                'optimism',
                'chaos_comfort',
                'confidence_level',
                'market_trust',
                'value_seeking'
            ]
            
            validation_failed = False
            
            for expert in result.data:
                expert_id = expert['expert_id']
                traits = expert.get('personality_traits', {})
                
                if not isinstance(traits, dict):
                    self.log_step(f"❌ {expert_id}: Personality traits not a dict", False)
                    validation_failed = True
                    continue
                
                missing_traits = set(required_traits) - set(traits.keys())
                if missing_traits:
                    self.log_step(f"❌ {expert_id}: Missing traits {missing_traits}", False)
                    validation_failed = True
                    continue
                
                # Validate trait values are between 0.0 and 1.0
                for trait_name, trait_value in traits.items():
                    if trait_name in required_traits:
                        if not isinstance(trait_value, (int, float)) or not (0.0 <= trait_value <= 1.0):
                            self.log_step(f"❌ {expert_id}: Invalid {trait_name} value: {trait_value}", False)
                            validation_failed = True
            
            if not validation_failed:
                self.log_step("✅ All personality traits properly structured")
                return True
            else:
                return False
                
        except Exception as e:
            self.log_step(f"Error validating personality traits: {str(e)}", False)
            return False
    
    def backup_current_data(self) -> bool:
        """Create a backup of current expert data"""
        try:
            self.log_step("Creating backup of current expert data")
            
            # This is handled by the migration SQL itself
            self.log_step("✅ Backup creation handled by migration SQL")
            return True
            
        except Exception as e:
            self.log_step(f"Error creating backup: {str(e)}", False)
            return False
    
    def run_migration(self) -> bool:
        """Execute the complete migration process"""
        self.log_step("🚀 Starting Expert Naming System Standardization Migration")
        
        # Step 1: Backup current data
        if not self.backup_current_data():
            return False
        
        # Step 2: Execute migration SQL
        migration_file = os.path.join(
            os.path.dirname(__file__),
            '..',
            'database',
            'migrations',
            '021_expert_naming_standardization.sql'
        )
        
        if not os.path.exists(migration_file):
            self.log_step(f"❌ Migration file not found: {migration_file}", False)
            return False
        
        if not self.execute_sql_file(migration_file):
            return False
        
        # Step 3: Validate migration results
        validations = [
            self.validate_expert_count(),
            self.validate_expert_ids(),
            self.validate_personality_traits()
        ]
        
        if all(validations):
            self.log_step("🎉 Expert Naming Standardization Migration completed successfully!")
            return True
        else:
            self.log_step("❌ Migration validation failed", False)
            return False
    
    def generate_migration_report(self) -> str:
        """Generate a detailed migration report"""
        report = []
        report.append("=" * 80)
        report.append("EXPERT NAMING SYSTEM STANDARDIZATION MIGRATION REPORT")
        report.append("=" * 80)
        report.append(f"Migration Date: {datetime.now().isoformat()}")
        report.append("")
        
        report.append("MIGRATION LOG:")
        report.append("-" * 40)
        for log_entry in self.migration_log:
            report.append(log_entry)
        
        report.append("")
        report.append("SUMMARY:")
        report.append("-" * 40)
        
        success_count = sum(1 for log in self.migration_log if "✅" in log)
        error_count = sum(1 for log in self.migration_log if "❌" in log)
        
        report.append(f"Total Steps: {len(self.migration_log)}")
        report.append(f"Successful: {success_count}")
        report.append(f"Failed: {error_count}")
        
        if error_count == 0:
            report.append("🎉 MIGRATION STATUS: SUCCESS")
        else:
            report.append("❌ MIGRATION STATUS: FAILED")
        
        report.append("=" * 80)
        
        return "\n".join(report)

def main():
    """Main migration execution"""
    migrator = ExpertNamingMigrator()
    
    try:
        success = migrator.run_migration()
        
        # Generate and save report
        report = migrator.generate_migration_report()
        
        report_file = f"expert_naming_migration_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        with open(report_file, 'w') as f:
            f.write(report)
        
        print(f"\n📄 Migration report saved to: {report_file}")
        print(report)
        
        if success:
            print("\n🎉 Expert naming standardization completed successfully!")
            sys.exit(0)
        else:
            print("\n❌ Migration failed. Please check the logs and try again.")
            sys.exit(1)
            
    except Exception as e:
        print(f"❌ Migration script error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()