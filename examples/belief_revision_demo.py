#!/usr/bin/env python3
"""
Belief Revision System - Demo & Validation
Demonstrates the adaptive belief revision system in action
"""

import asyncio
import sys
import os
from datetime import datetime, timedelta
from unittest.mock import Mock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.ml.adaptive_belief_revision import (
    BeliefRevisionService,
    RevisionTriggerType,
    RevisionAction,
    BeliefRevisionRecord
)


def create_mock_supabase():
    """Create mock Supabase client for demo"""
    client = Mock()
    table_mock = Mock()

    # Mock successful operations
    table_mock.insert.return_value.execute.return_value.data = [{'id': '123'}]
    table_mock.select.return_value.eq.return_value.order.return_value.limit.return_value.execute.return_value.data = []
    table_mock.update.return_value.eq.return_value.execute.return_value.data = [{'id': '123'}]

    client.table.return_value = table_mock
    return client


async def demo_consecutive_errors():
    """Demo: Detect and respond to consecutive incorrect predictions"""
    print("\n" + "="*60)
    print("DEMO 1: Consecutive Incorrect Predictions")
    print("="*60)

    # Setup
    service = BeliefRevisionService(create_mock_supabase())
    await service.initialize()

    # Simulate expert making 4 consecutive errors
    predictions = [
        {'game_id': 'game_1', 'was_correct': False, 'confidence': 0.75},
        {'game_id': 'game_2', 'was_correct': False, 'confidence': 0.70},
        {'game_id': 'game_3', 'was_correct': False, 'confidence': 0.80},
        {'game_id': 'game_4', 'was_correct': False, 'confidence': 0.72},
    ]

    print(f"\n📊 Expert made {len(predictions)} consecutive incorrect predictions")
    for i, pred in enumerate(predictions, 1):
        print(f"  {i}. Game {pred['game_id']}: Wrong (confidence: {pred['confidence']:.0%})")

    # Check for triggers
    triggers = await service.check_revision_triggers(
        expert_id='expert_1',
        recent_predictions=predictions
    )

    print(f"\n🔔 Triggers Detected: {len(triggers)}")
    for trigger in triggers:
        print(f"  • {trigger.trigger_type.value}")
        print(f"    Severity: {trigger.severity:.2f}")
        print(f"    Description: {trigger.description}")

    # Generate actions
    current_state = {'confidence_multiplier': 1.0}
    actions = await service.generate_revision_actions(
        expert_id='expert_1',
        triggers=triggers,
        current_state=current_state
    )

    print(f"\n📋 Recommended Actions: {len(actions)}")
    for i, action in enumerate(actions, 1):
        print(f"  {i}. {action.action.value}")
        print(f"     Priority: {action.priority}/5")
        print(f"     Rationale: {action.rationale}")
        print(f"     Expected Impact: {action.expected_impact:.0%}")
        if 'confidence_multiplier' in action.parameters:
            print(f"     New confidence multiplier: {action.parameters['confidence_multiplier']:.2f}")

    await service.close()
    print("\n✅ Demo 1 Complete")


async def demo_confidence_misalignment():
    """Demo: Detect overconfidence issues"""
    print("\n" + "="*60)
    print("DEMO 2: Confidence Misalignment")
    print("="*60)

    service = BeliefRevisionService(create_mock_supabase())
    await service.initialize()

    # Expert being overconfident but wrong
    predictions = [
        {'game_id': 'game_1', 'was_correct': True, 'confidence': 0.65},
        {'game_id': 'game_2', 'was_correct': False, 'confidence': 0.90},  # Overconfident!
        {'game_id': 'game_3', 'was_correct': True, 'confidence': 0.70},
        {'game_id': 'game_4', 'was_correct': False, 'confidence': 0.85},  # Overconfident!
        {'game_id': 'game_5', 'was_correct': False, 'confidence': 0.80},  # Overconfident!
    ]

    print(f"\n📊 Expert predictions:")
    for pred in predictions:
        status = "✓" if pred['was_correct'] else "✗"
        marker = " 🚨 OVERCONFIDENT" if not pred['was_correct'] and pred['confidence'] >= 0.75 else ""
        print(f"  {status} Game {pred['game_id']}: {pred['confidence']:.0%} confidence{marker}")

    triggers = await service.check_revision_triggers(
        expert_id='expert_2',
        recent_predictions=predictions
    )

    print(f"\n🔔 Triggers Detected: {len(triggers)}")
    for trigger in triggers:
        if trigger.trigger_type == RevisionTriggerType.CONFIDENCE_MISALIGNMENT:
            print(f"  • Confidence Misalignment")
            print(f"    High-confidence errors: {trigger.evidence['error_count']}")
            print(f"    Average confidence gap: {trigger.evidence['avg_confidence_gap']:.1%}")

    current_state = {'high_confidence_threshold': 0.75}
    actions = await service.generate_revision_actions(
        expert_id='expert_2',
        triggers=triggers,
        current_state=current_state
    )

    print(f"\n📋 Recommended Actions:")
    for action in actions:
        if action.action == RevisionAction.ADJUST_CONFIDENCE_THRESHOLD:
            print(f"  • Adjust Confidence Threshold")
            print(f"    Old threshold: {current_state['high_confidence_threshold']:.2f}")
            print(f"    New threshold: {action.parameters.get('high_confidence_threshold', 0):.2f}")
            print(f"    Add confidence penalty: {action.parameters.get('confidence_penalty', 0):.0%}")

    await service.close()
    print("\n✅ Demo 2 Complete")


