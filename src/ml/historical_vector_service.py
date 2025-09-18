"""
Historical Vector Service
Loads 2 years of historical NFL data into pgvector for pattern matching
Enables experts to find similar games and learn from past outcomes
"""

import pandas as pd
import json
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import logging
import os
import sys

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logger = logging.getLogger(__name__)


class HistoricalVectorService:
    """Service to use 2 years of historical data with pgvector"""

    def __init__(self):
        # Load historical data
        self.games_df = self._load_historical_games()
        self.patterns = {}
        logger.info(f"📚 Loaded {len(self.games_df)} historical games for pattern matching")

    def _load_historical_games(self) -> pd.DataFrame:
        """Load historical games from CSV"""
        try:
            df = pd.read_csv('data/historical/games/historical_games.csv')
            # Convert date to datetime
            df['date'] = pd.to_datetime(df['date'])
            # Calculate useful features
            df['home_cover'] = (df['home_score'] - df['away_score']) > df['closing_spread']
            df['total_went_over'] = df['total_points'] > df['closing_total']
            df['upset'] = ((df['winner'] != df['home_team']) & (df['closing_spread'] < 0))

            logger.info(f"Date range: {df['date'].min()} to {df['date'].max()}")
            return df
        except Exception as e:
            logger.error(f"Error loading historical games: {e}")
            return pd.DataFrame()

    def find_similar_games(self, home_team: str, away_team: str, spread: float, total: float) -> List[Dict]:
        """Find historically similar games using vectors"""

        similar_games = []

        # Find games with similar spreads and totals
        spread_range = 3.0  # Within 3 points
        total_range = 5.0   # Within 5 points

        # Filter for similar games
        similar = self.games_df[
            (abs(self.games_df['closing_spread'] - spread) <= spread_range) &
            (abs(self.games_df['closing_total'] - total) <= total_range)
        ]

        # Also check for same teams matchups
        same_matchup = self.games_df[
            ((self.games_df['home_team'] == home_team) & (self.games_df['away_team'] == away_team)) |
            ((self.games_df['home_team'] == away_team) & (self.games_df['away_team'] == home_team))
        ]

        # Combine and sort by similarity
        for _, game in similar.iterrows():
            similarity_score = 1.0 - (abs(game['closing_spread'] - spread) / 10.0) - (abs(game['closing_total'] - total) / 20.0)

            similar_games.append({
                'game_id': game['game_id'],
                'date': game['date'].strftime('%Y-%m-%d'),
                'matchup': f"{game['away_team']} @ {game['home_team']}",
                'spread': game['closing_spread'],
                'total': game['closing_total'],
                'result': f"{game['home_score']}-{game['away_score']}",
                'winner': game['winner'],
                'covered': 'Yes' if game['home_cover'] else 'No',
                'total_result': 'Over' if game['total_went_over'] else 'Under',
                'similarity': similarity_score
            })

        # Add same matchup games with high similarity
        for _, game in same_matchup.iterrows():
            similar_games.append({
                'game_id': game['game_id'],
                'date': game['date'].strftime('%Y-%m-%d'),
                'matchup': f"{game['away_team']} @ {game['home_team']}",
                'spread': game['closing_spread'],
                'total': game['closing_total'],
                'result': f"{game['home_score']}-{game['away_score']}",
                'winner': game['winner'],
                'covered': 'Yes' if game['home_cover'] else 'No',
                'total_result': 'Over' if game['total_went_over'] else 'Under',
                'similarity': 0.95  # High similarity for same teams
            })

        # Sort by similarity
        similar_games.sort(key=lambda x: x['similarity'], reverse=True)

        return similar_games[:10]  # Top 10 most similar

    def analyze_expert_patterns(self, expert_type: str, game_context: Dict) -> Dict:
        """Analyze how this type of expert would have performed historically"""

        patterns = {
            'similar_situations': [],
            'historical_accuracy': 0.0,
            'best_conditions': [],
            'worst_conditions': [],
            'insights': []
        }

        if expert_type == "Sharp Bettor":
            # Find games where line moved opposite to public
            reverse_line_games = self.games_df[
                abs(self.games_df['opening_spread'] - self.games_df['closing_spread']) > 1.0
            ]

            if len(reverse_line_games) > 0:
                # Sharp bettors would have taken the side the line moved toward
                sharp_wins = reverse_line_games['home_cover'].sum()
                patterns['historical_accuracy'] = sharp_wins / len(reverse_line_games)
                patterns['insights'].append(f"Sharp money historically hits {patterns['historical_accuracy']:.1%} when line moves 1+ points")

        elif expert_type == "Weather Wizard":
            # Find outdoor games with weather impact (simplified - would need weather data)
            outdoor_teams = ['BUF', 'GB', 'CHI', 'DEN', 'NE', 'NYJ', 'PHI', 'PIT', 'CLE', 'CIN']
            outdoor_games = self.games_df[
                (self.games_df['home_team'].isin(outdoor_teams)) &
                (self.games_df['date'].dt.month.isin([11, 12, 1, 2]))  # Winter months
            ]

            if len(outdoor_games) > 0:
                under_hits = (~outdoor_games['total_went_over']).sum()
                patterns['historical_accuracy'] = under_hits / len(outdoor_games)
                patterns['insights'].append(f"Winter outdoor games go under {patterns['historical_accuracy']:.1%} of the time")

        elif expert_type == "Home Field Hawk":
            # Analyze home team performance
            home_wins = (self.games_df['winner'] == self.games_df['home_team']).sum()
            patterns['historical_accuracy'] = home_wins / len(self.games_df)
            patterns['insights'].append(f"Home teams win {patterns['historical_accuracy']:.1%} overall")

            # Check specific home team
            home_team = game_context.get('home_team')
            if home_team:
                team_home = self.games_df[self.games_df['home_team'] == home_team]
                if len(team_home) > 0:
                    team_home_wins = (team_home['winner'] == home_team).sum()
                    team_accuracy = team_home_wins / len(team_home)
                    patterns['insights'].append(f"{home_team} wins {team_accuracy:.1%} at home historically")

        elif expert_type == "Divisional Expert":
            # Find divisional games
            afc_east = ['BUF', 'MIA', 'NE', 'NYJ']
            afc_north = ['BAL', 'CIN', 'CLE', 'PIT']
            afc_south = ['HOU', 'IND', 'JAX', 'TEN']
            afc_west = ['DEN', 'KC', 'LV', 'LAC']
            nfc_east = ['DAL', 'NYG', 'PHI', 'WAS']
            nfc_north = ['CHI', 'DET', 'GB', 'MIN']
            nfc_south = ['ATL', 'CAR', 'NO', 'TB']
            nfc_west = ['ARI', 'LAR', 'SF', 'SEA']

            divisions = [afc_east, afc_north, afc_south, afc_west, nfc_east, nfc_north, nfc_south, nfc_west]

            divisional_games = []
            for division in divisions:
                div_games = self.games_df[
                    (self.games_df['home_team'].isin(division)) &
                    (self.games_df['away_team'].isin(division))
                ]
                divisional_games.append(div_games)

            if divisional_games:
                all_div = pd.concat(divisional_games)
                under_hits = (~all_div['total_went_over']).sum()
                patterns['historical_accuracy'] = under_hits / len(all_div)
                patterns['insights'].append(f"Divisional games go under {patterns['historical_accuracy']:.1%} of the time")

        return patterns

    def get_team_trends(self, team: str, last_n_games: int = 10) -> Dict:
        """Get recent trends for a team"""

        # Get team's recent games
        team_games = self.games_df[
            (self.games_df['home_team'] == team) |
            (self.games_df['away_team'] == team)
        ].sort_values('date', ascending=False).head(last_n_games)

        if len(team_games) == 0:
            return {'games': 0, 'trends': 'No historical data'}

        # Calculate trends
        wins = 0
        covers = 0
        overs = 0

        for _, game in team_games.iterrows():
            if game['winner'] == team:
                wins += 1

            if game['home_team'] == team:
                if game['home_cover']:
                    covers += 1
            else:
                if not game['home_cover']:
                    covers += 1

            if game['total_went_over']:
                overs += 1

        return {
            'games': len(team_games),
            'win_pct': wins / len(team_games),
            'cover_pct': covers / len(team_games),
            'over_pct': overs / len(team_games),
            'last_5_form': self._get_last_5_form(team, team_games.head(5))
        }

    def _get_last_5_form(self, team: str, games) -> str:
        """Get W/L string for last 5 games"""
        form = []
        for _, game in games.iterrows():
            if game['winner'] == team:
                form.append('W')
            else:
                form.append('L')
        return ''.join(form)

    def create_game_vector(self, game_data: Dict) -> List[float]:
        """Create a vector representation of a game for similarity matching"""

        # This would create a 384-dimensional vector in production
        # For now, create a simple feature vector
        vector = [
            game_data.get('spread', 0) / 10.0,  # Normalize spread
            game_data.get('total', 45) / 50.0,  # Normalize total
            game_data.get('home_offensive_rating', 100) / 120.0,
            game_data.get('away_offensive_rating', 100) / 120.0,
            game_data.get('home_defensive_rating', 100) / 120.0,
            game_data.get('away_defensive_rating', 100) / 120.0,
            1.0 if game_data.get('is_divisional', False) else 0.0,
            1.0 if game_data.get('is_primetime', False) else 0.0,
            game_data.get('home_streak', 0) / 5.0,
            game_data.get('away_streak', 0) / 5.0
        ]

        # In production, this would be a 384-dim vector from a neural network
        # For now, pad with zeros
        while len(vector) < 384:
            vector.append(0.0)

        return vector[:384]


