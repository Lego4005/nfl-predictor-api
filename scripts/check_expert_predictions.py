#!/usr/bin/env python3
import os
from supabase import create_client, Client
from collections import defaultdict

# Supabase connection
SUPABASE_URL = "https://hfbzswsrgomevcuickhg.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImhmYnpzd3NyZ29tZXZjdWlja2hnIiwicm9sZSI6ImFub24iLCJpYXQiOjE3MzI1ODQwNTIsImV4cCI6MjA0ODE2MDA1Mn0.Gy8qOmGQzWfSVCCaGXINqDvziBQBGGlN-nNUF-SrfQU"

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Get all predictions grouped by expert
response = supabase.table('predictions').select('*').execute()

if response.data:
    expert_counts = defaultdict(int)
    expert_games = defaultdict(set)

    for prediction in response.data:
        expert_name = prediction.get('expert_name', 'Unknown')
        game_id = prediction.get('game_id')
        expert_counts[expert_name] += 1
        if game_id:
            expert_games[expert_name].add(game_id)

    print("Expert Prediction Counts:")
    print("-" * 50)
    for expert, count in sorted(expert_counts.items()):
        unique_games = len(expert_games[expert])
        print(f"{expert:30} | {count:3} predictions | {unique_games:3} unique games")

    print(f"\nTotal experts: {len(expert_counts)}")
    print(f"Total predictions: {sum(expert_counts.values())}")
    print(f"Average predictions per expert: {sum(expert_counts.values()) / len(expert_counts):.1f}")

    # Show sample of games
    print("\n" + "="*50)
    print("Sample of unique game IDs:")
    all_games = set()
    for games in expert_games.values():
        all_games.update(games)

    for game_id in list(all_games)[:5]:
        print(f"  - {game_id}")
    print(f"\nTotal unique games: {len(all_games)}")
else:
    print("No predictions found in database")