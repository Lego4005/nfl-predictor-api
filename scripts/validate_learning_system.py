#!/usr/bin/env python3
"""
Learning System Validation Suite

Tests all critical components of the NFL prediction learning system:
1. Memory Storage & Retrieval
2. Lesson Extraction from Outcomes
3. Belief Revision based on Evidence
4. Principle Discovery from Patterns
5. Self-Healing when Accuracy Drops
6. Cross-Week Persistence & Learning

Run with: python scripts/validate_learning_system.py
"""

import os
import sys
import json
import asyncio
from datetime import datetime, timedelta
from typing import List, Dict, Any, Tuple
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import learning system components
from app.services.learning.episodic_memory import EpisodicMemory
from app.services.learning.lesson_extractor import LessonExtractor
from app.services.learning.belief_revision import BeliefRevisionSystem
from app.services.learning.principle_discovery import PrincipleDiscovery
from app.services.learning.self_healing import SelfHealingSystem
from app.services.learning.cross_session_memory import CrossSessionMemory


class Colors:
    """Terminal colors for output"""
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    RESET = '\033[0m'
    BOLD = '\033[1m'


class ValidationResults:
    """Track validation results across all tests"""
    def __init__(self):
        self.tests_run = 0
        self.tests_passed = 0
        self.tests_failed = 0
        self.test_details = []
        self.metrics = {}

    def add_test(self, name: str, passed: bool, details: str, metrics: Dict = None):
        self.tests_run += 1
        if passed:
            self.tests_passed += 1
        else:
            self.tests_failed += 1

        self.test_details.append({
            'name': name,
            'passed': passed,
            'details': details,
            'metrics': metrics or {}
        })

    def add_metric(self, category: str, key: str, value: Any):
        if category not in self.metrics:
            self.metrics[category] = {}
        self.metrics[category][key] = value


def print_header(text: str):
    """Print a formatted header"""
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*80}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{text.center(80)}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*80}{Colors.RESET}\n")


def print_test_result(test_name: str, passed: bool, details: str = ""):
    """Print a test result with formatting"""
    status = f"{Colors.GREEN}✅ PASS{Colors.RESET}" if passed else f"{Colors.RED}❌ FAIL{Colors.RESET}"
    print(f"{status} | {Colors.BOLD}{test_name}{Colors.RESET}")
    if details:
        print(f"       {details}")


def print_metric(label: str, value: Any):
    """Print a metric with formatting"""
    print(f"  {Colors.CYAN}📊 {label}:{Colors.RESET} {value}")


async def test_memory_storage(results: ValidationResults) -> bool:
    """Test 1: Verify episodic memories are created and stored"""
    print_header("TEST 1: Memory Storage")

    try:
        memory = EpisodicMemory(expert_id="test_expert_001")

        # Create test memories for different scenarios
        test_scenarios = [
            {
                'prediction': {'team': 'Chiefs', 'confidence': 0.85, 'spread': -7},
                'outcome': {'correct': True, 'actual_spread': -10},
                'context': {'weather': 'clear', 'home_team': 'Chiefs'}
            },
            {
                'prediction': {'team': 'Bills', 'confidence': 0.72, 'spread': -3},
                'outcome': {'correct': False, 'actual_spread': 1},
                'context': {'weather': 'snow', 'home_team': 'Bills'}
            },
            {
                'prediction': {'team': 'Ravens', 'confidence': 0.90, 'spread': -14},
                'outcome': {'correct': True, 'actual_spread': -17},
                'context': {'weather': 'clear', 'home_team': 'Ravens'}
            }
        ]

        stored_ids = []
        for scenario in test_scenarios:
            memory_id = await memory.store_memory(
                prediction=scenario['prediction'],
                outcome=scenario['outcome'],
                context=scenario['context']
            )
            stored_ids.append(memory_id)

        # Verify storage
        stored_count = len(stored_ids)
        expected_count = len(test_scenarios)

        passed = stored_count == expected_count and all(stored_ids)
        details = f"Stored {stored_count}/{expected_count} memories successfully"

        print_test_result("Memory Storage", passed, details)
        print_metric("Memories Created", stored_count)
        print_metric("Memory IDs Valid", all(stored_ids))

        results.add_test(
            "Memory Storage",
            passed,
            details,
            {'memories_stored': stored_count, 'ids': stored_ids}
        )
        results.add_metric('memory', 'total_stored', stored_count)

        return passed

    except Exception as e:
        print_test_result("Memory Storage", False, f"Error: {str(e)}")
        results.add_test("Memory Storage", False, f"Exception: {str(e)}")
        return False


