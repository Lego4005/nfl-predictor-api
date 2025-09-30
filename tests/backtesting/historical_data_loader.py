"""
Historical NFL Data Loader for Backtesting
Loads 2023-2024 season data for validation testing
"""

import json
import csv
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime
from dataclasses import dataclass, asdict


@dataclass
class NFLGame:
    """Historical NFL game with results"""
    game_id: str
    season: int
    week: int
    home_team: str
    away_team: str
    home_score: int
    away_score: int
    vegas_spread: float  # Negative = home favored
    vegas_total: float
    game_date: str
    weather_temp: Optional[float] = None
    weather_wind: Optional[float] = None
    weather_conditions: Optional[str] = None

    @property
    def winner(self) -> str:
        """Get winning team"""
        if self.home_score > self.away_score:
            return self.home_team
        elif self.away_score > self.home_score:
            return self.away_team
        return "TIE"

    @property
    def spread_result(self) -> str:
        """Get spread result (home perspective)"""
        actual_spread = self.home_score - self.away_score
        if actual_spread + self.vegas_spread > 0:
            return "HOME_COVERS"
        elif actual_spread + self.vegas_spread < 0:
            return "AWAY_COVERS"
        return "PUSH"

    @property
    def total_result(self) -> str:
        """Get over/under result"""
        actual_total = self.home_score + self.away_score
        if actual_total > self.vegas_total:
            return "OVER"
        elif actual_total < self.vegas_total:
            return "UNDER"
        return "PUSH"

    @property
    def home_ml_result(self) -> str:
        """Get moneyline result"""
        if self.home_score > self.away_score:
            return "HOME_WIN"
        elif self.away_score > self.home_score:
            return "AWAY_WIN"
        return "TIE"


