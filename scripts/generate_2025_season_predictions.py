#!/usr/bin/env python3
"""
Generate 2025 Season Predictions (Weeks 1-4)

Generates predictions from all 15 experts for every game played so far in 2025.
Users can make predictions without looking at scores since games already happened.
"""

import asyncio
import sys
import os
import json
from typing import List, Dict

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.services.expert_data_access_layer import ExpertDataAccessLayer
from src.ml.expert_models import EXPERT_MODELS, get_expert_model


async def get_2025_games(weeks: List[int] = [1, 2, 3, 4]) -> List[str]:
    """Get all game IDs for specified weeks in 2025 season"""

    # For now, use sample game IDs
    # TODO: Query Supabase for actual 2025 games

    sample_games = [
        # Week 1 sample
        '2025_01_KC_BAL',
        '2025_01_PHI_GB',
        '2025_01_SF_NYJ',

        # Week 2 sample
        '2025_02_BUF_MIA',
        '2025_02_DAL_NO',
        '2025_02_DEN_PIT',

        # Week 3 sample
        '2025_03_KC_ATL',
        '2025_03_DET_ARI',
        '2025_03_TB_DEN',

        # Week 4 sample (today's MNF games)
        '2025_04_NYJ_MIA',
        '2025_04_CIN_DEN',
    ]

    return sample_games


async def generate_season_predictions():
    """Generate predictions for all 2025 games (Weeks 1-4)"""

    print("=" * 80)
    print("🏈 2025 NFL SEASON PREDICTIONS - WEEKS 1-4")
    print("=" * 80)
    print("\n📊 Generating predictions for all games played so far in 2025...")
    print("   (Users can make predictions without looking at scores!)\n")

    # Initialize
    dal = ExpertDataAccessLayer()
    expert_ids = list(EXPERT_MODELS.keys())

    print(f"✅ Loaded {len(expert_ids)} experts")

    # Get all 2025 games
    game_ids = await get_2025_games([1, 2, 3, 4])
    print(f"✅ Found {len(game_ids)} games from Weeks 1-4\n")

    print("=" * 80)
    print("FETCHING DATA FOR ALL GAMES...")
    print("=" * 80)

    # Batch fetch all expert data
    expert_data = await dal.batch_get_expert_data(expert_ids, game_ids)

    print(f"✅ Retrieved data for {len(expert_ids)} experts x {len(game_ids)} games")
    print(f"   Total datasets: {len(expert_ids) * len(game_ids)}\n")

    # Generate predictions for each game
    all_predictions = {}

    for game_id in game_ids:
        game_predictions = {}

        # Get predictions from all experts
        for expert_id in expert_ids:
            try:
                model = get_expert_model(expert_id)
                game_data = expert_data[expert_id].get(game_id)

                if game_data:
                    prediction = await model.predict(game_data)
                    game_predictions[expert_id] = {
                        'winner': prediction.winner,
                        'confidence': prediction.winner_confidence,
                        'spread_pick': prediction.spread_pick,
                        'spread_confidence': prediction.spread_confidence,
                        'total_pick': prediction.total_pick,
                        'total_confidence': prediction.total_confidence,
                        'reasoning': prediction.reasoning
                    }

            except Exception as e:
                print(f"⚠️  {expert_id}/{game_id}: {e}")

        all_predictions[game_id] = game_predictions

    # Display results by game
    print("=" * 80)
    print("PREDICTIONS BY GAME")
    print("=" * 80)

    for game_id, predictions in all_predictions.items():
        # Parse game ID
        parts = game_id.split('_')
        week = parts[1]
        away_team = parts[2]
        home_team = parts[3]

        print(f"\n{'=' * 80}")
        print(f"🏈 Week {week}: {away_team} @ {home_team}")
        print('=' * 80)

        # Count votes
        home_votes = sum(1 for p in predictions.values() if p.get('winner') == home_team)
        away_votes = sum(1 for p in predictions.values() if p.get('winner') == away_team)
        no_pick = len(predictions) - home_votes - away_votes

        print(f"\n📊 Consensus:")
        print(f"   {home_team}: {home_votes}/{len(predictions)} experts ({home_votes/len(predictions)*100:.1f}%)")
        print(f"   {away_team}: {away_votes}/{len(predictions)} experts ({away_votes/len(predictions)*100:.1f}%)")
        print(f"   No Pick: {no_pick}/{len(predictions)}")

        consensus_winner = home_team if home_votes > away_votes else away_team
        consensus_strength = max(home_votes, away_votes) / len(predictions)

        print(f"\n✅ Consensus Prediction: {consensus_winner}")
        print(f"   Strength: {consensus_strength*100:.1f}%")

        # Show high-confidence picks
        high_conf_picks = [
            (expert_id, p) for expert_id, p in predictions.items()
            if p.get('confidence', 0) > 0.65
        ]

        if high_conf_picks:
            print(f"\n💪 High Confidence Picks (>65%):")
            for expert_id, p in high_conf_picks[:5]:
                expert_name = expert_id.replace('_', ' ').title()
                print(f"   • {expert_name}: {p['winner']} ({p['confidence']*100:.0f}%)")

    # Overall statistics
    print("\n" + "=" * 80)
    print("SEASON STATISTICS")
    print("=" * 80)

    total_predictions = sum(len(p) for p in all_predictions.values())
    print(f"\n📊 Total Predictions Generated: {total_predictions}")
    print(f"   Games: {len(game_ids)}")
    print(f"   Experts: {len(expert_ids)}")
    print(f"   Coverage: {total_predictions / (len(game_ids) * len(expert_ids)) * 100:.1f}%")

    # Expert participation
    expert_participation = {}
    for expert_id in expert_ids:
        predictions_count = sum(
            1 for game_preds in all_predictions.values()
            if expert_id in game_preds and game_preds[expert_id].get('winner')
        )
        expert_participation[expert_id] = predictions_count

    print(f"\n📈 Expert Participation:")
    for expert_id, count in sorted(expert_participation.items(), key=lambda x: x[1], reverse=True)[:10]:
        expert_name = expert_id.replace('_', ' ').title()
        print(f"   {expert_name:<40} {count}/{len(game_ids)} games ({count/len(game_ids)*100:.0f}%)")

    # Save to JSON
    output_file = 'docs/2025_season_predictions.json'
    os.makedirs('docs', exist_ok=True)

    with open(output_file, 'w') as f:
        json.dump(all_predictions, f, indent=2)

    print(f"\n💾 Predictions saved to: {output_file}")

    print("\n" + "=" * 80)
    print("✅ 2025 SEASON PREDICTIONS COMPLETE")
    print("=" * 80)
    print("\nNext steps:")
    print("  1. Store predictions in Supabase database")
    print("  2. Compare predictions to actual game outcomes")
    print("  3. Calculate expert accuracy scores")
    print("  4. Generate Week 5 predictions for upcoming games")


if __name__ == "__main__":
    asyncio.run(generate_season_predictions())