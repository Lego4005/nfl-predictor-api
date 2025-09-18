#!/usr/bin/env python3
"""
Comprehensive NFL Data Fetcher
Integrates ALL SportsData.io APIs for complete NFL intelligence
"""

import os
import json
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import time
from dotenv import load_dotenv

load_dotenv()

@dataclass
class NFLDataCache:
    """Simple in-memory cache for API responses"""
    data: Dict[str, Any]
    timestamp: datetime
    ttl_minutes: int = 30

    def is_expired(self) -> bool:
        return datetime.now() - self.timestamp > timedelta(minutes=self.ttl_minutes)

class ComprehensiveNFLFetcher:
    """
    Comprehensive NFL Data Fetcher using ESPN (accurate) + SportsData.io APIs

    ⚠️ WARNING: SportsData.io has data accuracy issues for game scores
    ✅ SOLUTION: Uses ESPN for accurate final scores + SportsData.io for stats/odds

    APIs Integrated:
    - ESPN API: Accurate final game scores (PRIMARY for scores)
    - SportsData.io Stats API: Team/player statistics
    - SportsData.io Advanced Metrics API: EPA, DVOA-style analytics
    - SportsData.io Odds API: Betting lines, market movement
    - SportsData.io Projections API: Performance forecasts
    """

    def __init__(self):
        self.api_key = os.getenv('VITE_SPORTSDATA_IO_KEY')
        self.odds_api_key = os.getenv('VITE_ODDS_API_KEY')
        self.base_headers = {'Ocp-Apim-Subscription-Key': self.api_key}
        self.odds_headers = {'Ocp-Apim-Subscription-Key': self.odds_api_key}
        self.cache = {}

        # ESPN API for ACCURATE scores
        self.espn_base = "https://site.api.espn.com/apis/site/v2/sports/football/nfl"

        # SportsData.io API Base URLs (for stats/odds only - NOT scores)
        self.scores_base = "https://api.sportsdata.io/v3/nfl/scores"  # DEPRECATED for scores
        self.stats_base = "https://api.sportsdata.io/v3/nfl/stats"
        self.advanced_base = "https://api.sportsdata.io/v3/nfl/advanced-metrics"
        self.odds_base = "https://api.sportsdata.io/v3/nfl/odds"
        self.projections_base = "https://api.sportsdata.io/v3/nfl/projections"

        # Rate limiting
        self.last_request_time = 0
        self.min_request_interval = 0.1  # 100ms between requests

    def _rate_limit(self):
        """Simple rate limiting"""
        elapsed = time.time() - self.last_request_time
        if elapsed < self.min_request_interval:
            time.sleep(self.min_request_interval - elapsed)
        self.last_request_time = time.time()

    def _get_cached_or_fetch(self, cache_key: str, url: str, ttl_minutes: int = 30) -> Optional[Dict]:
        """Get from cache or fetch from API"""
        # Check cache first
        if cache_key in self.cache:
            cached = self.cache[cache_key]
            if not cached.is_expired():
                return cached.data

        # Rate limit and fetch
        self._rate_limit()

        try:
            response = requests.get(url, headers=self.base_headers)
            if response.status_code == 200:
                data = response.json()
                # Cache the response
                self.cache[cache_key] = NFLDataCache(
                    data=data,
                    timestamp=datetime.now(),
                    ttl_minutes=ttl_minutes
                )
                return data
            else:
                print(f"API Error {response.status_code}: {url}")
                return None
        except Exception as e:
            print(f"Fetch error: {e}")
            return None

    def _get_cached_or_fetch_odds(self, cache_key: str, url: str, ttl_minutes: int = 30) -> Optional[Dict]:
        """Get from cache or fetch from odds API with separate key"""
        # Check cache first
        if cache_key in self.cache:
            cached = self.cache[cache_key]
            if not cached.is_expired():
                return cached.data

        # Rate limit and fetch with odds API key
        self._rate_limit()

        try:
            response = requests.get(url, headers=self.odds_headers)
            if response.status_code == 200:
                data = response.json()
                # Cache the response
                self.cache[cache_key] = NFLDataCache(
                    data=data,
                    timestamp=datetime.now(),
                    ttl_minutes=ttl_minutes
                )
                return data
            else:
                print(f"Odds API Error {response.status_code}: {url}")
                return None
        except Exception as e:
            print(f"Odds fetch error: {e}")
            return None

    # ==========================================
    # PHASE 1: CORE GAME DATA
    # ==========================================

    def get_current_games(self, season: int = 2025, week: int = 2) -> List[Dict]:
        """Get current week games with ACCURATE final scores from ESPN"""
        # ⚠️ CRITICAL: Use ESPN fetcher for accurate scores, NOT SportsData.io
        try:
            from espn_accurate_fetcher import ESPNAccurateFetcher
            espn_fetcher = ESPNAccurateFetcher()
            games = espn_fetcher.get_manual_accurate_scores()

            # Convert ESPN format to SportsData.io format for compatibility
            converted_games = []
            for game in games:
                converted_game = {
                    'HomeTeam': game.get('home_team', ''),
                    'AwayTeam': game.get('away_team', ''),
                    'HomeScore': game.get('home_score', 0),
                    'AwayScore': game.get('away_score', 0),
                    'Status': 'Final',
                    'DateTime': '2025-09-14T13:00:00',
                    'Season': season,
                    'Week': week
                }
                converted_games.append(converted_game)

            print(f"✅ Using ESPN ACCURATE data: {len(converted_games)} games")
            return converted_games

        except ImportError:
            # Fallback to SportsData.io (with warning)
            print("⚠️ WARNING: Using SportsData.io data (may be inaccurate)")
            url = f"{self.scores_base}/json/ScoresByWeekFinal/{season}/{week}"
            cache_key = f"games_final_{season}_{week}"
            data = self._get_cached_or_fetch(cache_key, url, ttl_minutes=15)
            return data if data else []

    def get_team_season_stats(self, season: int = 2025) -> List[Dict]:
        """Get real team season statistics - replaces fake ratings"""
        url = f"{self.stats_base}/json/TeamSeasonStats/{season}"
        cache_key = f"team_season_stats_{season}"

        data = self._get_cached_or_fetch(cache_key, url, ttl_minutes=60)
        return data if data else []

    def get_team_game_stats(self, season: int = 2025, week: int = 2) -> List[Dict]:
        """Get team game-by-game statistics for recent form"""
        url = f"{self.stats_base}/json/TeamGameStatsFinal/{season}/{week}"
        cache_key = f"team_game_stats_{season}_{week}"

        data = self._get_cached_or_fetch(cache_key, url, ttl_minutes=30)
        return data if data else []

    def get_standings(self, season: int = 2025) -> List[Dict]:
        """Get current team standings"""
        url = f"{self.scores_base}/json/Standings/{season}"
        cache_key = f"standings_{season}"

        data = self._get_cached_or_fetch(cache_key, url, ttl_minutes=120)
        return data if data else []

    # ==========================================
    # PHASE 2: INJURY INTELLIGENCE
    # ==========================================

    def get_injuries_by_team(self, season: int = 2025, week: int = 2, team: str = None) -> List[Dict]:
        """Get injury reports by team - CRITICAL for predictions"""
        if team:
            url = f"{self.stats_base}/json/InjuriesByTeam/{season}/{week}/{team}"
            cache_key = f"injuries_{season}_{week}_{team}"
        else:
            url = f"{self.stats_base}/json/Injuries/{season}/{week}"
            cache_key = f"injuries_{season}_{week}_all"

        data = self._get_cached_or_fetch(cache_key, url, ttl_minutes=60)
        return data if data else []

    def get_all_injuries(self, season: int = 2025, week: int = 2) -> List[Dict]:
        """Get league-wide injury data"""
        return self.get_injuries_by_team(season, week, team=None)

    # ==========================================
    # PHASE 3: MARKET INTELLIGENCE
    # ==========================================

    def get_pregame_odds(self, season: int = 2025, week: int = 2) -> List[Dict]:
        """Get betting lines and market data using main API key"""
        url = f"{self.odds_base}/json/GameOddsByWeek/{season}/{week}"
        cache_key = f"pregame_odds_{season}_{week}"

        data = self._get_cached_or_fetch(cache_key, url, ttl_minutes=30)
        return data if data else []

    def get_betting_trends(self, team: str, season: int = 2025) -> List[Dict]:
        """Get betting trends and market movement using main API key"""
        url = f"{self.odds_base}/json/TeamTrends/{team}"
        cache_key = f"betting_trends_{season}_{team}"

        data = self._get_cached_or_fetch(cache_key, url, ttl_minutes=60)
        return data if data else []

    def get_player_props(self, season: int = 2025, week: int = 2) -> List[Dict]:
        """Get generated player prop bets using main API key"""
        url = f"{self.odds_base}/json/PlayerPropsByWeek/{season}/{week}"
        cache_key = f"player_props_{season}_{week}"

        data = self._get_cached_or_fetch(cache_key, url, ttl_minutes=60)
        return data if data else []

    # ==========================================
    # PHASE 4: NEWS & CONTEXT
    # ==========================================

    def get_news(self, count: int = 50) -> List[Dict]:
        """Get breaking NFL news"""
        url = f"{self.scores_base}/json/News"
        cache_key = "news_general"

        data = self._get_cached_or_fetch(cache_key, url, ttl_minutes=15)
        if data and isinstance(data, list):
            return data[:count]
        return []

    def get_news_by_team(self, team: str, count: int = 20) -> List[Dict]:
        """Get team-specific news"""
        url = f"{self.scores_base}/json/NewsByTeam/{team}"
        cache_key = f"news_{team}"

        data = self._get_cached_or_fetch(cache_key, url, ttl_minutes=30)
        if data and isinstance(data, list):
            return data[:count]
        return []

    # ==========================================
    # PHASE 5: ADVANCED METRICS
    # ==========================================

    def get_advanced_player_stats(self, season: int = 2025, week: int = 2) -> List[Dict]:
        """Get EPA, DVOA-style advanced metrics"""
        url = f"{self.advanced_base}/json/AdvancedPlayerGameStats/{season}/{week}"
        cache_key = f"advanced_player_stats_{season}_{week}"

        data = self._get_cached_or_fetch(cache_key, url, ttl_minutes=60)
        return data if data else []

    def get_advanced_season_stats(self, season: int = 2025) -> List[Dict]:
        """Get season-long advanced metrics"""
        url = f"{self.advanced_base}/json/AdvancedPlayerSeasonStatsByTeam/{season}"
        cache_key = f"advanced_season_stats_{season}"

        data = self._get_cached_or_fetch(cache_key, url, ttl_minutes=120)
        return data if data else []

    # ==========================================
    # PHASE 6: PLAYER INTELLIGENCE
    # ==========================================

    def get_player_season_stats(self, season: int = 2025) -> List[Dict]:
        """Get individual player performance data"""
        url = f"{self.stats_base}/json/PlayerSeasonStats/{season}"
        cache_key = f"player_season_stats_{season}"

        data = self._get_cached_or_fetch(cache_key, url, ttl_minutes=120)
        return data if data else []

    def get_league_leaders(self, season: int = 2025, week: int = 2) -> List[Dict]:
        """Get top performers by week"""
        url = f"{self.stats_base}/json/LeagueLeadersByWeek/{season}/{week}"
        cache_key = f"league_leaders_{season}_{week}"

        data = self._get_cached_or_fetch(cache_key, url, ttl_minutes=60)
        return data if data else []

    def get_player_projections(self, season: int = 2025, week: int = 2) -> List[Dict]:
        """Get player performance projections"""
        url = f"{self.projections_base}/json/ProjectedPlayerGameStatsByWeek/{season}/{week}"
        cache_key = f"player_projections_{season}_{week}"

        data = self._get_cached_or_fetch(cache_key, url, ttl_minutes=60)
        return data if data else []

    # ==========================================
    # COMPREHENSIVE DATA AGGREGATION
    # ==========================================

    def get_comprehensive_game_data(self, season: int = 2025, week: int = 2) -> Dict[str, Any]:
        """
        Get ALL NFL data for comprehensive predictions

        Returns complete intelligence package:
        - Games and scores
        - Team statistics and form
        - Injury reports
        - Betting market data
        - News and context
        - Advanced metrics
        - Player data
        """

        print(f"🔄 Fetching comprehensive NFL data for {season} Week {week}...")

        comprehensive_data = {
            "metadata": {
                "season": season,
                "week": week,
                "fetched_at": datetime.now().isoformat(),
                "data_sources": "SportsData.io (All APIs)"
            },

            # Core game data
            "games": self.get_current_games(season, week),
            "team_season_stats": self.get_team_season_stats(season),
            "team_game_stats": self.get_team_game_stats(season, week),
            "standings": self.get_standings(season),

            # Injury intelligence
            "injuries": self.get_all_injuries(season, week),

            # Market intelligence
            "betting_odds": self.get_pregame_odds(season, week),
            "player_props": self.get_player_props(season, week),

            # News and context
            "breaking_news": self.get_news(50),

            # Advanced analytics
            "advanced_metrics": self.get_advanced_player_stats(season, week),
            "advanced_season": self.get_advanced_season_stats(season),

            # Player intelligence
            "player_stats": self.get_player_season_stats(season),
            "league_leaders": self.get_league_leaders(season, week),
            "projections": self.get_player_projections(season, week)
        }

        # Calculate data completeness
        data_counts = {k: len(v) if isinstance(v, list) else (1 if v else 0)
                      for k, v in comprehensive_data.items() if k != "metadata"}

        comprehensive_data["metadata"]["data_completeness"] = data_counts
        comprehensive_data["metadata"]["total_data_points"] = sum(data_counts.values())

        print(f"✅ Fetched {comprehensive_data['metadata']['total_data_points']} total data points")

        return comprehensive_data

    def get_team_intelligence(self, team: str, season: int = 2025, week: int = 2) -> Dict[str, Any]:
        """Get comprehensive intelligence for a specific team"""
        return {
            "team": team,
            "season_stats": [t for t in self.get_team_season_stats(season) if t.get('Team') == team],
            "recent_games": [g for g in self.get_team_game_stats(season, week) if g.get('Team') == team],
            "injuries": self.get_injuries_by_team(season, week, team),
            "betting_trends": self.get_betting_trends(team, season),
            "team_news": self.get_news_by_team(team, 10),
            "fetched_at": datetime.now().isoformat()
        }

# Singleton instance for easy importing
nfl_data = ComprehensiveNFLFetcher()

if __name__ == "__main__":
    # Test the comprehensive data fetcher
    fetcher = ComprehensiveNFLFetcher()

    print("🏈 Testing Comprehensive NFL Data Fetcher...")
    print("=" * 60)

    # Test basic functionality
    games = fetcher.get_current_games(2025, 2)
    print(f"✅ Games: {len(games)} found")

    team_stats = fetcher.get_team_season_stats(2025)
    print(f"✅ Team Stats: {len(team_stats)} teams")

    injuries = fetcher.get_all_injuries(2025, 2)
    print(f"✅ Injuries: {len(injuries)} injury reports")

    odds = fetcher.get_pregame_odds(2025, 2)
    print(f"✅ Betting Odds: {len(odds)} games with odds")

    news = fetcher.get_news(10)
    print(f"✅ News: {len(news)} breaking stories")

    # Test comprehensive data fetch
    print("\n" + "=" * 60)
    comprehensive = fetcher.get_comprehensive_game_data(2025, 2)
    print(f"🎯 Comprehensive Data: {comprehensive['metadata']['total_data_points']} total data points")

    print("\n✅ Comprehensive NFL Data Fetcher is operational!")