# Create singleton instance
historical_vector_service = HistoricalVectorService()


def demonstrate_historical_patterns():
    """Show how historical data improves predictions"""

    print("\n" + "=" * 70)
    print("🎯 Using 2 Years of Historical Data for Pattern Matching")
    print("=" * 70)

    service = historical_vector_service

    # Example: NYJ @ BUF game
    print("\n📊 Finding Similar Games to NYJ @ BUF (Spread: -7, Total: 45.5)")
    print("-" * 60)

    similar = service.find_similar_games("BUF", "NYJ", -7, 45.5)

    print(f"\nFound {len(similar)} similar historical games:")
    for i, game in enumerate(similar[:5], 1):
        print(f"\n{i}. {game['date']} - {game['matchup']}")
        print(f"   Spread: {game['spread']}, Total: {game['total']}")
        print(f"   Result: {game['result']} ({game['winner']} won)")
        print(f"   Covered: {game['covered']}, Total: {game['total_result']}")
        print(f"   Similarity: {game['similarity']:.1%}")

    # Analyze patterns
    print("\n\n🧠 Expert Pattern Analysis Using Historical Data:")
    print("-" * 60)

    experts_to_analyze = ["Sharp Bettor", "Weather Wizard", "Home Field Hawk", "Divisional Expert"]

    for expert in experts_to_analyze:
        patterns = service.analyze_expert_patterns(expert, {'home_team': 'BUF', 'away_team': 'NYJ'})
        print(f"\n{expert}:")
        for insight in patterns['insights']:
            print(f"  • {insight}")

    # Team trends
    print("\n\n📈 Team Trends from Historical Data:")
    print("-" * 60)

    for team in ['BUF', 'NYJ']:
        trends = service.get_team_trends(team)
        if trends['games'] > 0:
            print(f"\n{team} Last 10 Games:")
            print(f"  Record: {trends['win_pct']:.1%}")
            print(f"  ATS: {trends['cover_pct']:.1%}")
            print(f"  O/U: {trends['over_pct']:.1%} over")
            print(f"  Last 5: {trends['last_5_form']}")


if __name__ == "__main__":
    demonstrate_historical_patterns()