async def test_memory_retrieval(results: ValidationResults) -> bool:
    """Test 2: Verify similar memories can be retrieved"""
    print_header("TEST 2: Memory Retrieval")

    try:
        memory = EpisodicMemory(expert_id="test_expert_002")

        # Store memories with distinct patterns
        weather_pattern_memories = [
            {
                'prediction': {'team': 'Packers', 'confidence': 0.80},
                'outcome': {'correct': False},
                'context': {'weather': 'snow', 'temperature': 25}
            },
            {
                'prediction': {'team': 'Vikings', 'confidence': 0.75},
                'outcome': {'correct': False},
                'context': {'weather': 'snow', 'temperature': 20}
            },
            {
                'prediction': {'team': 'Patriots', 'confidence': 0.85},
                'outcome': {'correct': True},
                'context': {'weather': 'clear', 'temperature': 70}
            }
        ]

        for mem in weather_pattern_memories:
            await memory.store_memory(
                prediction=mem['prediction'],
                outcome=mem['outcome'],
                context=mem['context']
            )

        # Query for snow game memories
        query_context = {'weather': 'snow', 'temperature': 22}
        similar_memories = await memory.retrieve_similar(query_context, limit=5)

        # Verify retrieval
        retrieved_count = len(similar_memories)
        snow_memories = [m for m in similar_memories if m.get('context', {}).get('weather') == 'snow']

        passed = retrieved_count > 0 and len(snow_memories) >= 2
        details = f"Retrieved {retrieved_count} similar memories, {len(snow_memories)} matched weather pattern"

        print_test_result("Memory Retrieval", passed, details)
        print_metric("Total Retrieved", retrieved_count)
        print_metric("Pattern Matches", len(snow_memories))
        print_metric("Similarity Score", f"{similar_memories[0].get('similarity', 0):.2f}" if similar_memories else "N/A")

        results.add_test(
            "Memory Retrieval",
            passed,
            details,
            {'retrieved': retrieved_count, 'pattern_matches': len(snow_memories)}
        )
        results.add_metric('memory', 'retrieval_working', passed)

        return passed

    except Exception as e:
        print_test_result("Memory Retrieval", False, f"Error: {str(e)}")
        results.add_test("Memory Retrieval", False, f"Exception: {str(e)}")
        return False


