"""
Historical Data Collector for NFL ML Engine
Collects and processes 3 years of NFL data (2022-2024) for training ML models.
"""

import asyncio
import aiohttp
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import logging
import json
import os
from dataclasses import dataclass

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class GameResult:
    """Historical game result data"""
    game_id: str
    date: datetime
    week: int
    season: int
    home_team: str
    away_team: str
    home_score: int
    away_score: int
    winner: str
    margin: int
    total_points: int
    
    # Betting data
    opening_spread: Optional[float] = None
    closing_spread: Optional[float] = None
    opening_total: Optional[float] = None
    closing_total: Optional[float] = None
    
    # Environmental
    weather_temp: Optional[float] = None
    weather_wind: Optional[float] = None
    weather_conditions: Optional[str] = None
    is_dome: bool = False

@dataclass
class PlayerGameLog:
    """Individual player performance in a game"""
    player_id: str
    player_name: str
    team: str
    opponent: str
    date: datetime
    week: int
    season: int
    position: str
    
    # Passing stats
    passing_yards: int = 0
    passing_tds: int = 0
    passing_attempts: int = 0
    passing_completions: int = 0
    
    # Rushing stats
    rushing_yards: int = 0
    rushing_tds: int = 0
    rushing_attempts: int = 0
    
    # Receiving stats
    receiving_yards: int = 0
    receiving_tds: int = 0
    receptions: int = 0
    targets: int = 0
    
    # Advanced stats
    snap_count: Optional[int] = None
    snap_percentage: Optional[float] = None

