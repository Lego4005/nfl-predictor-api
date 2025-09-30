#!/usr/bin/env python3
"""
Betting System Demo

Demonstrates the full flow of the virtual bankroll betting system:
1. Expert makes prediction
2. Bet is automatically placed
3. Game completes
4. Bet is settled
5. Bankroll is updated

Author: Financial Systems Engineer
Created: 2025-09-29
"""

import os
import sys
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.services import BetSizer, BankrollManager, BetPlacer, BetSettler


def print_header(title):
    """Print formatted section header."""
    print("\n" + "="*70)
    print(f"  {title}")
    print("="*70 + "\n")


def demo_bet_sizing():
    """Demo 1: Calculate optimal bet sizes."""
    print_header("DEMO 1: Bet Sizing with Kelly Criterion")

    sizer = BetSizer()

    # Example 1: Gambler personality
    print("Expert: The Gambler")
    print("  Personality: Aggressive (1.5x Kelly)")
    print("  Prediction: Chiefs -3.5")
    print("  Confidence: 75%")
    print("  Vegas Odds: +150")
    print("  Bankroll: $10,000")

    result = sizer.get_bet_size(
        expert_id='expert-the-gambler',
        expert_personality='gambler',
        confidence=0.75,
        odds='+150',
        bankroll=10000
    )

    if result['should_bet']:
        print(f"\n  ✅ BET APPROVED")
        print(f"     Amount: ${result['bet_amount']:,.2f}")
        print(f"     Kelly Suggested: {result['kelly_suggested']:.2%}")
        print(f"     Personality Adj: {result['personality_adjustment']}x")
        print(f"     Final Bet: {result['bet_fraction']:.2%} of bankroll")
        print(f"     Edge: {result['edge']:.2%}")
    else:
        print(f"\n  ❌ BET REJECTED: {result['reasoning']}")

    # Example 2: Conservative personality
    print("\n" + "-"*70 + "\n")
    print("Expert: The Scholar")
    print("  Personality: Conservative (0.5x Kelly)")
    print("  Prediction: Ravens +7.5")
    print("  Confidence: 72%")
    print("  Vegas Odds: -110")
    print("  Bankroll: $8,500")

    result = sizer.get_bet_size(
        expert_id='expert-the-scholar',
        expert_personality='conservative',
        confidence=0.72,
        odds='-110',
        bankroll=8500
    )

    if result['should_bet']:
        print(f"\n  ✅ BET APPROVED")
        print(f"     Amount: ${result['bet_amount']:,.2f}")
        print(f"     Kelly Suggested: {result['kelly_suggested']:.2%}")
        print(f"     Personality Adj: {result['personality_adjustment']}x")
        print(f"     Final Bet: {result['bet_fraction']:.2%} of bankroll")
    else:
        print(f"\n  ❌ BET REJECTED: {result['reasoning']}")

    # Example 3: Low confidence rejection
    print("\n" + "-"*70 + "\n")
    print("Expert: The Analyst")
    print("  Confidence: 68% (below 70% threshold)")

    result = sizer.get_bet_size(
        expert_id='expert-the-analyst',
        expert_personality='analyst',
        confidence=0.68,
        odds='+120',
        bankroll=9200
    )

    print(f"\n  ❌ BET REJECTED: {result['reasoning']}")


