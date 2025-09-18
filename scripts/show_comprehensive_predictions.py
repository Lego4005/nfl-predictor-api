#!/usr/bin/env python3
"""
Show Comprehensive Expert Predictions - All 20+ Categories Per Expert
Demonstrates the complete prediction system with all categories
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.ml.comprehensive_expert_models import ComprehensiveExpertCouncil
import json

def show_comprehensive_predictions():
    """Show all 20+ prediction categories from each expert"""

    print('🏈 COMPREHENSIVE EXPERT PREDICTIONS - ALL 20+ CATEGORIES')
    print('=' * 80)

    # Initialize comprehensive expert council
    council = ComprehensiveExpertCouncil()

    # Sample game data with comprehensive information
    game_data = {
        'spread': -3.5,
        'total': 47.5,
        'line_movement': 0.5,
        'public_betting_percentage': 65,
        'home_epa_per_play': 0.08,
        'away_epa_per_play': 0.05,
        'home_dvoa': 0.12,
        'away_dvoa': 0.08,
        'home_success_rate': 0.47,
        'away_success_rate': 0.44,
        'weather': {
            'wind_speed': 12,
            'precipitation': 0.1,
            'temperature': 68,
            'conditions': 'partly_cloudy'
        },
        'injuries': {
            'home': [
                {'player': 'WR1', 'position': 'WR', 'severity': 'questionable', 'is_starter': True},
                {'player': 'LB2', 'position': 'LB', 'severity': 'probable', 'is_starter': False}
            ],
            'away': [
                {'player': 'RB1', 'position': 'RB', 'severity': 'doubtful', 'is_starter': True}
            ]
        },
        'is_dome': False,
        'game_time_et': '20:20',
        'home_rest_days': 7,
        'away_rest_days': 6
    }

    # Generate comprehensive predictions
    home_team = "HOU"
    away_team = "TB"

    print(f'\\n🎯 ANALYZING: {away_team} @ {home_team}')
    print(f'📊 SPREAD: {game_data["spread"]} | TOTAL: {game_data["total"]}')
    print('=' * 80)

    all_predictions = council.get_all_comprehensive_predictions(home_team, away_team, game_data)

    print(f'\\n📋 TOTAL EXPERTS: {len(all_predictions)}')
    print('=' * 80)

    # Show each expert's comprehensive predictions
    for i, pred in enumerate(all_predictions, 1):
        print(f'\\n{i}. 🎯 {pred.expert_name.upper()} (Overall: {pred.confidence_overall:.1%})')
        print('=' * 60)

        # 1. CORE GAME PREDICTIONS
        print('\\n1️⃣ CORE GAME PREDICTIONS:')
        print(f'   • Winner: {pred.game_outcome["winner"]} ({pred.game_outcome["confidence"]:.1%})')
        print(f'   • Score: {pred.exact_score["home_score"]}-{pred.exact_score["away_score"]}')
        print(f'   • Margin: {pred.margin_of_victory["margin"]} points')
        print(f'   • ATS: {pred.against_the_spread["pick"]} ({pred.against_the_spread["confidence"]:.1%})')
        print(f'   • Total: {pred.totals["pick"]} {pred.totals["total_line"]} ({pred.totals["confidence"]:.1%})')
        print(f'   • Moneyline Value: {pred.moneyline_value["expected_value"]:.1%} edge')

        # 2. LIVE GAME PREDICTIONS
        print('\\n2️⃣ LIVE GAME PREDICTIONS:')
        print(f'   • Halftime Win Prob: {pred.real_time_win_probability["halftime"]["home"]:.1%} / {pred.real_time_win_probability["halftime"]["away"]:.1%}')
        print(f'   • Next Score: {pred.next_score_probability["opening_drive"]["team"]} ({pred.next_score_probability["opening_drive"]["score_type"]})')
        print(f'   • Drive TD Prob: {pred.drive_outcome_predictions["touchdown_prob"]:.1%}')
        print(f'   • 4th Down Rec: {pred.fourth_down_decisions["go_for_it_situations"]["red_zone"]["recommendation"]}')

        # 3. PLAYER PROPS PREDICTIONS
        print('\\n3️⃣ PLAYER PROPS PREDICTIONS:')
        passing = pred.passing_props['qb_yards']['home_qb']
        rushing = pred.rushing_props['rb_yards']['home_rb1']
        receiving = pred.receiving_props['wr_yards']['home_wr1']
        print(f'   • QB Yards: {passing["pick"]} {passing["over_under"]} ({passing["confidence"]:.1%})')
        print(f'   • RB Yards: {rushing["pick"]} {rushing["over_under"]} ({rushing["confidence"]:.1%})')
        print(f'   • WR Yards: {receiving["pick"]} {receiving["over_under"]} ({receiving["confidence"]:.1%})')
        print(f'   • Fantasy Points: QB {pred.fantasy_points["qb_points"]["home_qb"]["projected"]:.1f}')

        # 4. GAME SEGMENTS
        print('\\n4️⃣ GAME SEGMENTS:')
        print(f'   • First Half Winner: {pred.first_half_winner["pick"]} ({pred.first_half_winner["confidence"]:.1%})')
        print(f'   • Highest Quarter: Q{pred.highest_scoring_quarter["pick"]} ({pred.highest_scoring_quarter["confidence"]:.1%})')

        # 5. ENVIRONMENTAL & SITUATIONAL
        print('\\n5️⃣ ENVIRONMENTAL & SITUATIONAL:')
        print(f'   • Weather Impact: {pred.weather_impact["impact_level"]} ({pred.weather_impact["confidence"]:.1%})')
        print(f'   • Injury Impact: {pred.injury_impact["impact_rating"]} ({pred.injury_impact["confidence"]:.1%})')
        print(f'   • Momentum: {pred.momentum_analysis["trend"]} ({pred.momentum_analysis["confidence"]:.1%})')
        print(f'   • Red Zone Eff: Home {pred.situational_predictions["red_zone_efficiency"]["home"]:.1%} vs Away {pred.situational_predictions["red_zone_efficiency"]["away"]:.1%}')

        # 6. ADVANCED ANALYSIS
        print('\\n6️⃣ ADVANCED ANALYSIS:')
        print(f'   • FG Accuracy: Home {pred.special_teams["field_goal_accuracy"]["home"]:.1%} vs Away {pred.special_teams["field_goal_accuracy"]["away"]:.1%}')
        print(f'   • Coaching Edge: {pred.coaching_matchup["matchup_advantage"]} ({pred.coaching_matchup["confidence"]:.1%})')
        print(f'   • Home Advantage: {pred.home_field_advantage["point_adjustment"]:.1f} points')
        print(f'   • Travel Impact: {pred.travel_rest_impact["impact_rating"]} (Away {pred.travel_rest_impact["away_rest_days"]} days rest)')

        # 7. EXPERT REASONING
        print('\\n7️⃣ EXPERT REASONING:')
        print(f'   • Logic: {pred.reasoning}')
        print(f'   • Key Factors: {", ".join(pred.key_factors[:3])}')

        print('\\n' + '-' * 60)

    # Show the complete prediction categories available
    print('\\n\\n🎯 COMPLETE PREDICTION CATEGORY BREAKDOWN:')
    print('=' * 80)

    categories = [
        "1. ✅ Game Outcome (Winner & Probability)",
        "2. ✅ Final Score Predictions (Both Teams)",
        "3. ✅ Margin of Victory",
        "4. ✅ Against The Spread (ATS)",
        "5. ✅ Totals (Over/Under)",
        "6. ✅ Moneyline Value Analysis",
        "7. ✅ Real-Time Win Probability Updates",
        "8. ✅ Next Score Probability",
        "9. ✅ Drive Outcome Predictions",
        "10. ✅ Fourth Down Decision Recommendations",
        "11. ✅ Passing Props (Yards, TDs, Completions, INTs)",
        "12. ✅ Rushing Props (Yards, Attempts, TDs, Longest)",
        "13. ✅ Receiving Props (Yards, Receptions, TDs, Targets)",
        "14. ✅ Fantasy Points Predictions",
        "15. ✅ First Half Winner",
        "16. ✅ Highest Scoring Quarter",
        "17. ✅ Weather Impact Analysis",
        "18. ✅ Injury Impact Assessment",
        "19. ✅ Momentum/Trend Analysis",
        "20. ✅ Situational Predictions (Red Zone, 3rd Down)",
        "21. ✅ Special Teams Predictions",
        "22. ✅ Coaching Matchup Analysis",
        "23. ✅ Home Field Advantage Quantification",
        "24. ✅ Travel/Rest Impact Analysis",
        "25. ✅ Divisional Game Dynamics"
    ]

    for category in categories:
        print(f'   {category}')

    print('\\n\\n💡 SYSTEM CAPABILITIES:')
    print('=' * 80)
    print('✅ ALL 25 PREDICTION CATEGORIES IMPLEMENTED')
    print('✅ Each expert generates unique predictions across all categories')
    print('✅ Expert specializations influence confidence and methodology')
    print('✅ Comprehensive data integration (weather, injuries, analytics)')
    print('✅ Ready for live game integration and real-time updates')

    print('\\n\\n🏆 EXPERT SPECIALIZATIONS:')
    print('=' * 80)
    for pred in all_predictions:
        specialties = ", ".join(pred.specialty_confidence.keys())
        print(f'   • {pred.expert_name}: {specialties}')

    print('\\n\\n🚀 NEXT STEPS:')
    print('=' * 80)
    print('1. Integrate with live data feeds for real-time predictions')
    print('2. Add remaining 10 expert models to reach full 15-expert council')
    print('3. Implement live game prediction updates during play')
    print('4. Connect to Supabase for historical pattern matching')
    print('5. Add user interface for displaying all prediction categories')

if __name__ == "__main__":
    show_comprehensive_predictions()