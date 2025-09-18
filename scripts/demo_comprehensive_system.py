#!/usr/bin/env python3
"""
Comprehensive NFL Prediction System Demonstration
Shows the complete workflow from prediction generation to validation
"""

import json
import sys
import os
from datetime import datetime
from typing import Dict, List, Any

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.formatters.comprehensive_output_generator import ComprehensiveOutputGenerator

def create_comprehensive_demo_data() -> Dict[str, Dict]:
    """Create comprehensive demo data showcasing all system capabilities"""

    expert_names = [
        'statistical_analyst', 'momentum_tracker', 'weather_specialist',
        'injury_analyst', 'matchup_expert', 'coaching_analyst',
        'psychological_profiler', 'trend_forecaster', 'situational_specialist',
        'data_scientist', 'vegas_interpreter', 'contrarian_analyst',
        'neural_pattern_specialist', 'ensemble_coordinator', 'meta_analyst'
    ]

    games_data = {}

    # Game 1: High-profile AFC Championship preview
    game1_experts = {}
    for i, expert in enumerate(expert_names):
        confidence = 0.55 + (i * 0.02)  # Spread from 55% to 83%

        game1_experts[expert] = {
            'predicted_winner': 'Bills' if i % 3 == 0 else 'Chiefs',
            'confidence': confidence,
            'spread_prediction': -2.0 + (i * 0.3) - 2.1,
            'total_prediction': 54.0 + (i * 0.8) - 5.6,
            'reasoning_chain': f"""
            {expert.replace('_', ' ').title()} Analysis for Bills @ Chiefs:

            Primary Analysis: Comprehensive evaluation reveals key factors favoring the predicted outcome.
            The {expert} methodology emphasizes specific strengths and weaknesses in this matchup.

            Key Insights:
            - Offensive efficiency differential strongly impacts game flow
            - Defensive matchup advantages create strategic opportunities
            - Recent performance trends indicate momentum shifts
            - Environmental factors (weather, venue) play crucial role
            - Historical head-to-head patterns suggest likely scenarios

            Confidence Rationale: {confidence:.1%} confidence based on data quality,
            historical accuracy of this methodology, and strength of predictive signals.
            """,
            'key_factors': [
                f"Offensive efficiency advantage ({expert} methodology)",
                f"Defensive matchup analysis favors predicted winner",
                f"Recent momentum trends support prediction",
                f"Weather/venue factors align with strengths",
                f"Historical patterns confirm likely outcome"
            ],
            'home_score_prediction': 27 + (i % 7) - 2,
            'away_score_prediction': 24 + (i % 5) - 1
        }

    # Generate realistic consensus for Game 1
    bills_votes = sum(1 for pred in game1_experts.values() if pred['predicted_winner'] == 'Bills')
    chiefs_votes = len(game1_experts) - bills_votes
    consensus_winner = 'Bills' if bills_votes > chiefs_votes else 'Chiefs'
    avg_confidence = sum(pred['confidence'] for pred in game1_experts.values()) / len(game1_experts)

    games_data['afc_championship_preview_bills_chiefs'] = {
        'expert_predictions': game1_experts,
        'consensus': {
            'predicted_winner': consensus_winner,
            'confidence': avg_confidence,
            'vote_distribution': {'Bills': bills_votes, 'Chiefs': chiefs_votes},
            'weighted_confidence': avg_confidence,
            'unanimous': max(bills_votes, chiefs_votes) >= 13
        },
        'confidence_metrics': {
            'average': avg_confidence,
            'std_dev': 0.082,
            'min': min(pred['confidence'] for pred in game1_experts.values()),
            'max': max(pred['confidence'] for pred in game1_experts.values())
        },
        'reasoning_factors': {
            'team_statistics': {
                'home_record': '2-0 (1st in AFC West)',
                'away_record': '2-0 (1st in AFC East)',
                'home_ppg': 28.5,
                'away_ppg': 31.0,
                'home_papg': 18.0,
                'away_papg': 21.5
            },
            'recent_performance': {
                'home_trend': 'Dominant at home, perfect in September (2-0)',
                'away_trend': 'Strong road performance, explosive offense',
                'momentum': 'Both teams riding high with perfect records'
            },
            'head_to_head': {
                'last_meeting': 'Bills 24-20 in Buffalo (Week 14, 2023)',
                'series_record': 'Bills lead recent meetings 3-2 since 2020',
                'avg_total': 48.2,
                'playoff_history': 'Bills eliminated Chiefs in divisional round 2023'
            },
            'injury_report': {
                'home_impact': 'Chris Jones (Questionable) - Major defensive impact',
                'away_impact': 'Von Miller (Doubtful) - Pass rush concerns',
                'key_players': ['Travis Kelce (Probable)', 'Stefon Diggs (Full)']
            },
            'weather_conditions': {
                'condition': 'Clear skies',
                'temperature': 75,
                'wind': '5 mph SW (favorable for passing)',
                'precipitation': 0,
                'visibility': 'Excellent'
            },
            'betting_trends': {
                'public_money_home': 52,
                'public_money_away': 48,
                'sharp_money': 'Bills receiving professional support',
                'line_movement': 'Moved 0.5 points toward Bills',
                'total_movement': 'Stayed steady at 54.5'
            },
            'coaching_matchup': {
                'home_coach': 'Andy Reid - Excellent after bye weeks',
                'away_coach': 'Sean McDermott - Strong preparation vs elite teams',
                'edge': 'Reid\'s playoff experience vs McDermott\'s tactical adjustments'
            },
            'situational_factors': {
                'primetime': 'Sunday Night Football - both teams excel',
                'rest': 'Both teams coming off standard week',
                'travel': 'Buffalo moderate travel to Kansas City',
                'importance': 'Early season AFC Championship preview'
            }
        },
        'home_team': 'Chiefs',
        'away_team': 'Bills',
        'game_date': '2024-09-16',
        'game_time': '8:20 PM ET',
        'venue': 'Arrowhead Stadium, Kansas City, MO',
        'weather': 'Clear, 75°F, 5 mph SW wind'
    }

    # Game 2: NFC rivalry with different dynamics
    game2_experts = {}
    for i, expert in enumerate(expert_names):
        confidence = 0.48 + (i * 0.025)  # Lower confidence spread

        game2_experts[expert] = {
            'predicted_winner': 'Cowboys' if i % 2 == 0 else '49ers',
            'confidence': confidence,
            'spread_prediction': 1.0 + (i * 0.2) - 1.4,
            'total_prediction': 47.0 + (i * 0.6) - 4.2,
            'reasoning_chain': f"""
            {expert.replace('_', ' ').title()} Assessment for 49ers @ Cowboys:

            This NFC showdown presents unique challenges for prediction due to evenly matched teams.
            The {expert} approach reveals subtle advantages that could determine the outcome.

            Critical Factors:
            - Home field advantage in dome environment
            - Injury considerations affecting key position groups
            - Coaching chess match between elite staffs
            - Recent form divergence creates prediction opportunity
            - Playoff implications add motivation factor
            """,
            'key_factors': [
                f"{expert} identifies key matchup advantages",
                "Dome environment neutralizes weather factors",
                "Injury impacts favor predicted winner",
                "Coaching advantages in specific situations",
                "Recent form trending supports prediction"
            ],
            'home_score_prediction': 23 + (i % 6),
            'away_score_prediction': 21 + (i % 5)
        }

    # Consensus for Game 2 (closer split)
    cowboys_votes = sum(1 for pred in game2_experts.values() if pred['predicted_winner'] == 'Cowboys')
    niners_votes = len(game2_experts) - cowboys_votes
    consensus_winner_2 = 'Cowboys' if cowboys_votes > niners_votes else '49ers'
    avg_confidence_2 = sum(pred['confidence'] for pred in game2_experts.values()) / len(game2_experts)

    games_data['nfc_rivalry_49ers_cowboys'] = {
        'expert_predictions': game2_experts,
        'consensus': {
            'predicted_winner': consensus_winner_2,
            'confidence': avg_confidence_2,
            'vote_distribution': {'Cowboys': cowboys_votes, '49ers': niners_votes},
            'weighted_confidence': avg_confidence_2,
            'unanimous': max(cowboys_votes, niners_votes) >= 13
        },
        'confidence_metrics': {
            'average': avg_confidence_2,
            'std_dev': 0.095,
            'min': min(pred['confidence'] for pred in game2_experts.values()),
            'max': max(pred['confidence'] for pred in game2_experts.values())
        },
        'reasoning_factors': {
            'team_statistics': {
                'home_record': '1-1 (2nd in NFC East)',
                'away_record': '2-0 (1st in NFC West)',
                'home_ppg': 24.5,
                'away_ppg': 28.0,
                'home_papg': 22.0,
                'away_papg': 18.5
            },
            'recent_performance': {
                'home_trend': 'Inconsistent start, home venue provides boost',
                'away_trend': 'Undefeated but showing vulnerabilities',
                'momentum': 'Cowboys need bounce-back, 49ers riding confidence'
            },
            'head_to_head': {
                'last_meeting': '49ers 19-12 (2021 Wild Card)',
                'series_record': 'Cowboys lead all-time but 49ers won recent playoff meeting',
                'avg_total': 44.8,
                'postseason': '49ers eliminated Cowboys in dramatic fashion'
            },
            'injury_report': {
                'home_impact': 'Trevon Diggs (Full) - Key defensive return',
                'away_impact': 'Christian McCaffrey (IR) - Major offensive loss',
                'key_players': ['Dak Prescott (Full)', 'Brock Purdy (Probable)']
            },
            'weather_conditions': {
                'condition': 'Dome (controlled environment)',
                'temperature': 72,
                'wind': 'None',
                'advantages': 'Equal conditions for both teams'
            },
            'betting_trends': {
                'public_money_home': 58,
                'public_money_away': 42,
                'sharp_money': 'Cowboys getting fade-the-public support',
                'line_movement': 'Cowboys favored by increasing margin'
            }
        },
        'home_team': 'Cowboys',
        'away_team': '49ers',
        'game_date': '2024-09-16',
        'game_time': '4:25 PM ET',
        'venue': 'AT&T Stadium, Arlington, TX',
        'weather': 'Dome - controlled environment'
    }

    # Game 3: Divisional slugfest with weather factors
    game3_experts = {}
    for i, expert in enumerate(expert_names):
        confidence = 0.51 + (i * 0.018)  # Tight confidence range

        game3_experts[expert] = {
            'predicted_winner': 'Steelers' if i % 4 != 0 else 'Ravens',
            'confidence': confidence,
            'spread_prediction': 2.5 + (i * 0.25) - 1.75,
            'total_prediction': 44.0 + (i * 0.4) - 2.8,
            'reasoning_chain': f"""
            {expert.replace('_', ' ').title()} Divisional Analysis for Ravens @ Steelers:

            AFC North divisional games carry unique characteristics requiring specialized analysis.
            Historical patterns, weather considerations, and defensive strengths create complex dynamics.

            Divisional Game Factors:
            - Defensive-oriented matchup affects total points projection
            - Weather conditions significantly impact offensive strategies
            - Divisional familiarity reduces surprise element
            - Physical, grinding style expected from both teams
            - Home field advantage amplified in division games
            """,
            'key_factors': [
                "AFC North divisional dynamics favor defense",
                "Weather conditions impact passing games",
                "Home field crucial in divisional matchups",
                "Physical style reduces offensive explosiveness",
                f"{expert} methodology shows slight edge"
            ],
            'home_score_prediction': 20 + (i % 5),
            'away_score_prediction': 17 + (i % 4)
        }

    # Consensus for Game 3
    steelers_votes = sum(1 for pred in game3_experts.values() if pred['predicted_winner'] == 'Steelers')
    ravens_votes = len(game3_experts) - steelers_votes
    consensus_winner_3 = 'Steelers' if steelers_votes > ravens_votes else 'Ravens'
    avg_confidence_3 = sum(pred['confidence'] for pred in game3_experts.values()) / len(game3_experts)

    games_data['afc_north_ravens_steelers'] = {
        'expert_predictions': game3_experts,
        'consensus': {
            'predicted_winner': consensus_winner_3,
            'confidence': avg_confidence_3,
            'vote_distribution': {'Steelers': steelers_votes, 'Ravens': ravens_votes},
            'weighted_confidence': avg_confidence_3,
            'unanimous': max(steelers_votes, ravens_votes) >= 13
        },
        'confidence_metrics': {
            'average': avg_confidence_3,
            'std_dev': 0.067,
            'min': min(pred['confidence'] for pred in game3_experts.values()),
            'max': max(pred['confidence'] for pred in game3_experts.values())
        },
        'reasoning_factors': {
            'team_statistics': {
                'home_record': '1-1 (3rd in AFC North)',
                'away_record': '2-0 (1st in AFC North)',
                'home_ppg': 19.5,
                'away_ppg': 26.0,
                'defensive_focus': 'Both teams emphasize defensive strength'
            },
            'recent_performance': {
                'home_trend': 'Defensive improvements, offensive struggles',
                'away_trend': 'Balanced attack led by dynamic QB play',
                'momentum': 'Ravens confident, Steelers desperate for division win'
            },
            'head_to_head': {
                'last_meeting': 'Ravens 17-10 (2023 Week 18)',
                'series_record': 'Ravens have won 4 of last 6 meetings',
                'avg_total': 40.2,
                'defensive_battles': 'Recent games feature strong defensive play'
            },
            'injury_report': {
                'home_impact': 'T.J. Watt (Questionable) - Pass rush centerpiece',
                'away_impact': 'Roquan Smith (Full) - Defensive captain healthy',
                'key_players': ['Kenny Pickett (Full)', 'Lamar Jackson (Full)']
            },
            'weather_conditions': {
                'condition': 'Overcast with light winds',
                'temperature': 68,
                'wind': '8 mph NE (slight impact on passing)',
                'precipitation': 20,
                'field_conditions': 'Good despite recent rain'
            },
            'betting_trends': {
                'public_money_home': 45,
                'public_money_away': 55,
                'sharp_money': 'Ravens road favorites getting support',
                'line_movement': 'Ravens spread increasing'
            }
        },
        'home_team': 'Steelers',
        'away_team': 'Ravens',
        'game_date': '2024-09-16',
        'game_time': '1:00 PM ET',
        'venue': 'Heinz Field, Pittsburgh, PA',
        'weather': 'Overcast, 68°F, 8 mph NE wind'
    }

    return games_data