class HistoricalDataLoader:
    """Load historical NFL game data for backtesting"""

    def __init__(self, fixtures_dir: str = None):
        if fixtures_dir:
            self.fixtures_dir = Path(fixtures_dir)
        else:
            self.fixtures_dir = Path(__file__).parent.parent / "fixtures"
        self.fixtures_dir.mkdir(parents=True, exist_ok=True)

    def load_season(self, year: int) -> List[NFLGame]:
        """
        Load all games for a season

        Args:
            year: Season year (2023 or 2024)

        Returns:
            List of NFLGame objects
        """
        csv_file = self.fixtures_dir / f"nfl_{year}_season.csv"
        json_file = self.fixtures_dir / f"nfl_{year}_season.json"

        # Try CSV first
        if csv_file.exists():
            return self._load_from_csv(csv_file, year)

        # Try JSON
        if json_file.exists():
            return self._load_from_json(json_file)

        raise FileNotFoundError(
            f"No historical data found for {year}. "
            f"Expected: {csv_file} or {json_file}"
        )

    def load_week(self, year: int, week: int) -> List[NFLGame]:
        """Load games for a specific week"""
        all_games = self.load_season(year)
        return [game for game in all_games if game.week == week]

    def load_weeks(self, year: int, start_week: int, end_week: int) -> List[NFLGame]:
        """Load games for a range of weeks"""
        all_games = self.load_season(year)
        return [
            game for game in all_games
            if start_week <= game.week <= end_week
        ]

    def _load_from_csv(self, csv_file: Path, year: int) -> List[NFLGame]:
        """Load games from CSV file"""
        games = []

        with open(csv_file, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                game = NFLGame(
                    game_id=row.get('game_id', f"{year}_{row['week']}_{row['away_team']}_{row['home_team']}"),
                    season=int(row.get('season', year)),
                    week=int(row['week']),
                    home_team=row['home_team'],
                    away_team=row['away_team'],
                    home_score=int(row['home_score']),
                    away_score=int(row['away_score']),
                    vegas_spread=float(row['vegas_spread']),
                    vegas_total=float(row['vegas_total']),
                    game_date=row['game_date'],
                    weather_temp=float(row['weather_temp']) if row.get('weather_temp') else None,
                    weather_wind=float(row['weather_wind']) if row.get('weather_wind') else None,
                    weather_conditions=row.get('weather_conditions')
                )
                games.append(game)

        return games

    def _load_from_json(self, json_file: Path) -> List[NFLGame]:
        """Load games from JSON file"""
        with open(json_file, 'r') as f:
            data = json.load(f)

        games = []
        for game_data in data:
            game = NFLGame(**game_data)
            games.append(game)

        return games

    def get_available_seasons(self) -> List[int]:
        """Get list of available seasons"""
        seasons = []
        for file in self.fixtures_dir.glob("nfl_*_season.*"):
            try:
                year = int(file.stem.split('_')[1])
                if year not in seasons:
                    seasons.append(year)
            except (IndexError, ValueError):
                continue
        return sorted(seasons)

    def create_sample_data(self, year: int = 2023, num_weeks: int = 18):
        """
        Create sample data for testing (until real data is available)

        Args:
            year: Season year
            num_weeks: Number of weeks to generate
        """
        import random
        from datetime import datetime, timedelta

        teams = [
            "KC", "SF", "BAL", "BUF", "DAL", "DET", "PHI", "MIA",
            "CLE", "LAR", "TB", "NO", "GB", "MIN", "JAX", "HOU",
            "CIN", "PIT", "SEA", "LAC", "IND", "LV", "NYJ", "DEN",
            "ATL", "CHI", "CAR", "NYG", "WAS", "TEN", "NE", "ARI"
        ]

        games = []
        game_id = 1

        start_date = datetime(year, 9, 7)  # First Thursday in September

        for week in range(1, num_weeks + 1):
            # Create matchups (ensuring each team plays once per week roughly)
            week_teams = teams.copy()
            random.shuffle(week_teams)

            num_games = len(week_teams) // 2
            game_date = start_date + timedelta(weeks=week-1)

            for i in range(num_games):
                home_team = week_teams[i * 2]
                away_team = week_teams[i * 2 + 1]

                # Generate realistic scores
                home_score = random.randint(10, 42)
                away_score = random.randint(10, 42)

                # Generate realistic spread (based on score difference)
                actual_diff = home_score - away_score
                vegas_spread = round(actual_diff + random.uniform(-7, 7), 1)

                # Generate realistic total
                actual_total = home_score + away_score
                vegas_total = round(actual_total + random.uniform(-10, 10), 1)

                game = NFLGame(
                    game_id=f"{year}_W{week}_G{game_id}",
                    season=year,
                    week=week,
                    home_team=home_team,
                    away_team=away_team,
                    home_score=home_score,
                    away_score=away_score,
                    vegas_spread=vegas_spread,
                    vegas_total=vegas_total,
                    game_date=game_date.strftime("%Y-%m-%d"),
                    weather_temp=random.uniform(30, 85) if random.random() > 0.3 else None,
                    weather_wind=random.uniform(0, 25) if random.random() > 0.5 else None,
                    weather_conditions=random.choice(["Clear", "Cloudy", "Rain", "Snow"]) if random.random() > 0.6 else None
                )
                games.append(game)
                game_id += 1

        # Save to both CSV and JSON
        self._save_to_csv(games, year)
        self._save_to_json(games, year)

        return games

    def _save_to_csv(self, games: List[NFLGame], year: int):
        """Save games to CSV file"""
        csv_file = self.fixtures_dir / f"nfl_{year}_season.csv"

        with open(csv_file, 'w', newline='') as f:
            if not games:
                return

            fieldnames = list(asdict(games[0]).keys())
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()

            for game in games:
                writer.writerow(asdict(game))

    def _save_to_json(self, games: List[NFLGame], year: int):
        """Save games to JSON file"""
        json_file = self.fixtures_dir / f"nfl_{year}_season.json"

        with open(json_file, 'w') as f:
            game_dicts = [asdict(game) for game in games]
            json.dump(game_dicts, f, indent=2)

    def get_season_stats(self, year: int) -> Dict:
        """Get summary statistics for a season"""
        games = self.load_season(year)

        total_games = len(games)
        home_wins = sum(1 for g in games if g.home_score > g.away_score)
        away_wins = sum(1 for g in games if g.away_score > g.home_score)
        ties = total_games - home_wins - away_wins

        home_covers = sum(1 for g in games if g.spread_result == "HOME_COVERS")
        away_covers = sum(1 for g in games if g.spread_result == "AWAY_COVERS")
        spread_pushes = sum(1 for g in games if g.spread_result == "PUSH")

        overs = sum(1 for g in games if g.total_result == "OVER")
        unders = sum(1 for g in games if g.total_result == "UNDER")
        total_pushes = sum(1 for g in games if g.total_result == "PUSH")

        avg_total = sum(g.home_score + g.away_score for g in games) / total_games

        return {
            "season": year,
            "total_games": total_games,
            "home_wins": home_wins,
            "away_wins": away_wins,
            "ties": ties,
            "home_win_pct": home_wins / total_games,
            "home_covers": home_covers,
            "away_covers": away_covers,
            "spread_pushes": spread_pushes,
            "home_cover_pct": home_covers / (total_games - spread_pushes) if (total_games - spread_pushes) > 0 else 0,
            "overs": overs,
            "unders": unders,
            "total_pushes": total_pushes,
            "over_pct": overs / (total_games - total_pushes) if (total_games - total_pushes) > 0 else 0,
            "avg_points_per_game": avg_total
        }


if __name__ == "__main__":
    # Example usage and testing
    loader = HistoricalDataLoader()

    # Create sample data for testing
    print("Creating sample 2023 season data...")
    loader.create_sample_data(2023, 18)

    print("\nCreating sample 2024 season data...")
    loader.create_sample_data(2024, 18)

    # Load and display stats
    print("\n" + "="*60)
    print("2023 Season Statistics")
    print("="*60)
    stats_2023 = loader.get_season_stats(2023)
    for key, value in stats_2023.items():
        print(f"{key}: {value}")

    print("\n" + "="*60)
    print("2024 Season Statistics")
    print("="*60)
    stats_2024 = loader.get_season_stats(2024)
    for key, value in stats_2024.items():
        print(f"{key}: {value}")

    # Test loading specific weeks
    print("\n" + "="*60)
    print("Week 1 Games (2023)")
    print("="*60)
    week1_games = loader.load_week(2023, 1)
    for game in week1_games[:5]:  # Show first 5
        print(f"{game.away_team} @ {game.home_team}: {game.away_score}-{game.home_score} "
              f"(Spread: {game.spread_result}, Total: {game.total_result})")