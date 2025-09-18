#!/usr/bin/env python3
"""
Generate Expert Predictions for ACTUAL Week 2 Games
Using the games currently showing on the frontend
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.ml.expert_prediction_service import expert_prediction_service
from datetime import datetime


# ACTUAL WEEK 2 GAMES FROM THE FRONTEND
WEEK_2_GAMES = [
    ("BUF", "NYJ"),  # NYJ @ BUF - Thursday Night
    ("KC", "LAC"),   # LAC @ KC
    ("PHI", "DAL"),  # DAL @ PHI
    ("SF", "SEA"),   # SEA @ SF
    ("BAL", "CIN"),  # CIN @ BAL
    ("GB", "MIN"),   # MIN @ GB
]


def predict_all_week2_games():
    """Generate predictions for all Week 2 games"""

    print("\n" + "=" * 80)
    print("🏈 NFL WEEK 2 EXPERT PREDICTIONS - SEPTEMBER 15, 2025")
    print("=" * 80)

    all_predictions = []

    for home, away in WEEK_2_GAMES:
        print(f"\n\n{'='*70}")
        print(f"🏟️  {away} @ {home}")
        print(f"{'='*70}")

        # Generate predictions from all 15 experts
        results = expert_prediction_service.generate_all_expert_predictions(home, away)
        all_predictions.append(results)

        # Count votes
        winner_votes = {}
        spread_votes = {}
        total_votes = {'over': 0, 'under': 0}

        for pred in results['all_expert_predictions']:
            # Winner votes
            winner = pred['predictions']['game_outcome']['winner']
            winner_votes[winner] = winner_votes.get(winner, 0) + 1

            # Spread votes
            spread_pick = pred['predictions']['spread']['pick']
            spread_votes[spread_pick] = spread_votes.get(spread_pick, 0) + 1

            # Total votes
            total_pick = pred['predictions']['total']['pick']
            total_votes[total_pick] += 1

        # Display expert picks in compact format
        print("\n📊 EXPERT PICKS:")
        print("-" * 60)
        print(f"{'Expert':<22} {'Winner':<6} {'Conf':<6} {'ATS':<6} {'O/U':<6}")
        print("-" * 60)

        for pred in results['all_expert_predictions']:
            print(f"{pred['expert_name']:<22} {pred['predictions']['game_outcome']['winner']:<6} "
                  f"{pred['confidence_overall']*100:>5.1f}% {pred['predictions']['spread']['pick']:<6} "
                  f"{pred['predictions']['total']['pick']:<6}")

        # Display consensus
        print("\n🏆 CONSENSUS:")
        print("-" * 40)
        consensus = results['top5_consensus']
        print(f"Top 5 Winner: {consensus['winner']}")
        print(f"Vote Split: {home} ({winner_votes.get(home, 0)}) vs {away} ({winner_votes.get(away, 0)})")
        print(f"ATS Split: {home} ({spread_votes.get(home, 0)}) vs {away} ({spread_votes.get(away, 0)})")
        print(f"O/U Split: Over ({total_votes['over']}) vs Under ({total_votes['under']})")
        print(f"Confidence: {consensus['confidence']:.1%}")

        # Highlight disagreements
        if abs(winner_votes.get(home, 0) - winner_votes.get(away, 0)) <= 3:
            print("\n⚔️ SHARP DISAGREEMENT! Experts are split on this game!")

    return all_predictions


def show_thursday_night_special():
    """Special focus on tonight's Thursday Night game"""

    print("\n\n" + "=" * 80)
    print("🌙 THURSDAY NIGHT FOOTBALL SPECIAL: NYJ @ BUF")
    print("=" * 80)

    home, away = "BUF", "NYJ"
    results = expert_prediction_service.generate_all_expert_predictions(home, away)

    # Get live data context
    from src.services.live_data_service import live_data_service
    game_data = live_data_service.get_comprehensive_game_data(home, away)

    print("\n📈 LIVE BETTING DATA:")
    print(f"   • Spread: BUF {game_data['spread']}")
    print(f"   • Total: {game_data['total']}")
    print(f"   • Moneylines: BUF {game_data['home_moneyline']} / NYJ {game_data['away_moneyline']}")
    print(f"   • Public: {game_data['public_betting_percentage']}% on favorite")

    print("\n🔥 HOT TAKES FROM TOP EXPERTS:")
    print("-" * 60)

    # Get top 5 most confident experts
    sorted_preds = sorted(results['all_expert_predictions'],
                         key=lambda x: x['confidence_overall'],
                         reverse=True)

    for i, pred in enumerate(sorted_preds[:5], 1):
        print(f"\n{i}. {pred['expert_name']} ({pred['confidence_overall']:.1%} confident)")
        print(f"   Pick: {pred['predictions']['game_outcome']['winner']}")
        print(f"   Score: {pred['predictions']['exact_score']['home']} - {pred['predictions']['exact_score']['away']}")
        print(f"   Reasoning: {pred['reasoning']}")

    # Show unique algorithm insights
    print("\n\n🧠 UNIQUE ALGORITHM INSIGHTS:")
    print("-" * 60)

    for pred in results['all_expert_predictions']:
        if pred['expert_name'] == "Weather Wizard":
            print(f"\n⛈️ Weather Wizard: Analyzing Buffalo weather conditions...")
            print(f"   {pred['predictions']['game_outcome']['reasoning']}")
        elif pred['expert_name'] == "Sharp Bettor":
            print(f"\n💰 Sharp Bettor: Line movement indicates...")
            print(f"   {pred['predictions']['game_outcome']['reasoning']}")
        elif pred['expert_name'] == "Home Field Hawk":
            print(f"\n🏟️ Home Field Hawk: Bills Mafia factor...")
            print(f"   {pred['predictions']['game_outcome']['reasoning']}")
        elif pred['expert_name'] == "QB Whisperer":
            print(f"\n🎯 QB Whisperer: Rodgers vs Allen analysis...")
            print(f"   {pred['predictions']['game_outcome']['reasoning']}")


