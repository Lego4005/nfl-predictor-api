#!/usr/bin/env python3
"""
Fetch STORED predictions from database and compare with actual results
"""

import os
import sys
import json
import asyncio
from datetime import datetime, timedelta

# Add project paths
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)
sys.path.append(os.path.join(project_root, 'src'))

from src.services.enhanced_data_storage import EnhancedDataStorage
from src.services.enhanced_data_fetcher import EnhancedDataFetcher

async def fetch_stored_predictions_and_results():
    """Fetch stored predictions and actual game results from database"""

    # Database connection
    db_url = os.getenv('DATABASE_URL', 'postgresql://localhost/nfl_predictor')
    storage = EnhancedDataStorage(db_url)
    fetcher = EnhancedDataFetcher()

    try:
        await storage.initialize()

        # Get recent games with stored predictions
        query = """
            SELECT DISTINCT
                g.game_id,
                g.home_team,
                g.away_team,
                g.home_score,
                g.away_score,
                g.game_date,
                g.week,
                g.season
            FROM games g
            WHERE g.status = 'final'
                AND g.game_date >= NOW() - INTERVAL '7 days'
                AND EXISTS (
                    SELECT 1 FROM predictions p
                    WHERE p.game_id = g.game_id
                )
            ORDER BY g.game_date DESC
            LIMIT 1;
        """

        async with storage.pool.acquire() as conn:
            game_row = await conn.fetchrow(query)

            if not game_row:
                print("No recent games with predictions found in database")
                return None

            game_id = game_row['game_id']
            print(f"Found game: {game_row['away_team']} @ {game_row['home_team']}")
            print(f"Final Score: {game_row['away_team']} {game_row['away_score']}, {game_row['home_team']} {game_row['home_score']}")
            print(f"Game Date: {game_row['game_date']}")
            print("=" * 80)

            # Fetch all expert predictions for this game
            pred_query = """
                SELECT
                    p.expert_id,
                    p.prediction,
                    p.confidence,
                    p.created_at,
                    p.reasoning,
                    e.name as expert_name,
                    e.personality
                FROM predictions p
                LEFT JOIN experts e ON e.expert_id = p.expert_id
                WHERE p.game_id = $1
                ORDER BY p.expert_id;
            """

            predictions = await conn.fetch(pred_query, game_id)

            if not predictions:
                print(f"No predictions found for game {game_id}")

                # Check expert_prediction_verification table
                verify_query = """
                    SELECT * FROM expert_prediction_verification
                    WHERE game_id = $1;
                """
                verifications = await conn.fetch(verify_query, game_id)

                if verifications:
                    print(f"\nFound {len(verifications)} verification records:")
                    for v in verifications:
                        print(f"  Expert: {v['expert_id']}")
                        print(f"  Predictions: {json.dumps(v['predictions'], indent=2)}")
                        print(f"  Accuracy: {json.dumps(v['accuracy_scores'], indent=2)}")
                        print()

                return None

            print(f"\nFound {len(predictions)} expert predictions:")
            print("=" * 80)

            # Display each expert's prediction
            for pred in predictions:
                expert_name = pred['expert_name'] or pred['expert_id']
                prediction_data = pred['prediction']

                print(f"\n{expert_name}:")
                print(f"  Expert ID: {pred['expert_id']}")
                print(f"  Confidence: {pred['confidence']:.1%}")
                print(f"  Created: {pred['created_at']}")

                if isinstance(prediction_data, dict):
                    print(f"  Winner: {prediction_data.get('winner', 'N/A')}")
                    print(f"  Score: {prediction_data.get('away_score', '?')}-{prediction_data.get('home_score', '?')}")
                    print(f"  Spread Pick: {prediction_data.get('spread_pick', 'N/A')}")
                    print(f"  Total Pick: {prediction_data.get('total_pick', 'N/A')}")

                    # Compare to actual
                    if prediction_data.get('winner'):
                        actual_winner = game_row['away_team'] if game_row['away_score'] > game_row['home_score'] else game_row['home_team']
                        correct = prediction_data.get('winner') == actual_winner
                        print(f"  Result: {'✅ CORRECT' if correct else '❌ WRONG'}")

                    if prediction_data.get('reasoning'):
                        print(f"  Reasoning: {prediction_data.get('reasoning')[:100]}...")
                else:
                    print(f"  Raw Prediction: {prediction_data}")

            # Summary
            print("\n" + "=" * 80)
            print("SUMMARY:")
            print(f"Game Result: {game_row['away_team']} {game_row['away_score']}, {game_row['home_team']} {game_row['home_score']}")
            print(f"Total Predictions Stored: {len(predictions)}")

            # Check enhanced game data
            enhanced_query = """
                SELECT * FROM enhanced_game_data
                WHERE game_id = $1;
            """
            enhanced = await conn.fetchrow(enhanced_query, game_id)

            if enhanced:
                print(f"\n✅ Enhanced game data available:")
                print(f"  Total Yards: Home {enhanced['home_total_yards']} vs Away {enhanced['away_total_yards']}")
                print(f"  Turnovers: Home {enhanced['home_turnovers']} vs Away {enhanced['away_turnovers']}")
                print(f"  Time of Possession: Home {enhanced['home_time_of_possession']} vs Away {enhanced['away_time_of_possession']}")
            else:
                print("\n❌ No enhanced game data stored yet")

    except Exception as e:
        print(f"Error fetching data: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await storage.close()

if __name__ == "__main__":
    print("=" * 80)
    print("FETCHING STORED PREDICTIONS FROM DATABASE")
    print("=" * 80)
    asyncio.run(fetch_stored_predictions_and_results())