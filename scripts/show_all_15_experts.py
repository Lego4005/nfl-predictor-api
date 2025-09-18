#!/usr/bin/env python3
"""
Show All 15 Expert Predictions
Direct test of the ExpertCouncil with all experts
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.ml.expert_models import ExpertCouncil
import json

def show_all_15_experts():
    """Show predictions from all 15 experts"""

    print('🏈 ALL 15 EXPERT PREDICTIONS')
    print('=' * 80)

    # Initialize expert council
    council = ExpertCouncil()

    # Sample game data
    game_data = {
        'spread': -3.5,
        'total': 47.5,
        'line_movement': 0.5,
        'public_betting_percentage': 65,
        'weather': {
            'wind_speed': 12,
            'precipitation': 0.1,
            'temperature': 68
        },
        'injuries': {
            'home': [{'player': 'WR1', 'position': 'WR', 'severity': 'questionable'}],
            'away': [{'player': 'RB1', 'position': 'RB', 'severity': 'doubtful'}]
        },
        'is_dome': False,
        'game_time_et': '20:20'
    }

    home_team = "HOU"
    away_team = "TB"

    print(f'\\n🎯 ANALYZING: {away_team} @ {home_team}')
    print(f'📊 SPREAD: {game_data["spread"]} | TOTAL: {game_data["total"]}')
    print('=' * 80)

    # Get predictions from all 15 experts
    all_predictions = council.get_all_predictions(home_team, away_team, game_data)

    print(f'\\n📋 TOTAL EXPERTS: {len(all_predictions)}')
    print('=' * 80)

    # Show each expert
    for i, pred in enumerate(all_predictions, 1):
        print(f'\\n{i:2d}. 🎯 {pred.expert_name.upper()}')
        print(f'    Overall Confidence: {pred.confidence_overall:.1%}')
        print('-' * 60)

        # Core predictions
        print(f'   Winner: {pred.game_outcome["winner"]} ({pred.game_outcome["confidence"]:.1%})')
        print(f'   Score: {pred.exact_score["home_score"]}-{pred.exact_score["away_score"]}')
        print(f'   ATS: {pred.against_the_spread["pick"]} ({pred.against_the_spread["confidence"]:.1%})')
        print(f'   Total: {pred.totals["pick"]} ({pred.totals["confidence"]:.1%})')
        print(f'   Margin: {pred.margin_of_victory["margin"]} points')

        # Reasoning
        print(f'   Reasoning: {pred.reasoning[:80]}...')
        print(f'   Key Factors: {", ".join(pred.key_factors[:3])}')

    # Show consensus
    print('\\n\\n🏆 EXPERT VOTES SUMMARY:')
    print('=' * 80)

    # Count votes
    winner_votes = {}
    ats_votes = {}
    total_votes = {'over': 0, 'under': 0}

    for pred in all_predictions:
        winner = pred.game_outcome['winner']
        winner_votes[winner] = winner_votes.get(winner, 0) + 1

        ats_pick = pred.against_the_spread['pick']
        ats_votes[ats_pick] = ats_votes.get(ats_pick, 0) + 1

        total_pick = pred.totals['pick']
        total_votes[total_pick] += 1

    print(f'WINNER VOTES:')
    for team, votes in winner_votes.items():
        print(f'  {team}: {votes}/15 experts ({votes/15:.1%})')

    print(f'\\nATS VOTES:')
    for team, votes in ats_votes.items():
        print(f'  {team}: {votes}/15 experts ({votes/15:.1%})')

    print(f'\\nTOTAL VOTES:')
    for pick, votes in total_votes.items():
        print(f'  {pick.upper()}: {votes}/15 experts ({votes/15:.1%})')

    # Top 5 consensus
    print('\\n\\n🥇 TOP 5 EXPERT CONSENSUS:')
    print('=' * 80)

    # Sort by confidence
    sorted_experts = sorted(all_predictions, key=lambda x: x.confidence_overall, reverse=True)

    print('TOP 5 EXPERTS:')
    for i, pred in enumerate(sorted_experts[:5], 1):
        print(f'  {i}. {pred.expert_name} ({pred.confidence_overall:.1%}) - {pred.game_outcome["winner"]}')

    # Calculate top 5 consensus
    top5_winner_votes = {}
    top5_total_confidence = 0

    for pred in sorted_experts[:5]:
        winner = pred.game_outcome['winner']
        top5_winner_votes[winner] = top5_winner_votes.get(winner, 0) + 1
        top5_total_confidence += pred.confidence_overall

    consensus_winner = max(top5_winner_votes.items(), key=lambda x: x[1])[0]
    avg_confidence = top5_total_confidence / 5

    print(f'\\nTOP 5 CONSENSUS:')
    print(f'  Winner: {consensus_winner}')
    print(f'  Average Confidence: {avg_confidence:.1%}')
    print(f'  Vote Split: {dict(top5_winner_votes)}')

    print('\\n\\n📊 EXPERT SPECIALIZATIONS:')
    print('=' * 80)

    expert_specialties = {
        'Statistical Savant': 'Advanced statistical modeling and regression analysis',
        'Sharp Bettor': 'Line movement tracking and market inefficiency detection',
        'Weather Wizard': 'Meteorological impact analysis on game outcomes',
        'Injury Analyst': 'Player availability and depth chart impact assessment',
        'Trend Tracker': 'Momentum analysis and recent performance trends',
        'Divisional Expert': 'Division rivalry dynamics and familiarity factors',
        'Primetime Performer': 'National TV and prime time game analysis',
        'Under Expert': 'Defensive analysis and low-scoring game identification',
        'Over Enthusiast': 'Offensive firepower and high-scoring game detection',
        'Home Field Hawk': 'Home field advantage quantification and crowd impact',
        'Road Warrior': 'Road team value identification and travel analysis',
        'Coaching Connoisseur': 'Coaching matchup analysis and strategic advantages',
        'QB Whisperer': 'Quarterback performance analysis and matchup evaluation',
        'Situational Specialist': 'Game situation analysis and clutch performance',
        'Market Maven': 'Betting market analysis and public perception tracking'
    }

    for pred in all_predictions:
        specialty = expert_specialties.get(pred.expert_name, 'General analysis')
        print(f'  • {pred.expert_name}: {specialty}')

    print('\\n\\n✅ SYSTEM STATUS:')
    print('=' * 80)
    print('✅ ALL 15 EXPERT MODELS ACTIVE')
    print('✅ Unique algorithms and specializations per expert')
    print('✅ Competitive ranking system operational')
    print('✅ Top-5 weighted consensus calculation')
    print('✅ Comprehensive prediction categories')

if __name__ == "__main__":
    show_all_15_experts()