def show_expert_algorithms_in_action():
    """Show how each expert's algorithm produces different results"""

    print("\n\n" + "=" * 80)
    print("🤖 HOW EACH EXPERT'S UNIQUE ALGORITHM WORKS")
    print("=" * 80)

    print("""
Each expert uses DIFFERENT data and algorithms:

1. STATISTICAL SAVANT: Power ratings × defensive efficiency
   → Looks at: Team stats, historical matchups, regression models

2. SHARP BETTOR: Line movement vs public betting %
   → Looks at: If line moves opposite to public money = sharp action

3. WEATHER WIZARD: Environmental impact calculations
   → Looks at: Wind speed, precipitation, dome/outdoor

4. QB WHISPERER: QB rating differentials
   → Looks at: Passer rating, QB vs specific defense history

5. INJURY ANALYST: Health advantage scoring
   → Looks at: Key injuries × position importance (QB=35%, RB=15%)

6. HOME FIELD HAWK: Travel + timezone + crowd factors
   → Always picks home team, confidence varies by factors

7. ROAD WARRIOR: Contrarian road team specialist
   → Looks for road teams with better away record than home's home record

...and 8 more experts with unique approaches!
""")


if __name__ == "__main__":
    print("🚀 NFL WEEK 2 EXPERT PREDICTIONS SYSTEM")

    # 1. Predict all Week 2 games
    all_predictions = predict_all_week2_games()

    # 2. Special focus on Thursday Night
    show_thursday_night_special()

    # 3. Explain algorithms
    show_expert_algorithms_in_action()

    print("\n\n" + "=" * 80)
    print("📊 SUMMARY:")
    print("=" * 80)
    print("✅ 15 experts with UNIQUE algorithms analyzed 6 Week 2 games")
    print("✅ Each expert uses DIFFERENT data sources and methods")
    print("✅ Consensus formed from TOP 5 performing experts")
    print("✅ pgvector will improve predictions as season progresses")

    print("\n🔮 PGVECTOR TIMELINE:")
    print("   Week 1-4: Building prediction history")
    print("   Week 5-8: Pattern matching begins")
    print("   Week 9+: Full AI learning from similar situations")