async def test_lesson_extraction(results: ValidationResults) -> bool:
    """Test 3: Verify lessons are extracted from outcomes"""
    print_header("TEST 3: Lesson Extraction")

    try:
        extractor = LessonExtractor(expert_id="test_expert_003")

        # Test successful prediction
        success_lesson = await extractor.extract_lesson(
            prediction={
                'team': 'Chiefs',
                'confidence': 0.85,
                'reasoning': 'Strong offense vs weak defense'
            },
            outcome={'correct': True, 'margin': 14},
            context={'home_team': 'Chiefs', 'weather': 'clear'}
        )

        # Test failed prediction
        failure_lesson = await extractor.extract_lesson(
            prediction={
                'team': 'Cowboys',
                'confidence': 0.90,
                'reasoning': 'Home field advantage'
            },
            outcome={'correct': False, 'margin': -7},
            context={'home_team': 'Cowboys', 'weather': 'wind'}
        )

        # Verify lesson extraction
        success_valid = (
            success_lesson is not None and
            'what_worked' in success_lesson and
            len(success_lesson['what_worked']) > 0
        )

        failure_valid = (
            failure_lesson is not None and
            'what_failed' in failure_lesson and
            len(failure_lesson['what_failed']) > 0
        )

        passed = success_valid and failure_valid
        details = f"Extracted lessons from success ({success_valid}) and failure ({failure_valid})"

        print_test_result("Lesson Extraction", passed, details)
        print_metric("Success Lesson Valid", success_valid)
        print_metric("Failure Lesson Valid", failure_valid)
        if success_valid:
            print_metric("Success Insights", len(success_lesson.get('what_worked', [])))
        if failure_valid:
            print_metric("Failure Insights", len(failure_lesson.get('what_failed', [])))

        results.add_test(
            "Lesson Extraction",
            passed,
            details,
            {'success_lesson': success_valid, 'failure_lesson': failure_valid}
        )
        results.add_metric('learning', 'lesson_extraction', passed)

        return passed

    except Exception as e:
        print_test_result("Lesson Extraction", False, f"Error: {str(e)}")
        results.add_test("Lesson Extraction", False, f"Exception: {str(e)}")
        return False


async def test_belief_revision(results: ValidationResults) -> bool:
    """Test 4: Verify beliefs change when evidence accumulates"""
    print_header("TEST 4: Belief Revision")

    try:
        belief_system = BeliefRevisionSystem(expert_id="test_expert_004")

        # Initial belief
        initial_belief = {
            'statement': 'Home teams in cold weather have 70% win rate',
            'confidence': 0.70,
            'supporting_evidence': 5
        }

        await belief_system.register_belief(
            belief_id="cold_weather_home",
            belief=initial_belief
        )

        # Add contradicting evidence
        contradicting_evidence = [
            {'outcome': 'loss', 'context': {'weather': 'cold', 'location': 'home'}},
            {'outcome': 'loss', 'context': {'weather': 'cold', 'location': 'home'}},
            {'outcome': 'loss', 'context': {'weather': 'cold', 'location': 'home'}},
            {'outcome': 'loss', 'context': {'weather': 'cold', 'location': 'home'}}
        ]

        revisions_made = 0
        for evidence in contradicting_evidence:
            revision = await belief_system.update_belief(
                belief_id="cold_weather_home",
                evidence=evidence
            )
            if revision and revision.get('revised', False):
                revisions_made += 1

        # Get final belief state
        final_belief = await belief_system.get_belief("cold_weather_home")

        # Verify revision occurred
        confidence_decreased = (
            final_belief and
            final_belief.get('confidence', 1.0) < initial_belief['confidence']
        )

        passed = revisions_made > 0 and confidence_decreased
        details = f"Made {revisions_made} revisions, confidence decreased: {confidence_decreased}"

        print_test_result("Belief Revision", passed, details)
        print_metric("Initial Confidence", f"{initial_belief['confidence']:.2f}")
        print_metric("Final Confidence", f"{final_belief.get('confidence', 0):.2f}" if final_belief else "N/A")
        print_metric("Revisions Made", revisions_made)
        print_metric("Confidence Decreased", confidence_decreased)

        results.add_test(
            "Belief Revision",
            passed,
            details,
            {'revisions': revisions_made, 'confidence_changed': confidence_decreased}
        )
        results.add_metric('learning', 'belief_revision', passed)

        return passed

    except Exception as e:
        print_test_result("Belief Revision", False, f"Error: {str(e)}")
        results.add_test("Belief Revision", False, f"Exception: {str(e)}")
        return False


