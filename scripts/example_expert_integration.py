#!/usr/bin/env python3
"""
Example: Integrating ExpertDataAccessLayer with Expert Prediction Models

Shows how to:
1. Fetch filtered data for each expert personality
2. Pass data to expert prediction models
3. Generate consensus predictions
4. Handle errors gracefully
"""

import asyncio
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.services.expert_data_access_layer import ExpertDataAccessLayer, GameData
from typing import Dict, List


class ExpertPredictionModel:
    """Base class for expert prediction models"""

    def __init__(self, expert_id: str):
        self.expert_id = expert_id

    async def predict(self, game_data: GameData) -> Dict:
        """
        Generate prediction based on game data.

        Each expert uses different aspects of the data based on their personality.
        """
        # This is where your ML model or rule-based logic would go
        # For now, return a simple mock prediction

        prediction = {
            'expert_id': self.expert_id,
            'game_id': game_data.game_id,
            'winner': None,
            'spread_pick': None,
            'total_pick': None,
            'confidence': 0.0,
            'reasoning': ''
        }

        # The Analyst: Uses comprehensive stats
        if self.expert_id == 'the-analyst':
            home_ppg = game_data.team_stats.get('home_stats', {}).get('points_avg', 0)
            away_ppg = game_data.team_stats.get('away_stats', {}).get('points_avg', 0)

            if home_ppg > away_ppg:
                prediction['winner'] = game_data.home_team
                prediction['confidence'] = min((home_ppg - away_ppg) / 10, 0.9)
            else:
                prediction['winner'] = game_data.away_team
                prediction['confidence'] = min((away_ppg - home_ppg) / 10, 0.9)

            prediction['reasoning'] = f"Statistical analysis: {prediction['winner']} averaging {max(home_ppg, away_ppg):.1f} PPG"

        # The Gambler: Follows the odds
        elif self.expert_id == 'the-gambler':
            spread = game_data.odds.get('spread', {})
            if spread.get('home'):
                if spread['home'] < 0:  # Home is favorite
                    prediction['winner'] = game_data.home_team
                    prediction['spread_pick'] = game_data.home_team
                else:
                    prediction['winner'] = game_data.away_team
                    prediction['spread_pick'] = game_data.away_team

                prediction['confidence'] = 0.55  # Always moderate confidence
                prediction['reasoning'] = f"Following Vegas line: {spread['home']}"

        # Gut Instinct: Random with home bias
        elif self.expert_id == 'gut-instinct':
            # Just picks home team with slight bias
            prediction['winner'] = game_data.home_team
            prediction['confidence'] = 0.52
            prediction['reasoning'] = "Home field advantage feels right"

        # Contrarian Rebel: Fades the public
        elif self.expert_id == 'contrarian-rebel':
            # Would use public betting data to fade
            # For now, just picks underdog
            spread = game_data.odds.get('spread', {})
            if spread.get('home'):
                if spread['home'] > 0:  # Home is underdog
                    prediction['winner'] = game_data.home_team
                else:
                    prediction['winner'] = game_data.away_team

                prediction['confidence'] = 0.60
                prediction['reasoning'] = "Fading the public, taking the underdog"

        return prediction