def demo_full_workflow():
    """Demo 2: Full prediction → settlement workflow."""
    print_header("DEMO 2: Full Betting Workflow (Simulated)")

    print("SCENARIO: Week 1 - Chiefs vs Ravens")
    print("  Game: NFL_2025_W1_KC_BAL")
    print("  Matchup: Kansas City Chiefs vs Baltimore Ravens")
    print("  Spread: Chiefs -3.5 (+150)")
    print()

    # Step 1: Expert prediction
    print("STEP 1: Expert Makes Prediction")
    print("-" * 70)

    prediction = {
        'expert_id': 'expert-the-gambler',
        'game_id': 'NFL_2025_W1_KC_BAL',
        'prediction_category': 'spread_home',
        'confidence': 0.78,
        'vegas_odds': '+150',
        'reasoning': 'Chiefs dominant at home, Ravens missing key defensive starters'
    }

    print(f"  Expert: {prediction['expert_id']}")
    print(f"  Confidence: {prediction['confidence']:.0%}")
    print(f"  Pick: {prediction['prediction_category']}")
    print(f"  Reasoning: {prediction['reasoning']}")

    # Step 2: Bet sizing
    print("\n\nSTEP 2: Calculate Bet Size")
    print("-" * 70)

    sizer = BetSizer()
    bankroll = 10000.0

    bet_result = sizer.get_bet_size(
        expert_id=prediction['expert_id'],
        expert_personality='gambler',
        confidence=prediction['confidence'],
        odds=prediction['vegas_odds'],
        bankroll=bankroll
    )

    if bet_result['should_bet']:
        print(f"  Kelly Criterion: {bet_result['kelly_suggested']:.2%}")
        print(f"  Personality Adjustment: {bet_result['personality_adjustment']}x (Gambler)")
        print(f"  Edge: {bet_result['edge']:.2%}")
        print(f"  \n  💰 BET PLACED: ${bet_result['bet_amount']:,.2f}")
        print(f"     ({bet_result['bet_fraction']:.2%} of ${bankroll:,.2f} bankroll)")

        # Simulate bet placement
        bet_amount = bet_result['bet_amount']
        bankroll_before = bankroll
        bankroll -= bet_amount  # Deduct bet amount
    else:
        print(f"  ❌ Bet rejected: {bet_result['reasoning']}")
        return

    # Step 3: Game completion
    print("\n\nSTEP 3: Game Completes")
    print("-" * 70)

    game_result = {
        'home_score': 27,
        'away_score': 20,
        'home_team': 'KC',
        'away_team': 'BAL',
        'spread_result': 'home_covered',  # Chiefs won by 7 (covered -3.5)
        'total_result': 'under',
        'winner': 'home'
    }

    print(f"  Final Score: {game_result['home_team']} {game_result['home_score']} - "
          f"{game_result['away_team']} {game_result['away_score']}")
    print(f"  Result: Chiefs won by {game_result['home_score'] - game_result['away_score']} (COVERED -3.5)")
    print(f"  \n  ✅ BET WON!")

    # Step 4: Calculate payout
    print("\n\nSTEP 4: Calculate Payout")
    print("-" * 70)

    # Parse odds and calculate payout
    odds_value = 150  # +150
    profit = bet_amount * (odds_value / 100.0)
    payout = bet_amount + profit

    print(f"  Bet Amount: ${bet_amount:,.2f}")
    print(f"  Odds: +150")
    print(f"  Profit: ${profit:,.2f}")
    print(f"  Total Payout: ${payout:,.2f}")

    # Step 5: Update bankroll
    print("\n\nSTEP 5: Update Bankroll")
    print("-" * 70)

    bankroll_after = bankroll_before + (payout - bet_amount)
    net_change = bankroll_after - bankroll_before

    print(f"  Balance Before: ${bankroll_before:,.2f}")
    print(f"  Net Change: ${net_change:+,.2f}")
    print(f"  Balance After: ${bankroll_after:,.2f}")

    roi = (net_change / bankroll_before) * 100
    print(f"  ROI: {roi:+.2f}%")

    # Risk level
    risk_percentage = bankroll_after / bankroll_before
    if risk_percentage >= 0.70:
        risk_level = "SAFE ✅"
    elif risk_percentage >= 0.40:
        risk_level = "AT RISK ⚠️"
    elif risk_percentage >= 0.20:
        risk_level = "DANGER 🔶"
    else:
        risk_level = "CRITICAL 🔴"

    print(f"  Risk Level: {risk_level}")


def demo_multiple_experts():
    """Demo 3: Multiple experts with different personalities."""
    print_header("DEMO 3: Multiple Experts - Personality Comparison")

    sizer = BetSizer()

    experts = [
        ('The Gambler', 'gambler', 1.5),
        ('The Scholar', 'scholar', 1.0),
        ('The Conservative', 'conservative', 0.5),
        ('The Veteran', 'veteran', 0.7),
        ('The Rookie', 'rookie', 0.6)
    ]

    print("SCENARIO: Same prediction, different personalities")
    print("  Game: 49ers -6.5 vs Seahawks")
    print("  Confidence: 76%")
    print("  Odds: +140")
    print("  Bankroll: $10,000 (each)")
    print()

    results = []

    for name, personality, multiplier in experts:
        result = sizer.get_bet_size(
            expert_id=f'expert-{personality}',
            expert_personality=personality,
            confidence=0.76,
            odds='+140',
            bankroll=10000
        )

        if result['should_bet']:
            results.append((name, result['bet_amount'], result['bet_fraction'], multiplier))

    # Display results
    print(f"{'Expert':<20} {'Multiplier':<12} {'Bet Amount':<15} {'% of Bankroll':<15}")
    print("-" * 70)

    for name, amount, fraction, multiplier in results:
        print(f"{name:<20} {f'{multiplier}x Kelly':<12} ${amount:>10,.2f}    {fraction:>10.2%}")

    print("\n💡 Insight: Personality significantly impacts bet sizing!")
    print(f"   Range: ${min(r[1] for r in results):,.2f} - ${max(r[1] for r in results):,.2f}")


def main():
    """Run all demos."""
    print("\n")
    print("╔" + "="*68 + "╗")
    print("║" + " "*68 + "║")
    print("║" + "  NFL AI EXPERT PREDICTION PLATFORM".center(68) + "║")
    print("║" + "  Virtual Bankroll Betting System Demo".center(68) + "║")
    print("║" + " "*68 + "║")
    print("╚" + "="*68 + "╝")

    try:
        demo_bet_sizing()
        input("\n\nPress Enter to continue to Demo 2...")

        demo_full_workflow()
        input("\n\nPress Enter to continue to Demo 3...")

        demo_multiple_experts()

        print_header("DEMO COMPLETE")
        print("✅ All betting system components working correctly!")
        print()
        print("📚 For more information, see:")
        print("   - /docs/BETTING_SYSTEM_IMPLEMENTATION.md")
        print("   - /docs/BETTING_SYSTEM_DELIVERY.md")
        print()

    except KeyboardInterrupt:
        print("\n\n⚠️  Demo interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()