async def test_principle_discovery(results: ValidationResults) -> bool:
    """Test 5: Verify patterns are discovered and stored"""
    print_header("TEST 5: Principle Discovery")

    try:
        discovery = PrincipleDiscovery(expert_id="test_expert_005")

        # Simulate pattern: Road underdogs cover spread in division games
        pattern_data = [
            {
                'prediction': {'team': 'Browns', 'spread': 7, 'confidence': 0.60},
                'outcome': {'covered': True, 'actual_spread': 3},
                'context': {'location': 'away', 'underdog': True, 'division_game': True}
            },
            {
                'prediction': {'team': 'Lions', 'spread': 6, 'confidence': 0.65},
                'outcome': {'covered': True, 'actual_spread': 2},
                'context': {'location': 'away', 'underdog': True, 'division_game': True}
            },
            {
                'prediction': {'team': 'Bengals', 'spread': 5, 'confidence': 0.62},
                'outcome': {'covered': True, 'actual_spread': 4},
                'context': {'location': 'away', 'underdog': True, 'division_game': True}
            },
            {
                'prediction': {'team': 'Cardinals', 'spread': 8, 'confidence': 0.58},
                'outcome': {'covered': True, 'actual_spread': 1},
                'context': {'location': 'away', 'underdog': True, 'division_game': True}
            }
        ]

        # Feed data to discovery system
        for data in pattern_data:
            await discovery.analyze_outcome(
                prediction=data['prediction'],
                outcome=data['outcome'],
                context=data['context']
            )

        # Trigger pattern discovery
        principles = await discovery.discover_principles(min_occurrences=3)

        # Verify principles discovered
        principles_found = len(principles) > 0
        relevant_principle = None

        for principle in principles:
            if ('division' in principle.get('pattern', '').lower() or
                'underdog' in principle.get('pattern', '').lower()):
                relevant_principle = principle
                break

        passed = principles_found and relevant_principle is not None
        details = f"Discovered {len(principles)} principles, relevant pattern found: {passed}"

        print_test_result("Principle Discovery", passed, details)
        print_metric("Total Principles", len(principles))
        print_metric("Relevant Pattern Found", relevant_principle is not None)
        if relevant_principle:
            print_metric("Pattern Confidence", f"{relevant_principle.get('confidence', 0):.2f}")
            print_metric("Pattern Support", relevant_principle.get('occurrences', 0))

        results.add_test(
            "Principle Discovery",
            passed,
            details,
            {'principles_found': len(principles), 'relevant': relevant_principle is not None}
        )
        results.add_metric('learning', 'principle_discovery', passed)

        return passed

    except Exception as e:
        print_test_result("Principle Discovery", False, f"Error: {str(e)}")
        results.add_test("Principle Discovery", False, f"Exception: {str(e)}")
        return False


async def test_self_healing(results: ValidationResults) -> bool:
    """Test 6: Simulate accuracy drop and verify correction triggers"""
    print_header("TEST 6: Self-Healing System")

    try:
        healing = SelfHealingSystem(expert_id="test_expert_006")

        # Simulate initial good performance
        for i in range(10):
            await healing.record_prediction_result(correct=True, week=1)

        initial_accuracy = await healing.get_accuracy()

        # Simulate accuracy drop
        for i in range(15):
            await healing.record_prediction_result(correct=False, week=2)

        current_accuracy = await healing.get_accuracy()

        # Check if healing triggered
        healing_triggered = await healing.check_and_heal()
        corrections = await healing.get_corrections_made()

        # Verify self-healing activated
        accuracy_dropped = current_accuracy < initial_accuracy
        healing_activated = healing_triggered is not None and healing_triggered
        corrections_applied = corrections and len(corrections) > 0

        passed = accuracy_dropped and healing_activated
        details = f"Accuracy dropped: {accuracy_dropped}, healing triggered: {healing_activated}"

        print_test_result("Self-Healing", passed, details)
        print_metric("Initial Accuracy", f"{initial_accuracy:.2%}")
        print_metric("Current Accuracy", f"{current_accuracy:.2%}")
        print_metric("Healing Triggered", healing_activated)
        print_metric("Corrections Applied", len(corrections) if corrections else 0)

        results.add_test(
            "Self-Healing",
            passed,
            details,
            {'healing_triggered': healing_activated, 'corrections': len(corrections) if corrections else 0}
        )
        results.add_metric('system', 'self_healing', passed)

        return passed

    except Exception as e:
        print_test_result("Self-Healing", False, f"Error: {str(e)}")
        results.add_test("Self-Healing", False, f"Exception: {str(e)}")
        return False


