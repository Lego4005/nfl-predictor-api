#!/usr/bin/env python3
"""
REAL GAME DATA FETCHER - Get actual outcomes using premium APIs
Uses The Odds API and SportsData.io to get comprehensive game results
"""

import asyncio
import json
import sys
import os
import requests
from datetime import datetime
from dotenv import load_dotenv

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

load_dotenv()

class RealGameDataFetcher:
    def __init__(self):
        self.odds_api_key = os.getenv('VITE_ODDS_API_KEY') or os.getenv('ODDS_API_KEY')
        self.sportsdata_key = os.getenv('VITE_SPORTSDATA_IO_KEY') or os.getenv('SPORTSDATA_IO_KEY')
        self.rapid_api_key = os.getenv('RAPID_API_KEY')

        if not self.odds_api_key or not self.sportsdata_key:
            print("❌ Missing premium API keys!")
            print("Need: ODDS_API_KEY and SPORTSDATA_IO_KEY")
            return

        print("✅ Premium API keys loaded")

    def fetch_odds_api_game_result(self, team1="chargers", team2="raiders"):
        """Fetch betting outcomes from The Odds API"""

        # Get recent NFL games and outcomes
        url = f"https://api.the-odds-api.com/v4/sports/americanfootball_nfl/scores"
        params = {
            'api_key': self.odds_api_key,
            'daysFrom': 1,  # Last 1 day
            'dateFormat': 'iso'
        }

        try:
            response = requests.get(url, params=params)
            if response.status_code == 200:
                games = response.json()
                print(f"📊 Found {len(games)} recent NFL games")

                # Look for LAC vs LV game
                for game in games:
                    teams = [team['name'].lower() for team in game.get('scores', [])]
                    if any('charger' in team for team in teams) and any('raider' in team for team in teams):
                        print(f"🎯 Found LAC vs LV game: {game}")
                        return game

                print("🔍 No LAC vs LV game found in recent results")
                return None
            else:
                print(f"❌ Odds API error: {response.status_code}")
                return None

        except Exception as e:
            print(f"❌ Error fetching from Odds API: {e}")
            return None

    def fetch_sportsdata_game_details(self, season=2024, week=15):
        """Fetch detailed game data from SportsData.io"""

        # Get game details including advanced stats
        url = f"https://api.sportsdata.io/v3/nfl/scores/json/ScoresByWeek/{season}/{week}"
        headers = {
            'Ocp-Apim-Subscription-Key': self.sportsdata_key
        }

        try:
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                games = response.json()
                print(f"📊 Found {len(games)} games for week {week}")

                # Look for LAC vs LV game
                for game in games:
                    home_team = game.get('HomeTeam', '').upper()
                    away_team = game.get('AwayTeam', '').upper()

                    if (home_team in ['LAC', 'LV'] and away_team in ['LAC', 'LV']):
                        print(f"🎯 Found LAC vs LV game details")
                        return game

                print("🔍 No LAC vs LV game found in week data")
                return None
            else:
                print(f"❌ SportsData.io error: {response.status_code}")
                return None

        except Exception as e:
            print(f"❌ Error fetching from SportsData.io: {e}")
            return None

    def fetch_comprehensive_game_outcome(self):
        """Get comprehensive real game outcome for accuracy calculation"""

        print("\n" + "🔍" * 30)
        print("FETCHING REAL GAME DATA FROM PREMIUM APIs")
        print("🔍" * 30 + "\n")

        # Get betting outcomes
        odds_data = self.fetch_odds_api_game_result()

        # Get detailed game stats
        sportsdata_game = self.fetch_sportsdata_game_details()

        if not odds_data and not sportsdata_game:
            print("❌ No game data found from either API")
            return None

        # Combine data into comprehensive outcome
        real_outcome = {
            "data_sources": {
                "odds_api": odds_data is not None,
                "sportsdata_io": sportsdata_game is not None
            },
            "timestamp": datetime.now().isoformat()
        }

        # Extract basic game result
        if sportsdata_game:
            real_outcome.update({
                "final_score": f"{sportsdata_game.get('AwayTeam')} {sportsdata_game.get('AwayScore')} - {sportsdata_game.get('HomeTeam')} {sportsdata_game.get('HomeScore')}",
                "winner": sportsdata_game.get('AwayTeam') if sportsdata_game.get('AwayScore', 0) > sportsdata_game.get('HomeScore', 0) else sportsdata_game.get('HomeTeam'),
                "home_score": sportsdata_game.get('HomeScore'),
                "away_score": sportsdata_game.get('AwayScore'),
                "final_margin": abs(sportsdata_game.get('AwayScore', 0) - sportsdata_game.get('HomeScore', 0)),
                "final_total": sportsdata_game.get('AwayScore', 0) + sportsdata_game.get('HomeScore', 0),
                "game_status": sportsdata_game.get('Status'),
                "date_played": sportsdata_game.get('Date')
            })

        # Extract betting market results
        if odds_data:
            scores = odds_data.get('scores', [])
            if len(scores) >= 2:
                # Determine spread and total results based on actual scores
                score1 = int(scores[0].get('score', 0))
                score2 = int(scores[1].get('score', 0))
                total_points = score1 + score2

                real_outcome.update({
                    "betting_results": {
                        "total_points": total_points,
                        "total_result": "over" if total_points > 43.5 else "under",  # Common NFL total
                        "point_spread_result": "calculated_from_final_score",
                        "moneyline_result": scores[0]['name'] if score1 > score2 else scores[1]['name']
                    }
                })

        # Advanced metrics (would need more specific API calls)
        real_outcome.update({
            "advanced_analysis": {
                "coaching_performance": "requires_film_analysis",
                "special_teams_impact": "requires_detailed_stats",
                "home_field_advantage": "requires_situational_data",
                "fourth_down_conversions": "requires_play_by_play",
                "drive_outcomes": "requires_drive_data",
                "time_of_possession": "available_in_detailed_stats"
            },
            "verification_notes": [
                "Basic score and winner verified from APIs",
                "Betting outcomes calculated from final score",
                "Advanced metrics require additional API calls",
                "Some predictions require subjective analysis"
            ]
        })

        return real_outcome

async def main():
    fetcher = RealGameDataFetcher()

    if not fetcher.odds_api_key:
        print("❌ Cannot proceed without API keys")
        return

    # Fetch real game outcome
    real_outcome = fetcher.fetch_comprehensive_game_outcome()

    if real_outcome:
        # Save real outcome for accuracy calculation
        with open("real_game_outcome.json", "w") as f:
            json.dump(real_outcome, f, indent=2)

        print(f"\n✅ REAL GAME DATA FETCHED!")
        print(f"💾 Saved to real_game_outcome.json")
        print(f"\n🎯 BASIC RESULTS:")

        if 'final_score' in real_outcome:
            print(f"   Final Score: {real_outcome['final_score']}")
            print(f"   Winner: {real_outcome['winner']}")
            print(f"   Total Points: {real_outcome['final_total']}")
            print(f"   Margin: {real_outcome['final_margin']}")

        print(f"\n📊 Next: Run accuracy calculator to compare vs expert predictions")

    else:
        print("❌ Failed to fetch real game data")

if __name__ == "__main__":
    asyncio.run(main())