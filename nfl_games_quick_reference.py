#!/usr/bin/env python3
"""
🏈 NFL Games Quick Reference Guide
Common operations for both games tables
"""

def show_nfl_games_reference():
    """Show common NFL games operations"""
    
    print("🏈 NFL GAMES TABLE REFERENCE")
    print("=" * 50)
    
    print("\n📊 TABLE COMPARISON:")
    print("-" * 30)
    print("✅ games table (PRIMARY):")
    print("   • Season: 2025 (current)")
    print("   • Status: Active, complete schema")
    print("   • Use for: Current operations, predictions, UI")
    print("   • Schema: Rich with venue, weather, broadcasting data")
    
    print("\n⚠️ nfl_games table (HISTORICAL):")
    print("   • Season: 2020-2024 (historical)")
    print("   • Status: Incomplete data")
    print("   • Use for: Historical analysis only")
    print("   • Schema: Basic with betting and personnel data")
    
    print("\n🔍 COMMON QUERIES:")
    print("-" * 30)
    
    # Games table queries
    print("\n📋 GAMES TABLE (Primary):")
    queries = [
        {
            "description": "Get current week games",
            "sql": """
SELECT home_team, away_team, game_time, stadium, network
FROM games 
WHERE season = 2025 AND week = 2
ORDER BY game_time;"""
        },
        {
            "description": "Get team's upcoming games",
            "sql": """
SELECT * FROM games 
WHERE season = 2025 
AND (home_team = 'KC' OR away_team = 'KC')
AND status = 'scheduled'
ORDER BY game_time;"""
        },
        {
            "description": "Get games by network",
            "sql": """
SELECT home_team, away_team, game_time, network
FROM games 
WHERE season = 2025 AND network = 'CBS'
ORDER BY game_time;"""
        }
    ]
    
    for query in queries:
        print(f"\n💡 {query['description']}:")
        print(f"```sql{query['sql']}```")
    
    # NFL Games table queries  
    print("\n📋 NFL_GAMES TABLE (Historical):")
    historical_queries = [
        {
            "description": "Get historical team performance",
            "sql": """
SELECT season, COUNT(*) as games_played,
       AVG(CASE WHEN home_team = 'KC' THEN home_score 
                WHEN away_team = 'KC' THEN away_score END) as avg_points
FROM nfl_games 
WHERE home_team = 'KC' OR away_team = 'KC'
GROUP BY season ORDER BY season;"""
        },
        {
            "description": "Get betting line analysis",
            "sql": """
SELECT home_team, away_team, spread_line, 
       (home_score - away_score) as actual_margin
FROM nfl_games 
WHERE spread_line IS NOT NULL
ORDER BY game_date DESC LIMIT 10;"""
        }
    ]
    
    for query in historical_queries:
        print(f"\n💡 {query['description']}:")
        print(f"```sql{query['sql']}```")
    
    print("\n⚡ PYTHON/SUPABASE EXAMPLES:")
    print("-" * 30)
    
    python_examples = [
        {
            "description": "Get this week's games (Python)",
            "code": """
# Current games (games table)
result = supabase.table('games') \\
    .select('home_team, away_team, game_time, network') \\
    .eq('season', 2025) \\
    .eq('week', 2) \\
    .order('game_time') \\
    .execute()
    
games = result.data"""
        },
        {
            "description": "Get historical data (Python)",
            "code": """
# Historical analysis (nfl_games table)
result = supabase.table('nfl_games') \\
    .select('*') \\
    .eq('season', 2024) \\
    .not_.is_('home_score', 'null') \\
    .order('game_date', desc=True) \\
    .limit(50) \\
    .execute()

historical_games = result.data"""
        }
    ]
    
    for example in python_examples:
        print(f"\n🐍 {example['description']}:")
        print(f"```python{example['code']}```")
    
    print("\n🎯 BEST PRACTICES:")
    print("-" * 30)
    practices = [
        "✅ Use 'games' table for all current season (2025) operations",
        "✅ Use proper timezone handling (Eastern Time for NFL)",
        "✅ Filter by season=2025 for current data",
        "✅ Use 'nfl_games' only for historical analysis",
        "⚠️ Always check data completeness before using nfl_games",
        "⚠️ Be aware that nfl_games has incomplete 2020-2024 data"
    ]
    
    for practice in practices:
        print(f"   {practice}")
    
    print(f"\n📚 SCHEMA DIFFERENCES:")
    print("-" * 30)
    print("games table (Rich Schema):")
    print("   • venue_city, venue_state, timezone")
    print("   • network, is_primetime, is_playoff") 
    print("   • weather fields (temperature, wind, humidity)")
    print("   • espn_game_id integration")
    
    print("\nnfl_games table (Basic + Betting):")
    print("   • spread_line, moneyline, total_line")
    print("   • qb_name, coach data")
    print("   • rest days (away_rest, home_rest)")
    print("   • weather_temperature, weather_wind_mph")

if __name__ == "__main__":
    show_nfl_games_reference()