async def test_cross_week_persistence(results: ValidationResults) -> bool:
    """Test 7: Verify Week 5 predictions use Week 1-4 learnings"""
    print_header("TEST 7: Cross-Week Persistence")

    try:
        cross_memory = CrossSessionMemory(expert_id="test_expert_007")

        # Simulate Week 1-4 learnings
        weekly_learnings = []
        for week in range(1, 5):
            learning = {
                'week': week,
                'lessons': [
                    f'Week {week} lesson: Home favorites are covering',
                    f'Week {week} lesson: Totals are trending under'
                ],
                'principles': [
                    {'pattern': f'Week {week} pattern discovered', 'confidence': 0.7 + (week * 0.05)}
                ],
                'accuracy': 0.6 + (week * 0.05)
            }

            await cross_memory.store_session(
                session_id=f"week_{week}",
                data=learning,
                metadata={'week': week, 'games': 16}
            )
            weekly_learnings.append(learning)

        # Retrieve learnings for Week 5 prediction
        week5_context = await cross_memory.retrieve_relevant_sessions(
            query={'week': 5, 'looking_for': 'recent_trends'},
            limit=4
        )

        # Verify persistence and retrieval
        retrieved_weeks = len(week5_context)
        has_recent_data = retrieved_weeks >= 3

        # Check if learnings are accessible
        all_lessons = []
        for session in week5_context:
            if 'data' in session and 'lessons' in session['data']:
                all_lessons.extend(session['data']['lessons'])

        learnings_available = len(all_lessons) > 0

        # Verify temporal ordering (recent data prioritized)
        temporal_order_correct = True
        if len(week5_context) >= 2:
            for i in range(len(week5_context) - 1):
                week_current = week5_context[i].get('metadata', {}).get('week', 0)
                week_next = week5_context[i + 1].get('metadata', {}).get('week', 0)
                if week_current < week_next:
                    temporal_order_correct = False
                    break

        passed = has_recent_data and learnings_available and temporal_order_correct
        details = f"Retrieved {retrieved_weeks} weeks, {len(all_lessons)} lessons available, temporal order: {temporal_order_correct}"

        print_test_result("Cross-Week Persistence", passed, details)
        print_metric("Weeks Retrieved", retrieved_weeks)
        print_metric("Total Lessons", len(all_lessons))
        print_metric("Temporal Order", "Correct" if temporal_order_correct else "Incorrect")
        print_metric("Data Available for Week 5", has_recent_data)

        results.add_test(
            "Cross-Week Persistence",
            passed,
            details,
            {'weeks_retrieved': retrieved_weeks, 'lessons': len(all_lessons)}
        )
        results.add_metric('system', 'cross_week_persistence', passed)

        return passed

    except Exception as e:
        print_test_result("Cross-Week Persistence", False, f"Error: {str(e)}")
        results.add_test("Cross-Week Persistence", False, f"Exception: {str(e)}")
        return False