async def generate_week_predictions(week: int, season: int = 2024):
    """
    Generate predictions for all experts for a given week.

    This demonstrates the full workflow:
    1. Initialize data access layer
    2. Define games and experts
    3. Batch fetch filtered data
    4. Generate predictions from each expert
    5. Create consensus
    """

    print("="*70)
    print(f"GENERATING PREDICTIONS FOR WEEK {week}, {season} SEASON")
    print("="*70)

    # Initialize data access layer
    dal = ExpertDataAccessLayer()

    # Define games (in production, fetch from database)
    games = [
        '2024_05_KC_BUF',
        '2024_05_DAL_SF',
        '2024_05_PHI_NYG',
    ]

    # Define experts
    experts = [
        'the-analyst',
        'the-gambler',
        'gut-instinct',
        'contrarian-rebel'
    ]

    # Initialize expert models
    expert_models = {
        expert_id: ExpertPredictionModel(expert_id)
        for expert_id in experts
    }

    print(f"\n📊 Fetching data for {len(experts)} experts, {len(games)} games...")

    # Batch fetch all data in parallel
    try:
        expert_data = await dal.batch_get_expert_data(experts, games)
        print(f"✅ Data fetched successfully!")

        # Show what data each expert received
        print("\n📋 Data Access Summary:")
        for expert_id in experts:
            games_with_data = len(expert_data.get(expert_id, {}))
            print(f"   {expert_id:20} - {games_with_data} games")

    except Exception as e:
        print(f"❌ Error fetching data: {e}")
        return

    # Generate predictions for each expert
    print(f"\n🎯 Generating predictions...")

    all_predictions = {}

    for expert_id in experts:
        expert_predictions = []

        for game_id, game_data in expert_data[expert_id].items():
            try:
                prediction = await expert_models[expert_id].predict(game_data)
                expert_predictions.append(prediction)
            except Exception as e:
                print(f"   ⚠️  {expert_id} failed on {game_id}: {e}")

        all_predictions[expert_id] = expert_predictions

    # Display predictions
    print(f"\n{'='*70}")
    print("EXPERT PREDICTIONS")
    print('='*70)

    for game_id in games:
        # Parse game info
        try:
            parts = game_id.split('_')
            away_team = parts[2]
            home_team = parts[3]

            print(f"\n🏈 {away_team} @ {home_team}")
            print("-" * 50)

            for expert_id in experts:
                expert_preds = all_predictions.get(expert_id, [])
                game_pred = next((p for p in expert_preds if p['game_id'] == game_id), None)

                if game_pred:
                    winner = game_pred.get('winner', 'N/A')
                    confidence = game_pred.get('confidence', 0) * 100
                    reasoning = game_pred.get('reasoning', '')

                    print(f"   {expert_id:20} → {winner:4} ({confidence:.0f}%) - {reasoning}")
                else:
                    print(f"   {expert_id:20} → No prediction")

        except Exception as e:
            print(f"   Error displaying {game_id}: {e}")

    # Generate consensus
    print(f"\n{'='*70}")
    print("CONSENSUS PREDICTIONS")
    print('='*70)

    for game_id in games:
        parts = game_id.split('_')
        away_team = parts[2]
        home_team = parts[3]

        # Count votes for each team
        home_votes = 0
        away_votes = 0
        total_confidence = 0

        for expert_id in experts:
            expert_preds = all_predictions.get(expert_id, [])
            game_pred = next((p for p in expert_preds if p['game_id'] == game_id), None)

            if game_pred and game_pred.get('winner'):
                if game_pred['winner'] == home_team:
                    home_votes += 1
                elif game_pred['winner'] == away_team:
                    away_votes += 1

                total_confidence += game_pred.get('confidence', 0)

        # Determine consensus
        if home_votes > away_votes:
            consensus = home_team
            vote_count = home_votes
        elif away_votes > home_votes:
            consensus = away_team
            vote_count = away_votes
        else:
            consensus = "TIE"
            vote_count = home_votes

        avg_confidence = (total_confidence / len(experts)) * 100 if experts else 0

        print(f"\n🏈 {away_team} @ {home_team}")
        print(f"   Consensus: {consensus} ({vote_count}/{len(experts)} experts)")
        print(f"   Avg Confidence: {avg_confidence:.1f}%")

    # Show API usage
    print(f"\n{'='*70}")
    print("API USAGE")
    print('='*70)

    limits = dal.get_rate_limit_status()
    print(f"   SportsData.io: {limits['sportsdata']} requests")
    print(f"   The Odds API: {limits['odds_api']} requests")

    print(f"\n{'='*70}")
    print("PREDICTIONS COMPLETE")
    print('='*70)


async def test_single_prediction():
    """Test prediction flow for a single game"""

    print("\n" + "="*70)
    print("TESTING SINGLE GAME PREDICTION")
    print("="*70)

    dal = ExpertDataAccessLayer()

    # Test with The Analyst
    print("\n🤖 Testing: The Analyst")
    game_data = await dal.get_expert_data_view(
        expert_id='the-analyst',
        game_id='2024_05_KC_BUF'
    )

    model = ExpertPredictionModel('the-analyst')
    prediction = await model.predict(game_data)

    print(f"   Game: {game_data.away_team} @ {game_data.home_team}")
    print(f"   Prediction: {prediction['winner']}")
    print(f"   Confidence: {prediction['confidence']*100:.1f}%")
    print(f"   Reasoning: {prediction['reasoning']}")

    # Test with different expert
    print("\n🎲 Testing: The Gambler")
    game_data = await dal.get_expert_data_view(
        expert_id='the-gambler',
        game_id='2024_05_KC_BUF'
    )

    model = ExpertPredictionModel('the-gambler')
    prediction = await model.predict(game_data)

    print(f"   Game: {game_data.away_team} @ {game_data.home_team}")
    print(f"   Prediction: {prediction['winner']}")
    print(f"   Confidence: {prediction['confidence']*100:.1f}%")
    print(f"   Reasoning: {prediction['reasoning']}")


async def main():
    """Main entry point"""

    # Test 1: Single prediction
    await test_single_prediction()

    # Test 2: Full week predictions
    await generate_week_predictions(week=5, season=2024)


if __name__ == "__main__":
    asyncio.run(main())