class HistoricalDataCollector:
    """
    Collects historical NFL data from multiple sources for ML training.
    Focuses on 2022-2024 seasons for comprehensive dataset.
    """
    
    def __init__(self):
        self.seasons = [2022, 2023, 2024]
        self.data_dir = "data/historical"
        self.ensure_data_directory()
        
        # API keys from environment
        self.sportsdata_key = "bc297647c7aa4ef29747e6a85cb575dc"
        self.odds_api_key = "415cf3d0662545e66f7c31e0c30ac2c4"
        
        # Data storage
        self.game_results: List[GameResult] = []
        self.player_logs: List[PlayerGameLog] = []
        
    def ensure_data_directory(self):
        """Create data directory structure"""
        os.makedirs(self.data_dir, exist_ok=True)
        os.makedirs(f"{self.data_dir}/games", exist_ok=True)
        os.makedirs(f"{self.data_dir}/players", exist_ok=True)
        os.makedirs(f"{self.data_dir}/betting", exist_ok=True)
        
    async def collect_all_historical_data(self):
        """Main method to collect all historical data"""
        logger.info("🏈 Starting historical data collection for 2022-2024 seasons")
        
        for season in self.seasons:
            logger.info(f"📊 Collecting data for {season} season")
            
            # Collect game results
            await self.collect_season_games(season)
            
            # Collect player stats
            await self.collect_season_player_stats(season)
            
            # Collect betting data
            await self.collect_season_betting_data(season)
            
            logger.info(f"✅ Completed {season} season data collection")
        
        # Save all collected data
        await self.save_historical_data()
        
        logger.info(f"🎉 Historical data collection complete!")
        logger.info(f"📈 Collected {len(self.game_results)} games and {len(self.player_logs)} player performances")
        
    async def collect_season_games(self, season: int):
        """Collect all games for a season"""
        try:
            url = f"https://api.sportsdata.io/v3/nfl/scores/json/Scores/{season}"
            headers = {"Ocp-Apim-Subscription-Key": self.sportsdata_key}
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers, timeout=aiohttp.ClientTimeout(total=30)) as response:
                    if response.status == 200:
                        games_data = await response.json()
                        
                        for game_data in games_data:
                            if game_data.get('Status') == 'Final':  # Only completed games
                                game_result = self.parse_game_result(game_data, season)
                                if game_result:
                                    self.game_results.append(game_result)
                        
                        logger.info(f"✅ Collected {len([g for g in self.game_results if g.season == season])} games for {season}")
                    else:
                        logger.error(f"❌ Failed to fetch {season} games: {response.status}")
                        
        except Exception as e:
            logger.error(f"❌ Error collecting {season} games: {e}")
            
    def parse_game_result(self, game_data: Dict, season: int) -> Optional[GameResult]:
        """Parse raw game data into GameResult object"""
        try:
            home_score = game_data.get('HomeScore', 0) or 0
            away_score = game_data.get('AwayScore', 0) or 0
            
            # Determine winner and margin
            if home_score > away_score:
                winner = game_data.get('HomeTeam', '')
                margin = home_score - away_score
            elif away_score > home_score:
                winner = game_data.get('AwayTeam', '')
                margin = away_score - home_score
            else:
                winner = 'TIE'
                margin = 0
            
            # Parse date
            date_str = game_data.get('Date', '')
            if date_str:
                date = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            else:
                return None
                
            return GameResult(
                game_id=str(game_data.get('GameKey', '')),
                date=date,
                week=game_data.get('Week', 0),
                season=season,
                home_team=game_data.get('HomeTeam', ''),
                away_team=game_data.get('AwayTeam', ''),
                home_score=home_score,
                away_score=away_score,
                winner=winner,
                margin=margin,
                total_points=home_score + away_score,
                weather_temp=game_data.get('Temperature'),
                weather_wind=game_data.get('WindSpeed'),
                weather_conditions=game_data.get('WeatherDescription'),
                is_dome=game_data.get('IsDome', False)
            )
            
        except Exception as e:
            logger.error(f"❌ Error parsing game data: {e}")
            return None
            
    async def collect_season_player_stats(self, season: int):
        """Collect player statistics for a season"""
        try:
            # Get player stats by week (this is a simplified approach)
            for week in range(1, 19):  # 18 weeks
                await self.collect_week_player_stats(season, week)
                await asyncio.sleep(1)  # Rate limiting
                
        except Exception as e:
            logger.error(f"❌ Error collecting {season} player stats: {e}")
            
    async def collect_week_player_stats(self, season: int, week: int):
        """Collect player stats for a specific week"""
        try:
            url = f"https://api.sportsdata.io/v3/nfl/stats/json/PlayerGameStatsByWeek/{season}/{week}"
            headers = {"Ocp-Apim-Subscription-Key": self.sportsdata_key}
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers, timeout=aiohttp.ClientTimeout(total=30)) as response:
                    if response.status == 200:
                        stats_data = await response.json()
                        
                        for player_data in stats_data:
                            player_log = self.parse_player_stats(player_data, season, week)
                            if player_log:
                                self.player_logs.append(player_log)
                                
                    elif response.status == 429:  # Rate limited
                        logger.warning(f"⚠️ Rate limited, waiting...")
                        await asyncio.sleep(5)
                    else:
                        logger.warning(f"⚠️ Failed to fetch week {week} {season} player stats: {response.status}")
                        
        except Exception as e:
            logger.error(f"❌ Error collecting week {week} {season} player stats: {e}")
            
    def parse_player_stats(self, player_data: Dict, season: int, week: int) -> Optional[PlayerGameLog]:
        """Parse raw player stats into PlayerGameLog object"""
        try:
            # Parse date
            date_str = player_data.get('Date', '')
            if date_str:
                date = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            else:
                date = datetime.now()  # Fallback
                
            return PlayerGameLog(
                player_id=str(player_data.get('PlayerID', '')),
                player_name=player_data.get('Name', ''),
                team=player_data.get('Team', ''),
                opponent=player_data.get('Opponent', ''),
                date=date,
                week=week,
                season=season,
                position=player_data.get('Position', ''),
                
                # Passing stats
                passing_yards=player_data.get('PassingYards', 0) or 0,
                passing_tds=player_data.get('PassingTouchdowns', 0) or 0,
                passing_attempts=player_data.get('PassingAttempts', 0) or 0,
                passing_completions=player_data.get('PassingCompletions', 0) or 0,
                
                # Rushing stats
                rushing_yards=player_data.get('RushingYards', 0) or 0,
                rushing_tds=player_data.get('RushingTouchdowns', 0) or 0,
                rushing_attempts=player_data.get('RushingAttempts', 0) or 0,
                
                # Receiving stats
                receiving_yards=player_data.get('ReceivingYards', 0) or 0,
                receiving_tds=player_data.get('ReceivingTouchdowns', 0) or 0,
                receptions=player_data.get('Receptions', 0) or 0,
                targets=player_data.get('Targets', 0) or 0,
                
                # Advanced stats
                snap_count=player_data.get('OffensiveSnapsPlayed'),
                snap_percentage=player_data.get('OffensiveSnapPercentage')
            )
            
        except Exception as e:
            logger.error(f"❌ Error parsing player stats: {e}")
            return None
            
    async def collect_season_betting_data(self, season: int):
        """Collect historical betting lines (simplified for now)"""
        logger.info(f"📊 Collecting betting data for {season} (using game data)")
        
        # For now, we'll use the spread data from game results
        # In production, you'd want to collect actual historical betting lines
        for game in self.game_results:
            if game.season == season:
                # Simulate historical betting lines based on final scores
                # This is a placeholder - real implementation would use historical odds
                game.opening_spread = self.estimate_opening_spread(game)
                game.closing_spread = game.opening_spread  # Simplified
                game.opening_total = self.estimate_opening_total(game)
                game.closing_total = game.opening_total  # Simplified
                
    def estimate_opening_spread(self, game: GameResult) -> float:
        """Estimate opening spread based on final result (placeholder)"""
        # This is a simplified estimation - real data would come from historical odds
        margin = game.margin
        if game.winner == game.home_team:
            return -margin * 0.8  # Home team favored
        else:
            return margin * 0.8   # Away team favored
            
    def estimate_opening_total(self, game: GameResult) -> float:
        """Estimate opening total based on final score (placeholder)"""
        # This is a simplified estimation - real data would come from historical odds
        return game.total_points * 0.95  # Slightly under actual total
        
    async def save_historical_data(self):
        """Save all collected data to files"""
        logger.info("💾 Saving historical data to files...")
        
        # Save game results
        games_df = pd.DataFrame([
            {
                'game_id': g.game_id,
                'date': g.date.isoformat(),
                'week': g.week,
                'season': g.season,
                'home_team': g.home_team,
                'away_team': g.away_team,
                'home_score': g.home_score,
                'away_score': g.away_score,
                'winner': g.winner,
                'margin': g.margin,
                'total_points': g.total_points,
                'opening_spread': g.opening_spread,
                'closing_spread': g.closing_spread,
                'opening_total': g.opening_total,
                'closing_total': g.closing_total,
                'weather_temp': g.weather_temp,
                'weather_wind': g.weather_wind,
                'weather_conditions': g.weather_conditions,
                'is_dome': g.is_dome
            }
            for g in self.game_results
        ])
        
        games_df.to_csv(f"{self.data_dir}/games/historical_games.csv", index=False)
        logger.info(f"✅ Saved {len(games_df)} games to historical_games.csv")
        
        # Save player logs
        players_df = pd.DataFrame([
            {
                'player_id': p.player_id,
                'player_name': p.player_name,
                'team': p.team,
                'opponent': p.opponent,
                'date': p.date.isoformat(),
                'week': p.week,
                'season': p.season,
                'position': p.position,
                'passing_yards': p.passing_yards,
                'passing_tds': p.passing_tds,
                'passing_attempts': p.passing_attempts,
                'passing_completions': p.passing_completions,
                'rushing_yards': p.rushing_yards,
                'rushing_tds': p.rushing_tds,
                'rushing_attempts': p.rushing_attempts,
                'receiving_yards': p.receiving_yards,
                'receiving_tds': p.receiving_tds,
                'receptions': p.receptions,
                'targets': p.targets,
                'snap_count': p.snap_count,
                'snap_percentage': p.snap_percentage
            }
            for p in self.player_logs
        ])
        
        players_df.to_csv(f"{self.data_dir}/players/historical_player_stats.csv", index=False)
        logger.info(f"✅ Saved {len(players_df)} player performances to historical_player_stats.csv")
        
        # Save summary statistics
        summary = {
            'collection_date': datetime.now().isoformat(),
            'seasons_collected': self.seasons,
            'total_games': len(self.game_results),
            'total_player_performances': len(self.player_logs),
            'games_by_season': {
                season: len([g for g in self.game_results if g.season == season])
                for season in self.seasons
            },
            'players_by_season': {
                season: len([p for p in self.player_logs if p.season == season])
                for season in self.seasons
            }
        }
        
        with open(f"{self.data_dir}/collection_summary.json", 'w') as f:
            json.dump(summary, f, indent=2)
            
        logger.info("✅ Saved collection summary")
        
    def get_data_summary(self) -> Dict[str, Any]:
        """Get summary of collected data"""
        return {
            'total_games': len(self.game_results),
            'total_player_performances': len(self.player_logs),
            'seasons': self.seasons,
            'date_range': {
                'start': min(g.date for g in self.game_results).isoformat() if self.game_results else None,
                'end': max(g.date for g in self.game_results).isoformat() if self.game_results else None
            }
        }

# Main execution function
async def main():
    """Main function to run historical data collection"""
    collector = HistoricalDataCollector()
    await collector.collect_all_historical_data()
    
    summary = collector.get_data_summary()
    print("\n🎉 Historical Data Collection Complete!")
    print(f"📊 Total Games: {summary['total_games']}")
    print(f"👥 Total Player Performances: {summary['total_player_performances']}")
    print(f"📅 Date Range: {summary['date_range']['start']} to {summary['date_range']['end']}")

if __name__ == "__main__":
    asyncio.run(main())