def print_final_report(results: ValidationResults):
    """Print comprehensive final report"""
    print_header("VALIDATION SUMMARY")

    # Overall statistics
    pass_rate = (results.tests_passed / results.tests_run * 100) if results.tests_run > 0 else 0
    print(f"\n{Colors.BOLD}Overall Results:{Colors.RESET}")
    print(f"  Total Tests: {results.tests_run}")
    print(f"  {Colors.GREEN}Passed: {results.tests_passed}{Colors.RESET}")
    print(f"  {Colors.RED}Failed: {results.tests_failed}{Colors.RESET}")
    print(f"  Pass Rate: {pass_rate:.1f}%\n")

    # Detailed test breakdown
    print(f"{Colors.BOLD}Test Breakdown:{Colors.RESET}")
    for test in results.test_details:
        status = f"{Colors.GREEN}✅" if test['passed'] else f"{Colors.RED}❌"
        print(f"  {status} {test['name']}{Colors.RESET}")
        print(f"     {test['details']}")
        if test['metrics']:
            for key, value in test['metrics'].items():
                print(f"     • {key}: {value}")
        print()

    # Category metrics
    if results.metrics:
        print(f"{Colors.BOLD}System Metrics:{Colors.RESET}")
        for category, metrics in results.metrics.items():
            print(f"\n  {Colors.CYAN}{category.upper()}:{Colors.RESET}")
            for key, value in metrics.items():
                print(f"    • {key}: {value}")

    # Production readiness assessment
    print(f"\n{Colors.BOLD}Production Readiness Assessment:{Colors.RESET}\n")

    critical_tests = [
        'Memory Storage',
        'Memory Retrieval',
        'Lesson Extraction',
        'Cross-Week Persistence'
    ]

    critical_passed = all(
        test['passed'] for test in results.test_details
        if test['name'] in critical_tests
    )

    if pass_rate == 100:
        status = f"{Colors.GREEN}✅ PRODUCTION READY{Colors.RESET}"
        message = "All systems operational. Ready for 15-expert deployment."
    elif pass_rate >= 85 and critical_passed:
        status = f"{Colors.YELLOW}⚠️  PRODUCTION READY (with caveats){Colors.RESET}"
        message = "Critical systems working. Minor issues can be addressed in production."
    elif pass_rate >= 70:
        status = f"{Colors.YELLOW}⚠️  NOT RECOMMENDED{Colors.RESET}"
        message = "Significant issues detected. Recommend fixes before deployment."
    else:
        status = f"{Colors.RED}❌ NOT PRODUCTION READY{Colors.RESET}"
        message = "Critical failures detected. Do not deploy."

    print(f"  Status: {status}")
    print(f"  Assessment: {message}")

    # Specific recommendations
    print(f"\n{Colors.BOLD}Recommendations:{Colors.RESET}")
    failed_tests = [test for test in results.test_details if not test['passed']]

    if not failed_tests:
        print(f"  {Colors.GREEN}• All validation tests passed successfully{Colors.RESET}")
        print(f"  {Colors.GREEN}• System is ready for multi-expert deployment{Colors.RESET}")
        print(f"  {Colors.GREEN}• Memory system functioning as designed{Colors.RESET}")
    else:
        print(f"  {Colors.RED}• Failed tests must be addressed:{Colors.RESET}")
        for test in failed_tests:
            print(f"    - {test['name']}: {test['details']}")
        print(f"  {Colors.YELLOW}• Run validation again after fixes{Colors.RESET}")

    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*80}{Colors.RESET}\n")


async def run_all_tests():
    """Execute all validation tests"""
    print(f"{Colors.BOLD}{Colors.MAGENTA}")
    print("╔════════════════════════════════════════════════════════════════════════════╗")
    print("║                  NFL PREDICTION LEARNING SYSTEM                            ║")
    print("║                       VALIDATION TEST SUITE                                ║")
    print("║                                                                            ║")
    print("║  Testing: Memory, Learning, Beliefs, Principles, Healing, Persistence     ║")
    print("╚════════════════════════════════════════════════════════════════════════════╝")
    print(f"{Colors.RESET}\n")

    results = ValidationResults()

    # Run all tests
    await test_memory_storage(results)
    await test_memory_retrieval(results)
    await test_lesson_extraction(results)
    await test_belief_revision(results)
    await test_principle_discovery(results)
    await test_self_healing(results)
    await test_cross_week_persistence(results)

    # Print final report
    print_final_report(results)

    # Return exit code
    return 0 if results.tests_failed == 0 else 1


if __name__ == "__main__":
    exit_code = asyncio.run(run_all_tests())
    sys.exit(exit_code)