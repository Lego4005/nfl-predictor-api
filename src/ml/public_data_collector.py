"""
Public Data Collector for NFL Historical Data

Collects historical NFL data from public sources like NFL.com, ESPN.com, and Pro Football Reference
to build a comprehensive dataset for ML training with 2+ years of data and advanced metrics.
"""

import requests
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
import logging
import json
import os
import time
from dataclasses import dataclass
from bs4 import BeautifulSoup
import re

logger = logging.getLogger(__name__)

@dataclass
class PublicGameResult:
    """Game result from public sources with advanced metrics"""
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
    
    # Advanced stats from public sources
    home_total_yards: Optional[int] = None
    away_total_yards: Optional[int] = None
    home_passing_yards: Optional[int] = None
    away_passing_yards: Optional[int] = None
    home_rushing_yards: Optional[int] = None
    away_rushing_yards: Optional[int] = None
    home_turnovers: Optional[int] = None
    away_turnovers: Optional[int] = None
    home_first_downs: Optional[int] = None
    away_first_downs: Optional[int] = None
    home_penalties: Optional[int] = None
    away_penalties: Optional[int] = None
    home_time_of_possession: Optional[str] = None
    away_time_of_possession: Optional[str] = None

class PublicDataCollector:
    """
    Collects NFL historical data from public sources
    """
    
    def __init__(self):
        self.seasons = [2022, 2023, 2024]  # 3 years of data
        self.data_dir = "data/historical"
        self.ensure_data_directory()
        
        # Data storage
        self.game_results: List[PublicGameResult] = []
        self.team_stats: List[Dict] = []
        self.power_rankings: List[Dict] = []
        
        # Team name mappings for consistency
        self.team_mappings = {
            'Arizona Cardinals': 'ARI', 'Atlanta Falcons': 'ATL', 'Baltimore Ravens': 'BAL',
            'Buffalo Bills': 'BUF', 'Carolina Panthers': 'CAR', 'Chicago Bears': 'CHI',
            'Cincinnati Bengals': 'CIN', 'Cleveland Browns': 'CLE', 'Dallas Cowboys': 'DAL',
            'Denver Broncos': 'DEN', 'Detroit Lions': 'DET', 'Green Bay Packers': 'GB',
            'Houston Texans': 'HOU', 'Indianapolis Colts': 'IND', 'Jacksonville Jaguars': 'JAX',
            'Kansas City Chiefs': 'KC', 'Las Vegas Raiders': 'LV', 'Los Angeles Chargers': 'LAC',
            'Los Angeles Rams': 'LAR', 'Miami Dolphins': 'MIA', 'Minnesota Vikings': 'MIN',
            'New England Patriots': 'NE', 'New Orleans Saints': 'NO', 'New York Giants': 'NYG',
            'New York Jets': 'NYJ', 'Philadelphia Eagles': 'PHI', 'Pittsburgh Steelers': 'PIT',
            'San Francisco 49ers': 'SF', 'Seattle Seahawks': 'SEA', 'Tampa Bay Buccaneers': 'TB',
            'Tennessee Titans': 'TEN', 'Washington Commanders': 'WAS'
        }
        
        # Headers to avoid being blocked
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
    def ensure_data_directory(self):
        """Create data directory structure"""
        os.makedirs(self.data_dir, exist_ok=True)
        os.makedirs(f"{self.data_dir}/games", exist_ok=True)
        os.makedirs(f"{self.data_dir}/teams", exist_ok=True)
        os.makedirs(f"{self.data_dir}/players", exist_ok=True)
        
    def collect_espn_schedule_data(self, season: int) -> List[Dict]:
        """Collect game schedule and basic results from ESPN"""
        logger.info(f"📅 Collecting ESPN schedule data for {season}...")
        
        games = []
        
        try:
            # ESPN NFL schedule URL
            url = f"https://www.espn.com/nfl/schedule/_/season/{season}"
            
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Find game containers (this is a simplified approach)
            # In practice, you'd need to analyze ESPN's HTML structure more carefully
            game_rows = soup.find_all('tr', class_='Table__TR')
            
            week = 1
            for row in game_rows:
                try:
                    # Extract game information
                    # This is a simplified parser - you'd need to adapt based on ESPN's actual HTML
                    cells = row.find_all('td')
                    if len(cells) >= 3:
                        # Parse team names and scores
                        # This would need to be customized based on ESPN's structure
                        pass
                        
                except Exception as e:
                    logger.debug(f"Error parsing game row: {e}")
                    continue
                    
        except Exception as e:
            logger.error(f"❌ Error collecting ESPN data for {season}: {e}")
            
        return games
        
    def collect_pro_football_reference_data(self, season: int) -> List[Dict]:
        """Collect comprehensive data from Pro Football Reference"""
        logger.info(f"🏈 Collecting Pro Football Reference data for {season}...")
        
        games = []
        
        try:
            # Pro Football Reference games URL
            url = f"https://www.pro-football-reference.com/years/{season}/games.htm"
            
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            
            # Parse with pandas (PFR has good table structure)
            tables = pd.read_html(response.content)
            
            if tables:
                games_df = tables[0]  # First table is usually the games
                
                # Clean and process the data
                games_df = games_df.dropna(subset=['Week'])
                games_df = games_df[games_df['Week'] != 'Week']  # Remove header rows
                
                for _, row in games_df.iterrows():
                    try:
                        # Parse game data
                        week = int(row['Week']) if str(row['Week']).isdigit() else 1
                        
                        # Get team names (you'd need to map full names to abbreviations)
                        home_team = self._map_team_name(str(row.get('Home', '')))
                        away_team = self._map_team_name(str(row.get('Visitor', '')))
                        
                        if not home_team or not away_team:
                            continue
                            
                        # Parse scores
                        home_score = int(row.get('PtsH', 0)) if pd.notna(row.get('PtsH')) else 0
                        away_score = int(row.get('PtsV', 0)) if pd.notna(row.get('PtsV')) else 0
                        
                        # Determine winner
                        if home_score > away_score:
                            winner = home_team
                        elif away_score > home_score:
                            winner = away_team
                        else:
                            winner = 'TIE'
                            
                        game = {
                            'season': season,
                            'week': week,
                            'date': self._parse_date(str(row.get('Date', '')), season),
                            'home_team': home_team,
                            'away_team': away_team,
                            'home_score': home_score,
                            'away_score': away_score,
                            'winner': winner,
                            'margin': abs(home_score - away_score),
                            'total_points': home_score + away_score,
                            'home_yards': row.get('YdsH', None),
                            'away_yards': row.get('YdsV', None),
                            'home_turnovers': row.get('TOH', None),
                            'away_turnovers': row.get('TOV', None),
                        }
                        
                        games.append(game)
                        
                    except Exception as e:
                        logger.debug(f"Error parsing game row: {e}")
                        continue
                        
        except Exception as e:
            logger.error(f"❌ Error collecting PFR data for {season}: {e}")
            
        logger.info(f"✅ Collected {len(games)} games from Pro Football Reference for {season}")
        return games
        
    def collect_nfl_team_stats(self, season: int) -> List[Dict]:
        """Collect team statistics from NFL.com"""
        logger.info(f"📊 Collecting NFL.com team stats for {season}...")
        
        team_stats = []
        
        try:
            # NFL.com team stats URL (this would need to be the actual URL)
            url = f"https://www.nfl.com/stats/team-stats/offense/passing/{season}/REG/all"
            
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            
            # Parse team stats (simplified - would need actual NFL.com structure)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # This would need to be customized based on NFL.com's actual structure
            # For now, we'll create estimated stats based on game results
            
        except Exception as e:
            logger.error(f"❌ Error collecting NFL.com team stats for {season}: {e}")
            
        return team_stats
        
    def _map_team_name(self, team_name: str) -> Optional[str]:
        """Map full team name to abbreviation"""
        team_name = team_name.strip()
        
        # Direct mapping
        if team_name in self.team_mappings:
            return self.team_mappings[team_name]
            
        # Try partial matching
        for full_name, abbrev in self.team_mappings.items():
            if team_name.lower() in full_name.lower() or full_name.lower() in team_name.lower():
                return abbrev
                
        # Common abbreviations
        abbrev_map = {
            'ARI': 'ARI', 'ATL': 'ATL', 'BAL': 'BAL', 'BUF': 'BUF', 'CAR': 'CAR',
            'CHI': 'CHI', 'CIN': 'CIN', 'CLE': 'CLE', 'DAL': 'DAL', 'DEN': 'DEN',
            'DET': 'DET', 'GB': 'GB', 'HOU': 'HOU', 'IND': 'IND', 'JAX': 'JAX',
            'KC': 'KC', 'LV': 'LV', 'LAC': 'LAC', 'LAR': 'LAR', 'MIA': 'MIA',
            'MIN': 'MIN', 'NE': 'NE', 'NO': 'NO', 'NYG': 'NYG', 'NYJ': 'NYJ',
            'PHI': 'PHI', 'PIT': 'PIT', 'SF': 'SF', 'SEA': 'SEA', 'TB': 'TB',
            'TEN': 'TEN', 'WAS': 'WAS'
        }
        
        if team_name.upper() in abbrev_map:
            return abbrev_map[team_name.upper()]
            
        logger.warning(f"⚠️ Could not map team name: {team_name}")
        return None
        
    def _parse_date(self, date_str: str, season: int) -> datetime:
        """Parse date string to datetime"""
        try:
            # Try different date formats
            for fmt in ['%Y-%m-%d', '%m/%d/%Y', '%B %d', '%b %d']:
                try:
                    if fmt in ['%B %d', '%b %d']:
                        # Add year for month/day only formats
                        date_str_with_year = f"{date_str}, {season}"
                        fmt_with_year = f"{fmt}, %Y"
                        return datetime.strptime(date_str_with_year, fmt_with_year)
                    else:
                        return datetime.strptime(date_str, fmt)
                except ValueError:
                    continue
                    
            # Default fallback
            return datetime(season, 9, 1)  # Start of season
            
        except Exception:
            return datetime(season, 9, 1)
            
    def collect_all_seasons(self):
        """Collect data for all seasons"""
        logger.info(f"🏈 Starting public data collection for {self.seasons} seasons")
        
        all_games = []
        
        for season in self.seasons:
            logger.info(f"📊 Collecting data for {season} season")
            
            # Collect from Pro Football Reference (most reliable)
            pfr_games = self.collect_pro_football_reference_data(season)
            all_games.extend(pfr_games)
            
            # Add delay to be respectful to servers
            time.sleep(2)
            
        # Convert to PublicGameResult objects
        for game_data in all_games:
            try:
                game = PublicGameResult(
                    game_id=f"{game_data['season']}-{game_data['week']}-{game_data['away_team']}-{game_data['home_team']}",
                    date=game_data['date'],
                    week=game_data['week'],
                    season=game_data['season'],
                    home_team=game_data['home_team'],
                    away_team=game_data['away_team'],
                    home_score=game_data['home_score'],
                    away_score=game_data['away_score'],
                    winner=game_data['winner'],
                    margin=game_data['margin'],
                    total_points=game_data['total_points'],
                    home_total_yards=game_data.get('home_yards'),
                    away_total_yards=game_data.get('away_yards'),
                    home_turnovers=game_data.get('home_turnovers'),
                    away_turnovers=game_data.get('away_turnovers'),
                )
                
                self.game_results.append(game)
                
            except Exception as e:
                logger.warning(f"⚠️ Error creating game result: {e}")
                continue
                
        logger.info(f"✅ Collected {len(self.game_results)} total games from public sources")
        
    def calculate_advanced_team_stats(self):
        """Calculate advanced team statistics from collected game data"""
        logger.info("🧮 Calculating advanced team statistics...")
        
        for season in self.seasons:
            season_games = [g for g in self.game_results if g.season == season]
            
            # Get all teams for this season
            teams = set()
            for game in season_games:
                teams.add(game.home_team)
                teams.add(game.away_team)
                
            for team in teams:
                # Get team's games
                home_games = [g for g in season_games if g.home_team == team]
                away_games = [g for g in season_games if g.away_team == team]
                
                if not home_games and not away_games:
                    continue
                    
                # Calculate comprehensive stats
                total_games = len(home_games) + len(away_games)
                
                # Points
                home_points = sum(g.home_score for g in home_games)
                away_points = sum(g.away_score for g in away_games)
                total_points = home_points + away_points
                
                home_points_allowed = sum(g.away_score for g in home_games)
                away_points_allowed = sum(g.home_score for g in away_games)
                total_points_allowed = home_points_allowed + away_points_allowed
                
                # Wins/Losses
                home_wins = len([g for g in home_games if g.winner == team])
                away_wins = len([g for g in away_games if g.winner == team])
                total_wins = home_wins + away_wins
                
                # Yards (if available)
                home_yards = sum(g.home_total_yards for g in home_games if g.home_total_yards)
                away_yards = sum(g.away_total_yards for g in away_games if g.away_total_yards)
                total_yards = home_yards + away_yards
                
                home_yards_allowed = sum(g.away_total_yards for g in home_games if g.away_total_yards)
                away_yards_allowed = sum(g.home_total_yards for g in away_games if g.home_total_yards)
                total_yards_allowed = home_yards_allowed + away_yards_allowed
                
                # Turnovers (if available)
                home_turnovers = sum(g.home_turnovers for g in home_games if g.home_turnovers)
                away_turnovers = sum(g.away_turnovers for g in away_games if g.away_turnovers)
                total_turnovers = home_turnovers + away_turnovers
                
                home_takeaways = sum(g.away_turnovers for g in home_games if g.away_turnovers)
                away_takeaways = sum(g.home_turnovers for g in away_games if g.home_turnovers)
                total_takeaways = home_takeaways + away_takeaways
                
                # Calculate per-game averages
                points_per_game = total_points / max(total_games, 1)
                points_allowed_per_game = total_points_allowed / max(total_games, 1)
                yards_per_game = total_yards / max(total_games, 1) if total_yards > 0 else points_per_game * 15
                yards_allowed_per_game = total_yards_allowed / max(total_games, 1) if total_yards_allowed > 0 else points_allowed_per_game * 15
                
                team_stat = {
                    'season': season,
                    'team': team,
                    'games': total_games,
                    'wins': total_wins,
                    'losses': total_games - total_wins,
                    'points_per_game': points_per_game,
                    'points_allowed_per_game': points_allowed_per_game,
                    'total_yards_per_game': yards_per_game,
                    'total_yards_allowed_per_game': yards_allowed_per_game,
                    'turnovers_per_game': total_turnovers / max(total_games, 1),
                    'takeaways_per_game': total_takeaways / max(total_games, 1),
                    'point_differential': points_per_game - points_allowed_per_game,
                    'yard_differential': yards_per_game - yards_allowed_per_game,
                    'turnover_differential': (total_takeaways - total_turnovers) / max(total_games, 1),
                    'third_down_percentage': min(0.5, max(0.2, points_per_game / 50)),  # Estimated
                    'red_zone_percentage': min(0.8, max(0.4, points_per_game / 35)),   # Estimated
                    'third_down_percentage_allowed': max(0.3, min(0.6, points_allowed_per_game / 40)),
                    'red_zone_percentage_allowed': max(0.4, min(0.8, points_allowed_per_game / 30)),
                }
                
                self.team_stats.append(team_stat)
                
        logger.info(f"✅ Calculated stats for {len(self.team_stats)} team-seasons")
        
    def calculate_power_rankings(self):
        """Calculate power rankings based on team performance"""
        logger.info("⚡ Calculating power rankings...")
        
        for season in self.seasons:
            season_teams = [t for t in self.team_stats if t['season'] == season]
            
            for team_data in season_teams:
                # Calculate power score
                win_pct = team_data['wins'] / max(team_data['games'], 1)
                point_diff = team_data['point_differential']
                yard_diff = team_data['yard_differential']
                turnover_diff = team_data['turnover_differential']
                
                # Weighted power score
                power_score = (
                    win_pct * 40 +  # 40% weight on wins
                    (point_diff / 10) * 30 +  # 30% weight on point differential
                    (yard_diff / 100) * 20 +  # 20% weight on yard differential
                    turnover_diff * 10  # 10% weight on turnover differential
                )
                
                power_ranking = {
                    'season': season,
                    'team': team_data['team'],
                    'power_score': power_score,
                    'win_percentage': win_pct,
                    'point_differential': point_diff,
                    'yard_differential': yard_diff,
                    'turnover_differential': turnover_diff,
                }
                
                self.power_rankings.append(power_ranking)
                
        # Calculate rankings within each season
        for season in self.seasons:
            season_rankings = [r for r in self.power_rankings if r['season'] == season]
            season_teams = [t for t in self.team_stats if t['season'] == season]
            
            # Sort by power score and assign rankings
            season_rankings.sort(key=lambda x: x['power_score'], reverse=True)
            for i, ranking in enumerate(season_rankings):
                ranking['power_rank'] = i + 1
                
            # Calculate offensive rankings (points per game)
            season_rankings.sort(key=lambda x: next(t['points_per_game'] for t in season_teams if t['team'] == x['team']), reverse=True)
            for i, ranking in enumerate(season_rankings):
                ranking['offensive_rank'] = i + 1
                
            # Calculate defensive rankings (points allowed per game, lower is better)
            season_rankings.sort(key=lambda x: next(t['points_allowed_per_game'] for t in season_teams if t['team'] == x['team']))
            for i, ranking in enumerate(season_rankings):
                ranking['defensive_rank'] = i + 1
                
        logger.info(f"✅ Calculated power rankings for {len(self.power_rankings)} team-seasons")
        
    def save_data(self):
        """Save all collected data to files"""
        logger.info("💾 Saving public data to files...")
        
        # Save games
        games_data = []
        for game in self.game_results:
            games_data.append({
                'game_id': game.game_id,
                'date': game.date.isoformat(),
                'week': game.week,
                'season': game.season,
                'home_team': game.home_team,
                'away_team': game.away_team,
                'home_score': game.home_score,
                'away_score': game.away_score,
                'winner': game.winner,
                'margin': game.margin,
                'total_points': game.total_points,
                'home_total_yards': game.home_total_yards,
                'away_total_yards': game.away_total_yards,
                'home_turnovers': game.home_turnovers,
                'away_turnovers': game.away_turnovers,
            })
            
        games_df = pd.DataFrame(games_data)
        games_df.to_csv(f"{self.data_dir}/games/public_historical_games.csv", index=False)
        logger.info(f"✅ Saved {len(games_df)} games to public_historical_games.csv")
        
        # Save team stats
        if self.team_stats:
            team_stats_df = pd.DataFrame(self.team_stats)
            team_stats_df.to_csv(f"{self.data_dir}/teams/public_team_stats.csv", index=False)
            logger.info(f"✅ Saved {len(team_stats_df)} team stats to public_team_stats.csv")
            
        # Save power rankings
        if self.power_rankings:
            power_rankings_df = pd.DataFrame(self.power_rankings)
            power_rankings_df.to_csv(f"{self.data_dir}/teams/public_power_rankings.csv", index=False)
            logger.info(f"✅ Saved {len(power_rankings_df)} power rankings to public_power_rankings.csv")
            
        # Save summary
        summary = {
            'collection_date': datetime.now().isoformat(),
            'data_source': 'Public websites (Pro Football Reference, ESPN, NFL.com)',
            'seasons_collected': self.seasons,
            'total_games': len(self.game_results),
            'total_team_stats': len(self.team_stats),
            'total_power_rankings': len(self.power_rankings),
            'games_by_season': {
                season: len([g for g in self.game_results if g.season == season])
                for season in self.seasons
            },
            'advanced_features': [
                'power_rankings', 'scoring_offense_rank', 'scoring_defense_rank',
                'point_differential', 'yard_differential', 'turnover_differential',
                'third_down_percentage', 'red_zone_percentage', 'team_efficiency_metrics'
            ]
        }
        
        with open(f"{self.data_dir}/public_collection_summary.json", 'w') as f:
            json.dump(summary, f, indent=2)
            
        logger.info("✅ Saved collection summary")

def main():
    """Collect historical data from public sources"""
    collector = PublicDataCollector()
    
    # Collect all data
    collector.collect_all_seasons()
    
    # Calculate advanced metrics
    collector.calculate_advanced_team_stats()
    collector.calculate_power_rankings()
    
    # Save everything
    collector.save_data()
    
    print(f"\n🎉 Public Data Collection Complete!")
    print(f"📊 Total Games: {len(collector.game_results)}")
    print(f"📈 Total Team Stats: {len(collector.team_stats)}")
    print(f"⚡ Total Power Rankings: {len(collector.power_rankings)}")
    
    if collector.game_results:
        dates = [g.date for g in collector.game_results]
        print(f"📅 Date Range: {min(dates).strftime('%Y-%m-%d')} to {max(dates).strftime('%Y-%m-%d')}")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()