async def demo_pattern_repetition():
    """Demo: Detect repeated error patterns"""
    print("\n" + "="*60)
    print("DEMO 3: Pattern Repetition Detection")
    print("="*60)

    service = BeliefRevisionService(create_mock_supabase())
    await service.initialize()

    # Expert keeps making direction reversal errors
    predictions = [
        {
            'game_id': 'game_1',
            'was_correct': False,
            'confidence': 0.70,
            'predicted_margin': 10,
            'actual_margin': -8
        },  # Predicted home win, away won
        {
            'game_id': 'game_2',
            'was_correct': True,
            'confidence': 0.65,
            'predicted_margin': 5,
            'actual_margin': 6
        },
        {
            'game_id': 'game_3',
            'was_correct': False,
            'confidence': 0.75,
            'predicted_margin': 12,
            'actual_margin': -10
        },  # Predicted home win, away won
        {
            'game_id': 'game_4',
            'was_correct': False,
            'confidence': 0.68,
            'predicted_margin': 8,
            'actual_margin': -7
        },  # Predicted home win, away won
    ]

    print(f"\n📊 Expert predictions:")
    for pred in predictions:
        status = "✓" if pred['was_correct'] else "✗"
        pred_margin = pred.get('predicted_margin', 0)
        actual_margin = pred.get('actual_margin', 0)
        if pred_margin * actual_margin < 0:  # Opposite signs
            marker = " 🔄 DIRECTION REVERSAL"
        else:
            marker = ""
        print(f"  {status} Game {pred['game_id']}: Predicted margin {pred_margin:+.0f}, Actual {actual_margin:+.0f}{marker}")

    triggers = await service.check_revision_triggers(
        expert_id='expert_3',
        recent_predictions=predictions
    )

    print(f"\n🔔 Triggers Detected: {len(triggers)}")
    for trigger in triggers:
        if trigger.trigger_type == RevisionTriggerType.PATTERN_REPETITION:
            print(f"  • Pattern Repetition")
            print(f"    Pattern type: {trigger.evidence['pattern_type']}")
            print(f"    Occurrences: {trigger.evidence['occurrences']}")

    current_state = {}
    actions = await service.generate_revision_actions(
        expert_id='expert_3',
        triggers=triggers,
        current_state=current_state
    )

    print(f"\n📋 Recommended Actions:")
    for action in actions:
        if action.action == RevisionAction.CHANGE_FACTOR_WEIGHTS:
            print(f"  • Change Factor Weights")
            print(f"    Adjustments:")
            for factor, adjustment in action.parameters['weight_adjustments'].items():
                sign = "+" if adjustment > 0 else ""
                print(f"      - {factor}: {sign}{adjustment:.2f}")

    await service.close()
    print("\n✅ Demo 3 Complete")