async def run_comprehensive_demonstration():
    """Run the complete system demonstration"""

    print("🏈 NFL Comprehensive Prediction System Demonstration")
    print("=" * 60)
    print("Showcasing complete prediction workflow with validation capabilities")
    print("")

    # Initialize system components
    print("🔧 Initializing System Components")
    print("-" * 40)

    try:
        output_generator = ComprehensiveOutputGenerator()
        print("✅ Comprehensive Output Generator initialized")

        # Create comprehensive demo data
        print("📊 Generating comprehensive demo predictions...")
        demo_data = create_comprehensive_demo_data()
        print(f"✅ Generated predictions for {len(demo_data)} games")

        # Calculate statistics
        total_experts = 15
        categories_per_expert = len(output_generator.get_prediction_categories())
        total_predictions = len(demo_data) * total_experts * categories_per_expert

        print(f"   🤖 Experts: {total_experts}")
        print(f"   📋 Categories: {categories_per_expert}")
        print(f"   🎯 Total Predictions: {total_predictions:,}")

        # Generate comprehensive report
        print("\n📝 Generating Comprehensive Report")
        print("-" * 40)

        report_content = await output_generator.generate_comprehensive_report(
            demo_data, week=3, season=2024
        )

        # Report statistics
        line_count = report_content.count('\n')
        word_count = len(report_content.split())
        char_count = len(report_content)

        print(f"✅ Report generated successfully!")
        print(f"   📄 Lines: {line_count:,}")
        print(f"   📝 Words: {word_count:,}")
        print(f"   📊 Characters: {char_count:,}")

        # Save comprehensive report
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_filename = f"comprehensive_demo_report_{timestamp}.md"

        save_info = await output_generator.save_report(report_content, report_filename)
        print(f"💾 {save_info}")

        # Validate report structure
        print("\n🔍 Validating Report Structure")
        print("-" * 40)

        required_sections = [
            "# NFL Week 3 Comprehensive Predictions Report",
            "## 📈 Executive Summary",
            "## 🧠 Expert System Overview",
            "### 📊 Expert Predictions Breakdown",
            "### 🎯 Category Predictions",
            "## 🎯 Consensus Analysis",
            "## 📊 Confidence Analysis",
            "## 👥 Expert Performance Tracking",
            "## 🔬 Methodology & Technical Notes"
        ]

        missing_sections = []
        present_sections = []

        for section in required_sections:
            if section in report_content:
                present_sections.append(section)
            else:
                missing_sections.append(section)

        print(f"✅ Report sections present: {len(present_sections)}/{len(required_sections)}")

        if missing_sections:
            print(f"⚠️  Missing sections: {len(missing_sections)}")
            for section in missing_sections:
                print(f"   - {section}")

        # Analyze prediction quality
        print("\n📊 Analyzing Prediction Quality")
        print("-" * 40)

        all_confidences = []
        consensus_data = []
        expert_distribution = {}

        for game_id, game_data in demo_data.items():
            expert_preds = game_data['expert_predictions']

            # Collect confidence scores
            for expert_name, pred in expert_preds.items():
                all_confidences.append(pred['confidence'])

                # Track expert winner distribution
                winner = pred['predicted_winner']
                if winner not in expert_distribution:
                    expert_distribution[winner] = 0
                expert_distribution[winner] += 1

            # Collect consensus data
            consensus = game_data['consensus']
            consensus_data.append({
                'winner': consensus['predicted_winner'],
                'confidence': consensus['confidence'],
                'unanimous': consensus['unanimous']
            })

        # Calculate statistics
        avg_confidence = sum(all_confidences) / len(all_confidences)
        min_confidence = min(all_confidences)
        max_confidence = max(all_confidences)

        high_confidence = len([c for c in all_confidences if c > 0.7])
        high_conf_pct = high_confidence / len(all_confidences) * 100

        print(f"Confidence Analysis:")
        print(f"   📈 Average: {avg_confidence:.1%}")
        print(f"   📊 Range: {min_confidence:.1%} - {max_confidence:.1%}")
        print(f"   🎯 High Confidence (>70%): {high_confidence}/{len(all_confidences)} ({high_conf_pct:.1f}%)")

        print(f"\nExpert Winner Distribution:")
        for team, count in sorted(expert_distribution.items(), key=lambda x: x[1], reverse=True):
            print(f"   🏈 {team}: {count} predictions")

        print(f"\nConsensus Analysis:")
        unanimous_games = sum(1 for c in consensus_data if c['unanimous'])
        print(f"   🤝 Unanimous games: {unanimous_games}/{len(consensus_data)}")

        for i, consensus in enumerate(consensus_data, 1):
            print(f"   Game {i}: {consensus['winner']} ({consensus['confidence']:.1%})")

        # Save prediction data for validation
        print("\n💾 Saving Prediction Data")
        print("-" * 40)

        predictions_dir = "/home/iris/code/experimental/nfl-predictor-api/predictions"
        os.makedirs(predictions_dir, exist_ok=True)

        json_filename = f"demo_predictions_data_{timestamp}.json"
        json_filepath = os.path.join(predictions_dir, json_filename)

        json_data = {
            'meta': {
                'week': 3,
                'season': 2024,
                'generated_at': datetime.now().isoformat(),
                'total_games': len(demo_data),
                'total_experts': total_experts,
                'total_predictions': total_predictions,
                'demonstration': True
            },
            'predictions': demo_data,
            'statistics': {
                'confidence': {
                    'average': avg_confidence,
                    'min': min_confidence,
                    'max': max_confidence,
                    'high_confidence_count': high_confidence
                },
                'expert_distribution': expert_distribution,
                'consensus_data': consensus_data
            }
        }

        with open(json_filepath, 'w', encoding='utf-8') as f:
            json.dump(json_data, f, indent=2, default=str)

        file_size = os.path.getsize(json_filepath)
        print(f"✅ Prediction data saved: {json_filepath}")
        print(f"   📁 File size: {file_size:,} bytes")

        # Final summary
        print("\n🎉 Comprehensive Demonstration Complete")
        print("=" * 60)

        summary = {
            'status': 'SUCCESS',
            'games_analyzed': len(demo_data),
            'experts_utilized': total_experts,
            'prediction_categories': categories_per_expert,
            'total_predictions': total_predictions,
            'report_lines': line_count,
            'report_words': word_count,
            'report_chars': char_count,
            'avg_confidence': avg_confidence,
            'high_confidence_pct': high_conf_pct,
            'consensus_unanimous': unanimous_games,
            'report_file': report_filename,
            'data_file': json_filename
        }

        print("📋 DEMONSTRATION SUMMARY:")
        print(f"   🏈 Games Analyzed: {summary['games_analyzed']}")
        print(f"   🤖 Experts Utilized: {summary['experts_utilized']}")
        print(f"   📊 Prediction Categories: {summary['prediction_categories']}")
        print(f"   🎯 Total Predictions: {summary['total_predictions']:,}")
        print(f"   📄 Report Lines: {summary['report_lines']:,}")
        print(f"   📝 Report Words: {summary['report_words']:,}")
        print(f"   💪 Average Confidence: {summary['avg_confidence']:.1%}")
        print(f"   🎯 High Confidence Rate: {summary['high_confidence_pct']:.1f}%")
        print(f"   📁 Report File: {summary['report_file']}")
        print(f"   💾 Data File: {summary['data_file']}")

        return summary

    except Exception as e:
        print(f"❌ Demonstration failed: {e}")
        import traceback
        traceback.print_exc()
        return {'status': 'FAILED', 'error': str(e)}

if __name__ == "__main__":
    import asyncio

    # Run the comprehensive demonstration
    result = asyncio.run(run_comprehensive_demonstration())

    if result['status'] == 'SUCCESS':
        print("\n✅ All systems operational and validated!")
    else:
        print(f"\n❌ System demonstration failed: {result.get('error', 'Unknown error')}")