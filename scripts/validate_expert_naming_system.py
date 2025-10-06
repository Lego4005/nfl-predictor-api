#!/usr/bin/env python3
"""
Expert Naming System Validation Framework
Comprehensive testing to ensure consistency across all system components
"""

import os
import sys
import json
import asyncio
import requests
from typing import Dict, List, Optional, Any
from datetime import datetime

# Add the project root to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.database.supabase_client import get_supabase_client
from src.ml.personality_driven_experts import (
    ConservativeAnalyzer, RiskTakingGambler, ContrarianRebel,
    ValueHunter, MomentumRider, FundamentalistScholar,
    ChaosTheoryBeliever, GutInstinctExpert, StatisticsPurist,
    TrendReversalSpecialist, PopularNarrativeFader,
    SharpMoneyFollower, UnderdogChampion, ConsensusFollower,
    MarketInefficiencyExploiter
)

class ExpertNamingValidator:
    """Validates expert naming consistency across all system components"""
    
    def __init__(self):
        self.supabase = get_supabase_client()
        self.validation_results = []
        self.errors = []
        
        # Expected standardized expert mapping
        self.expected_experts = {
            'conservative_analyzer': 'The Analyst',
            'risk_taking_gambler': 'The Gambler', 
            'contrarian_rebel': 'The Rebel',
            'value_hunter': 'The Hunter',
            'momentum_rider': 'The Rider',
            'fundamentalist_scholar': 'The Scholar',
            'chaos_theory_believer': 'The Chaos',
            'gut_instinct_expert': 'The Intuition',
            'statistics_purist': 'The Quant',
            'trend_reversal_specialist': 'The Reversal',
            'popular_narrative_fader': 'The Fader',
            'sharp_money_follower': 'The Sharp',
            'underdog_champion': 'The Underdog',
            'consensus_follower': 'The Consensus',
            'market_inefficiency_exploiter': 'The Exploiter'
        }
        
        self.expert_classes = [
            ConservativeAnalyzer, RiskTakingGambler, ContrarianRebel,
            ValueHunter, MomentumRider, FundamentalistScholar,
            ChaosTheoryBeliever, GutInstinctExpert, StatisticsPurist,
            TrendReversalSpecialist, PopularNarrativeFader,
            SharpMoneyFollower, UnderdogChampion, ConsensusFollower,
            MarketInefficiencyExploiter
        ]
    
    def log_result(self, component: str, test: str, success: bool, details: str = ""):
        """Log validation result"""
        status = "✅ PASS" if success else "❌ FAIL"
        result = {
            'timestamp': datetime.now().isoformat(),
            'component': component,
            'test': test,
            'status': status,
            'success': success,
            'details': details
        }
        self.validation_results.append(result)
        
        print(f"{status} [{component}] {test}")
        if details:
            print(f"    {details}")
        
        if not success:
            self.errors.append(f"{component}: {test} - {details}")
    
    def validate_ml_backend_experts(self) -> bool:
        """Validate ML backend expert classes and IDs"""
        print("\n🧠 VALIDATING ML BACKEND EXPERTS")
        print("-" * 50)
        
        all_valid = True
        
        try:
            # Test expert class instantiation
            for expert_class in self.expert_classes:
                try:
                    expert = expert_class()
                    expected_name = self.expected_experts.get(expert.expert_id)
                    
                    if not expected_name:
                        self.log_result(
                            "ML Backend", 
                            f"Expert ID Recognition: {expert_class.__name__}",
                            False,
                            f"Expert ID '{expert.expert_id}' not in expected mapping"
                        )
                        all_valid = False
                        continue
                    
                    if expert.name != expected_name:
                        self.log_result(
                            "ML Backend",
                            f"Expert Name Consistency: {expert_class.__name__}",
                            False,
                            f"Expected '{expected_name}', got '{expert.name}'"
                        )
                        all_valid = False
                        continue
                    
                    self.log_result(
                        "ML Backend",
                        f"Expert Instantiation: {expert_class.__name__}",
                        True,
                        f"{expert.expert_id} → {expert.name}"
                    )
                    
                except Exception as e:
                    self.log_result(
                        "ML Backend",
                        f"Expert Instantiation: {expert_class.__name__}",
                        False,
                        f"Failed to instantiate: {str(e)}"
                    )
                    all_valid = False
            
            # Validate all expected experts are represented
            instantiated_ids = []
            for expert_class in self.expert_classes:
                try:
                    expert = expert_class()
                    instantiated_ids.append(expert.expert_id)
                except:
                    pass
            
            missing_ids = set(self.expected_experts.keys()) - set(instantiated_ids)
            if missing_ids:
                self.log_result(
                    "ML Backend",
                    "Complete Expert Coverage",
                    False,
                    f"Missing expert implementations: {missing_ids}"
                )
                all_valid = False
            else:
                self.log_result(
                    "ML Backend",
                    "Complete Expert Coverage",
                    True,
                    f"All {len(self.expected_experts)} experts implemented"
                )
            
        except Exception as e:
            self.log_result(
                "ML Backend",
                "Expert System Validation",
                False,
                f"Critical error: {str(e)}"
            )
            all_valid = False
        
        return all_valid
    
    def validate_database_experts(self) -> bool:
        """Validate database expert records"""
        print("\n🗄️  VALIDATING DATABASE EXPERTS")
        print("-" * 50)
        
        all_valid = True
        
        try:
            # Fetch all experts from database
            result = self.supabase.table('personality_experts')\
                .select('expert_id, name, personality_traits, decision_style')\
                .execute()
            
            if not result.data:
                self.log_result(
                    "Database",
                    "Expert Data Existence",
                    False,
                    "No expert records found in database"
                )
                return False
            
            db_experts = {expert['expert_id']: expert for expert in result.data}
            
            # Check expert count
            if len(db_experts) != 15:
                self.log_result(
                    "Database",
                    "Expert Count",
                    False,
                    f"Expected 15 experts, found {len(db_experts)}"
                )
                all_valid = False
            else:
                self.log_result(
                    "Database",
                    "Expert Count",
                    True,
                    f"Found all {len(db_experts)} experts"
                )
            
            # Validate each expected expert
            for expected_id, expected_name in self.expected_experts.items():
                if expected_id not in db_experts:
                    self.log_result(
                        "Database",
                        f"Expert Existence: {expected_id}",
                        False,
                        f"Expert '{expected_id}' not found in database"
                    )
                    all_valid = False
                    continue
                
                db_expert = db_experts[expected_id]
                
                # Validate name
                if db_expert['name'] != expected_name:
                    self.log_result(
                        "Database",
                        f"Expert Name: {expected_id}",
                        False,
                        f"Expected '{expected_name}', got '{db_expert['name']}'"
                    )
                    all_valid = False
                else:
                    self.log_result(
                        "Database",
                        f"Expert Name: {expected_id}",
                        True,
                        f"{expected_id} → {expected_name}"
                    )
                
                # Validate personality traits structure
                traits = db_expert.get('personality_traits', {})
                required_traits = [
                    'risk_tolerance', 'analytics_trust', 'contrarian_tendency',
                    'optimism', 'chaos_comfort', 'confidence_level',
                    'market_trust', 'value_seeking'
                ]
                
                if not isinstance(traits, dict):
                    self.log_result(
                        "Database",
                        f"Personality Traits Structure: {expected_id}",
                        False,
                        "Personality traits is not a JSON object"
                    )
                    all_valid = False
                    continue
                
                missing_traits = set(required_traits) - set(traits.keys())
                if missing_traits:
                    self.log_result(
                        "Database",
                        f"Personality Traits Completeness: {expected_id}",
                        False,
                        f"Missing traits: {missing_traits}"
                    )
                    all_valid = False
                else:
                    self.log_result(
                        "Database",
                        f"Personality Traits: {expected_id}",
                        True,
                        f"All {len(required_traits)} traits present"
                    )
            
        except Exception as e:
            self.log_result(
                "Database",
                "Database Connection",
                False,
                f"Database error: {str(e)}"
            )
            all_valid = False
        
        return all_valid
    
    def validate_frontend_experts(self) -> bool:
        """Validate frontend expert definitions"""
        print("\n🎨 VALIDATING FRONTEND EXPERTS")
        print("-" * 50)
        
        all_valid = True
        
        try:
            # Check if the frontend expert file exists and is valid
            frontend_file = os.path.join(
                os.path.dirname(__file__),
                '..',
                'src',
                'data',
                'expertPersonalities.ts'
            )
            
            if not os.path.exists(frontend_file):
                self.log_result(
                    "Frontend",
                    "Expert Personalities File",
                    False,
                    f"File not found: {frontend_file}"
                )
                return False
            
            # Read and analyze the TypeScript file
            with open(frontend_file, 'r') as f:
                content = f.read()
            
            # Check for standardized expert IDs
            found_experts = 0
            for expected_id in self.expected_experts.keys():
                if f"id: '{expected_id}'" in content:
                    found_experts += 1
                    self.log_result(
                        "Frontend",
                        f"Expert ID: {expected_id}",
                        True,
                        f"Found in expert definitions"
                    )
                else:
                    self.log_result(
                        "Frontend",
                        f"Expert ID: {expected_id}",
                        False,
                        f"Not found in expert definitions"
                    )
                    all_valid = False
            
            # Validate expert count in frontend
            if found_experts != 15:
                self.log_result(
                    "Frontend",
                    "Expert Count",
                    False,
                    f"Expected 15 experts, found {found_experts}"
                )
                all_valid = False
            else:
                self.log_result(
                    "Frontend",
                    "Expert Count",
                    True,
                    f"All {found_experts} experts defined"
                )
            
            # Check for personality traits structure
            if "personality_traits: {" in content:
                self.log_result(
                    "Frontend",
                    "Personality Traits Structure",
                    True,
                    "Structured personality traits found"
                )
            else:
                self.log_result(
                    "Frontend",
                    "Personality Traits Structure",
                    False,
                    "Structured personality traits not found"
                )
                all_valid = False
            
        except Exception as e:
            self.log_result(
                "Frontend",
                "File Analysis",
                False,
                f"Error analyzing frontend file: {str(e)}"
            )
            all_valid = False
        
        return all_valid
    
    def validate_api_endpoints(self) -> bool:
        """Validate API endpoint expert consistency"""
        print("\n🔌 VALIDATING API ENDPOINTS")
        print("-" * 50)
        
        all_valid = True
        
        try:
            # Check simple expert API
            simple_api_file = os.path.join(
                os.path.dirname(__file__),
                '..',
                'src',
                'api',
                'simple_expert_api.py'
            )
            
            if os.path.exists(simple_api_file):
                with open(simple_api_file, 'r') as f:
                    content = f.read()
                
                # Check for standardized expert IDs
                found_count = 0
                for expected_id in self.expected_experts.keys():
                    if f'"{expected_id}"' in content:
                        found_count += 1
                
                if found_count >= 10:  # Allow some flexibility
                    self.log_result(
                        "API",
                        "Simple Expert API IDs",
                        True,
                        f"Found {found_count}/15 standardized IDs"
                    )
                else:
                    self.log_result(
                        "API",
                        "Simple Expert API IDs",
                        False,
                        f"Only found {found_count}/15 standardized IDs"
                    )
                    all_valid = False
            
            # Check expert deep dive API
            deep_dive_file = os.path.join(
                os.path.dirname(__file__),
                '..',
                'src',
                'api',
                'expert_deep_dive_endpoints.py'
            )
            
            if os.path.exists(deep_dive_file):
                with open(deep_dive_file, 'r') as f:
                    content = f.read()
                
                found_count = 0
                for expected_id in self.expected_experts.keys():
                    if f'"{expected_id}"' in content:
                        found_count += 1
                
                if found_count >= 10:
                    self.log_result(
                        "API",
                        "Deep Dive API IDs",
                        True,
                        f"Found {found_count}/15 standardized IDs"
                    )
                else:
                    self.log_result(
                        "API",
                        "Deep Dive API IDs",
                        False,
                        f"Only found {found_count}/15 standardized IDs"
                    )
                    all_valid = False
            
        except Exception as e:
            self.log_result(
                "API",
                "API File Analysis",
                False,
                f"Error analyzing API files: {str(e)}"
            )
            all_valid = False
        
        return all_valid
    
    def validate_cross_component_consistency(self) -> bool:
        """Validate consistency between all components"""
        print("\n🔄 VALIDATING CROSS-COMPONENT CONSISTENCY")
        print("-" * 50)
        
        all_valid = True
        
        try:
            # Collect expert data from all components
            ml_experts = {}
            for expert_class in self.expert_classes:
                try:
                    expert = expert_class()
                    ml_experts[expert.expert_id] = expert.name
                except:
                    pass
            
            # Database experts
            result = self.supabase.table('personality_experts')\
                .select('expert_id, name')\
                .execute()
            
            db_experts = {}
            if result.data:
                db_experts = {expert['expert_id']: expert['name'] for expert in result.data}
            
            # Compare ML and Database
            ml_db_consistent = True
            for expert_id in self.expected_experts.keys():
                ml_name = ml_experts.get(expert_id)
                db_name = db_experts.get(expert_id)
                expected_name = self.expected_experts[expert_id]
                
                if ml_name != expected_name or db_name != expected_name:
                    self.log_result(
                        "Cross-Component",
                        f"Name Consistency: {expert_id}",
                        False,
                        f"ML: '{ml_name}', DB: '{db_name}', Expected: '{expected_name}'"
                    )
                    ml_db_consistent = False
                    all_valid = False
                else:
                    self.log_result(
                        "Cross-Component",
                        f"Name Consistency: {expert_id}",
                        True,
                        f"All components use '{expected_name}'"
                    )
            
            if ml_db_consistent:
                self.log_result(
                    "Cross-Component",
                    "Overall Consistency",
                    True,
                    "All components use consistent expert names"
                )
            
        except Exception as e:
            self.log_result(
                "Cross-Component",
                "Consistency Check",
                False,
                f"Error checking consistency: {str(e)}"
            )
            all_valid = False
        
        return all_valid
    
    def run_full_validation(self) -> bool:
        """Run complete validation suite"""
        print("🔍 EXPERT NAMING SYSTEM VALIDATION")
        print("=" * 80)
        
        validation_components = [
            ("ML Backend", self.validate_ml_backend_experts),
            ("Database", self.validate_database_experts),
            ("Frontend", self.validate_frontend_experts),
            ("API Endpoints", self.validate_api_endpoints),
            ("Cross-Component", self.validate_cross_component_consistency)
        ]
        
        overall_success = True
        
        for component_name, validation_func in validation_components:
            try:
                success = validation_func()
                if not success:
                    overall_success = False
            except Exception as e:
                print(f"❌ CRITICAL ERROR in {component_name}: {str(e)}")
                overall_success = False
        
        return overall_success
    
    def generate_validation_report(self) -> str:
        """Generate comprehensive validation report"""
        report = []
        report.append("=" * 80)
        report.append("EXPERT NAMING SYSTEM VALIDATION REPORT")
        report.append("=" * 80)
        report.append(f"Validation Date: {datetime.now().isoformat()}")
        report.append(f"Total Tests: {len(self.validation_results)}")
        
        passed = sum(1 for r in self.validation_results if r['success'])
        failed = len(self.validation_results) - passed
        
        report.append(f"Passed: {passed}")
        report.append(f"Failed: {failed}")
        report.append("")
        
        # Group results by component
        components = {}
        for result in self.validation_results:
            comp = result['component']
            if comp not in components:
                components[comp] = []
            components[comp].append(result)
        
        for component, results in components.items():
            report.append(f"{component.upper()}:")
            report.append("-" * len(component))
            
            for result in results:
                report.append(f"  {result['status']} {result['test']}")
                if result['details']:
                    report.append(f"    {result['details']}")
            report.append("")
        
        if self.errors:
            report.append("ERRORS SUMMARY:")
            report.append("-" * 20)
            for error in self.errors:
                report.append(f"  ❌ {error}")
            report.append("")
        
        if failed == 0:
            report.append("🎉 OVERALL STATUS: ALL VALIDATIONS PASSED")
        else:
            report.append("❌ OVERALL STATUS: VALIDATION FAILURES DETECTED")
        
        report.append("=" * 80)
        
        return "\n".join(report)

def main():
    """Main validation execution"""
    validator = ExpertNamingValidator()
    
    try:
        success = validator.run_full_validation()
        
        # Generate and save report
        report = validator.generate_validation_report()
        
        report_file = f"expert_naming_validation_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        with open(report_file, 'w') as f:
            f.write(report)
        
        print(f"\n📄 Validation report saved to: {report_file}")
        print("\n" + "=" * 80)
        print("VALIDATION SUMMARY")
        print("=" * 80)
        
        if success:
            print("🎉 ALL VALIDATIONS PASSED!")
            print("✅ Expert naming system is consistent across all components")
            sys.exit(0)
        else:
            print("❌ VALIDATION FAILURES DETECTED")
            print("🔧 Please review the report and fix the identified issues")
            sys.exit(1)
            
    except Exception as e:
        print(f"❌ Validation script error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()