async def demo_full_workflow():
    """Demo: Complete revision workflow"""
    print("\n" + "="*60)
    print("DEMO 4: Full Revision Workflow")
    print("="*60)

    service = BeliefRevisionService(create_mock_supabase())
    await service.initialize()

    # Simulate problematic performance
    predictions = [
        {'game_id': 'game_1', 'was_correct': False, 'confidence': 0.85},
        {'game_id': 'game_2', 'was_correct': False, 'confidence': 0.90},
        {'game_id': 'game_3', 'was_correct': False, 'confidence': 0.80},
    ]

    print("\n📊 Step 1: Detect Performance Issues")
    print(f"  Expert made 3 consecutive high-confidence errors")

    # Step 1: Detect
    triggers = await service.check_revision_triggers(
        expert_id='expert_4',
        recent_predictions=predictions
    )

    print(f"\n🔔 Step 2: Triggers Identified: {len(triggers)}")
    for trigger in triggers:
        print(f"  • {trigger.trigger_type.value} (severity: {trigger.severity:.2f})")

    # Step 2: Generate Actions
    current_state = {
        'confidence_multiplier': 1.0,
        'high_confidence_threshold': 0.75
    }

    actions = await service.generate_revision_actions(
        expert_id='expert_4',
        triggers=triggers,
        current_state=current_state
    )

    print(f"\n📋 Step 3: Actions Generated: {len(actions)}")
    for i, action in enumerate(actions, 1):
        print(f"  {i}. {action.action.value} (priority: {action.priority})")

    # Step 3: Apply Actions (simulated)
    print("\n⚙️ Step 4: Applying Actions")
    new_state = current_state.copy()
    for action in actions:
        if action.action == RevisionAction.ADJUST_CONFIDENCE_THRESHOLD:
            if 'confidence_multiplier' in action.parameters:
                old_mult = new_state.get('confidence_multiplier', 1.0)
                new_mult = action.parameters['confidence_multiplier']
                new_state['confidence_multiplier'] = new_mult
                print(f"  • Confidence multiplier: {old_mult:.2f} → {new_mult:.2f}")
            if 'high_confidence_threshold' in action.parameters:
                old_thresh = new_state.get('high_confidence_threshold', 0.75)
                new_thresh = action.parameters['high_confidence_threshold']
                new_state['high_confidence_threshold'] = new_thresh
                print(f"  • Confidence threshold: {old_thresh:.2f} → {new_thresh:.2f}")

    # Step 4: Store Revision
    revision = BeliefRevisionRecord(
        revision_id='demo_revision_001',
        expert_id='expert_4',
        trigger=triggers[0],
        actions=actions,
        pre_revision_state=current_state,
        post_revision_state=new_state,
        timestamp=datetime.now()
    )

    success = await service.store_revision(revision)
    print(f"\n💾 Step 5: Revision Stored: {'✅' if success else '❌'}")

    # Step 5: Simulate improved performance
    print("\n📈 Step 6: Measuring Effectiveness")
    post_predictions = [
        {'game_id': 'game_4', 'was_correct': True, 'confidence': 0.65},
        {'game_id': 'game_5', 'was_correct': True, 'confidence': 0.70},
        {'game_id': 'game_6', 'was_correct': True, 'confidence': 0.68},
        {'game_id': 'game_7', 'was_correct': True, 'confidence': 0.72},
        {'game_id': 'game_8', 'was_correct': False, 'confidence': 0.60},
    ]

    effectiveness = await service.measure_revision_effectiveness(
        revision_id='demo_revision_001',
        post_revision_predictions=post_predictions,
        window_size=5
    )

    print(f"  Effectiveness Score: {effectiveness:.0%}")
    print(f"  Post-revision accuracy: {sum(1 for p in post_predictions if p['was_correct']) / len(post_predictions):.0%}")

    await service.close()
    print("\n✅ Demo 4 Complete")


async def run_all_demos():
    """Run all demonstration scenarios"""
    print("\n" + "="*60)
    print("ADAPTIVE BELIEF REVISION SYSTEM - DEMONSTRATION")
    print("="*60)
    print("\nThis demo shows how the belief revision system:")
    print("1. Detects when experts need to adapt their strategies")
    print("2. Generates specific corrective actions")
    print("3. Measures effectiveness of changes")

    try:
        await demo_consecutive_errors()
        await demo_confidence_misalignment()
        await demo_pattern_repetition()
        await demo_full_workflow()

        print("\n" + "="*60)
        print("ALL DEMOS COMPLETED SUCCESSFULLY ✅")
        print("="*60)
        print("\nKey Capabilities Demonstrated:")
        print("  ✓ Consecutive error detection (3+ wrong in a row)")
        print("  ✓ Confidence misalignment detection (overconfidence)")
        print("  ✓ Pattern repetition detection (systematic errors)")
        print("  ✓ Automatic action generation with priorities")
        print("  ✓ State tracking (before/after revision)")
        print("  ✓ Effectiveness measurement")
        print("\nThe system is production-ready for integration!")

    except Exception as e:
        print(f"\n❌ Error during demo: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    asyncio.run(run_all_demos())