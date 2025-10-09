#!/usr/bin/env python3
"""
Neo4j Usage Example for Kiro and Training Scripts
Demonstrates how to connect to and use Neo4j for Expert Learning System
"""
import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from services.neo4j_service import Neo4jService, get_neo4j_service
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


def main():
    """Example usage of Neo4j service"""

    print("=" * 60)
    print("Neo4j Expert Learning System - Usage Example")
    print("=" * 60)

    # Initialize service
    neo4j = get_neo4j_service()

    # 1. Health Check
    print("\n1. Health Check")
    print("-" * 40)
    if neo4j.health_check():
        print("✓ Neo4j connection healthy")
    else:
        print("✗ Neo4j connection failed")
        return

    # 2. List Experts
    print("\n2. List All Experts")
    print("-" * 40)
    experts = neo4j.list_experts()
    print(f"Found {len(experts)} experts:")
    for expert in experts[:5]:
        print(f"  - {expert['name']} ({expert['id']})")
        print(f"    Personality: {expert['personality']}")
        print(f"    Style: {expert['decision_style']}")

    # 3. Get Specific Expert
    print("\n3. Get Specific Expert")
    print("-" * 40)
    expert = neo4j.get_expert("conservative_analyzer")
    if expert:
        print(f"Expert: {expert['name']}")
        print(f"ID: {expert['id']}")
        print(f"Personality: {expert['personality']}")

    # 4. List Teams
    print("\n4. List NFL Teams")
    print("-" * 40)
    teams = neo4j.list_teams()
    print(f"Found {len(teams)} teams:")
    for team in teams[:5]:
        print(f"  - {team['name']} ({team['id']}) - {team['division']}")

    # 5. Filter Teams by Division
    print("\n5. Filter Teams by Division")
    print("-" * 40)
    afc_north = neo4j.list_teams(division="AFC North")
    print(f"AFC North teams: {len(afc_north)}")
    for team in afc_north:
        print(f"  - {team['name']}")

    # 6. Create Game Example
    print("\n6. Create Game Node")
    print("-" * 40)
    game_result = neo4j.create_game(
        game_id="KC_BUF_2024_W10",
        home_team="KC",
        away_team="BUF",
        season=2024,
        week=10,
        game_date="2024-10-13"
    )
    print(f"Game created: {game_result}")

    # 7. Record Prediction
    print("\n7. Record Expert Prediction")
    print("-" * 40)
    prediction_result = neo4j.record_prediction(
        expert_id="conservative_analyzer",
        game_id="KC_BUF_2024_W10",
        winner="KC",
        confidence=0.72,
        win_probability=0.65,
        reasoning="Chiefs home field advantage and defensive strength"
    )
    print(f"Prediction recorded: {prediction_result}")

    # 8. Get Expert Predictions
    print("\n8. Get Expert's Recent Predictions")
    print("-" * 40)
    predictions = neo4j.get_expert_predictions("conservative_analyzer", limit=5)
    print(f"Found {len(predictions)} predictions:")
    for pred in predictions:
        print(f"  - {pred['home_team']} vs {pred['away_team']}")
        print(f"    Predicted: {pred['predicted_winner']} (Conf: {pred['confidence']:.2%})")

    # 9. Custom Query Example
    print("\n9. Custom Cypher Query")
    print("-" * 40)
    custom_query = """
    MATCH (e:Expert)
    WHERE e.personality CONTAINS 'contrarian'
    RETURN e.name as name, e.id as id
    """
    contrarians = neo4j.execute_query(custom_query)
    print(f"Found {len(contrarians)} contrarian experts:")
    for expert in contrarians:
        print(f"  - {expert['name']}")

    # 10. Graph Statistics
    print("\n10. Database Statistics")
    print("-" * 40)
    stats_query = """
    MATCH (e:Expert)
    OPTIONAL MATCH (e)-[p:PREDICTED]->(g:Game)
    RETURN e.name as expert,
           count(p) as predictions_count
    ORDER BY predictions_count DESC
    LIMIT 5
    """
    stats = neo4j.execute_query(stats_query)
    print("Expert prediction counts:")
    for stat in stats:
        print(f"  - {stat['expert']}: {stat['predictions_count']} predictions")

    print("\n" + "=" * 60)
    print("Example completed successfully!")
    print("=" * 60)

    # Close connection
    neo4j.close()


if __name__ == "__main__":
    main()
