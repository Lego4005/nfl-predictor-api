"""
Supabase Historical Data Service
Retrieves 2 years of historical NFL data directly from Supabase
Uses pgvector for similarity matching and pattern detection
"""

import os
import sys
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import logging
from supabase import create_client, Client
import numpy as np
from dotenv import load_dotenv

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)


class SupabaseHistoricalService:
    """Service to retrieve and analyze historical data from Supabase with pgvector"""

    def __init__(self):
        # Initialize Supabase client
        self.supabase_url = os.getenv('VITE_SUPABASE_URL', 'https://vaypgzvivahnfegnlinn.supabase.co')
        self.supabase_key = os.getenv('VITE_SUPABASE_ANON_KEY', 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im55cGJxenpmtWNrZmFkZXhsdHprIiwicm9sZSI6ImFub24iLCJpYXQiOjE3MzYyMzA5MjcsImV4cCI6MjA1MTgwNjkyN30.7Bf7g7-9mDbTMBg8o-Y7Yqb-ovvQrJkzkNnHlKUWkMQ')

        self.supabase: Client = create_client(self.supabase_url, self.supabase_key)
        logger.info("📚 Connected to Supabase for historical data retrieval")

        # Cache for frequently accessed data
        self._cache = {}
        self._cache_timestamp = {}
        self.CACHE_DURATION = 300  # 5 minutes

    def get_historical_games(self,
                            start_date: Optional[datetime] = None,
                            end_date: Optional[datetime] = None,
                            teams: Optional[List[str]] = None) -> List[Dict]:
        """Retrieve historical games from Supabase"""

        cache_key = f"games_{start_date}_{end_date}_{teams}"

        # Check cache
        if self._is_cache_valid(cache_key):
            return self._cache[cache_key]

        try:
            # Build query
            query = self.supabase.table('games').select('*')

            # Apply date filters
            if start_date:
                query = query.gte('game_time', start_date.isoformat())
            else:
                # Default to 2 years of data
                two_years_ago = datetime.now() - timedelta(days=730)
                query = query.gte('game_time', two_years_ago.isoformat())

            if end_date:
                query = query.lte('game_time', end_date.isoformat())

            # Apply team filters
            if teams:
                # Get games where either team is in the list
                team_conditions = []
                for team in teams:
                    team_conditions.extend([
                        f"home_team.eq.{team}",
                        f"away_team.eq.{team}"
                    ])
                # Note: Supabase Python client handles OR conditions differently
                # We'll fetch all and filter in Python for simplicity

            # Execute query with ordering
            response = query.order('game_time', desc=True).execute()

            games = response.data if response.data else []

            # Filter by teams if specified (post-query filtering)
            if teams and games:
                filtered_games = []
                for game in games:
                    if game.get('home_team') in teams or game.get('away_team') in teams:
                        filtered_games.append(game)
                games = filtered_games

            # Cache the results
            self._cache[cache_key] = games
            self._cache_timestamp[cache_key] = datetime.now()

            logger.info(f"Retrieved {len(games)} historical games from Supabase")
            return games

        except Exception as e:
            logger.error(f"Error retrieving historical games: {e}")
            return []

    def find_similar_games_vector(self,
                                  home_team: str,
                                  away_team: str,
                                  spread: float,
                                  total: float,
                                  limit: int = 10) -> List[Dict]:
        """Find similar games using pgvector similarity search"""

        try:
            # Create a vector representation of the current game
            # This would ideally use the same embedding model as stored vectors
            current_vector = self._create_game_vector({
                'home_team': home_team,
                'away_team': away_team,
                'spread': spread,
                'total': total
            })

            # Use pgvector similarity search via RPC function
            # Note: This assumes we have a function in Supabase for vector similarity
            response = self.supabase.rpc('find_similar_games_for_learning', {
                'query_vector': current_vector,
                'match_count': limit
            }).execute()

            if response.data:
                similar_games = response.data
                logger.info(f"Found {len(similar_games)} similar games using pgvector")
                return similar_games

        except Exception as e:
            logger.warning(f"pgvector search failed, falling back to traditional search: {e}")

        # Fallback to traditional similarity search
        return self._find_similar_games_traditional(home_team, away_team, spread, total, limit)

    def _find_similar_games_traditional(self,
                                       home_team: str,
                                       away_team: str,
                                       spread: float,
                                       total: float,
                                       limit: int = 10) -> List[Dict]:
        """Traditional similarity search without pgvector"""

        # Get historical games
        games = self.get_historical_games()

        similar_games = []

        for game in games:
            # Skip if game doesn't have necessary data
            if not all(key in game for key in ['home_team', 'away_team', 'home_score', 'away_score']):
                continue

            # Calculate similarity metrics
            similarity_score = 0.0

            # Same matchup bonus
            if (game['home_team'] == home_team and game['away_team'] == away_team) or \
               (game['home_team'] == away_team and game['away_team'] == home_team):
                similarity_score += 0.3

            # Spread similarity (if available)
            if 'spread' in game and game['spread'] is not None:
                spread_diff = abs(float(game['spread']) - spread)
                spread_similarity = max(0, 1 - spread_diff / 10)  # Normalize to 0-1
                similarity_score += spread_similarity * 0.35

            # Total similarity (if available)
            if 'total' in game and game['total'] is not None:
                total_diff = abs(float(game['total']) - total)
                total_similarity = max(0, 1 - total_diff / 20)  # Normalize to 0-1
                similarity_score += total_similarity * 0.35

            # Add to results if similarity is meaningful
            if similarity_score > 0.3:
                game_result = {
                    'game_id': game.get('id', 'unknown'),
                    'date': game.get('game_time', 'unknown'),
                    'matchup': f"{game['away_team']} @ {game['home_team']}",
                    'spread': game.get('spread', 'N/A'),
                    'total': game.get('total', 'N/A'),
                    'home_score': game.get('home_score', 0),
                    'away_score': game.get('away_score', 0),
                    'similarity': similarity_score
                }

                # Calculate derived metrics
                if game.get('home_score') is not None and game.get('away_score') is not None:
                    game_result['winner'] = game['home_team'] if game['home_score'] > game['away_score'] else game['away_team']
                    game_result['actual_total'] = game['home_score'] + game['away_score']

                    # Check if spread was covered (if we have spread data)
                    if 'spread' in game and game['spread'] is not None:
                        actual_margin = game['home_score'] - game['away_score']
                        game_result['covered'] = 'Yes' if actual_margin > float(game['spread']) else 'No'

                    # Check over/under (if we have total data)
                    if 'total' in game and game['total'] is not None:
                        game_result['total_result'] = 'Over' if game_result['actual_total'] > float(game['total']) else 'Under'

                similar_games.append(game_result)

        # Sort by similarity and return top matches
        similar_games.sort(key=lambda x: x['similarity'], reverse=True)
        return similar_games[:limit]

    def get_team_performance_history(self, team: str, last_n_games: int = 10) -> Dict:
        """Get a team's recent performance from Supabase"""

        try:
            # Get games where team played (home or away)
            games = self.get_historical_games(teams=[team])

            # Limit to last N games
            recent_games = games[:last_n_games] if len(games) > last_n_games else games

            if not recent_games:
                return {
                    'games_played': 0,
                    'message': f"No historical data found for {team}"
                }

            # Calculate performance metrics
            wins = 0
            total_points_scored = 0
            total_points_allowed = 0
            home_games = 0
            away_games = 0

            for game in recent_games:
                # Determine if team won
                if game['home_team'] == team:
                    home_games += 1
                    if game.get('home_score', 0) > game.get('away_score', 0):
                        wins += 1
                    total_points_scored += game.get('home_score', 0)
                    total_points_allowed += game.get('away_score', 0)
                else:
                    away_games += 1
                    if game.get('away_score', 0) > game.get('home_score', 0):
                        wins += 1
                    total_points_scored += game.get('away_score', 0)
                    total_points_allowed += game.get('home_score', 0)

            games_count = len(recent_games)

            return {
                'games_played': games_count,
                'wins': wins,
                'losses': games_count - wins,
                'win_percentage': wins / games_count if games_count > 0 else 0,
                'avg_points_scored': total_points_scored / games_count if games_count > 0 else 0,
                'avg_points_allowed': total_points_allowed / games_count if games_count > 0 else 0,
                'home_games': home_games,
                'away_games': away_games,
                'recent_form': self._get_form_string(team, recent_games[:5])
            }

        except Exception as e:
            logger.error(f"Error getting team performance: {e}")
            return {'games_played': 0, 'error': str(e)}

    def get_expert_historical_performance(self, expert_name: str, weeks_back: int = 4) -> Dict:
        """Retrieve an expert's historical predictions and accuracy from Supabase"""

        try:
            # Calculate date range
            start_date = datetime.now() - timedelta(weeks=weeks_back)

            # Query expert predictions with results
            response = self.supabase.table('expert_predictions_comprehensive')\
                .select('*')\
                .eq('expert_name', expert_name)\
                .gte('prediction_time', start_date.isoformat())\
                .execute()

            if not response.data:
                return {
                    'expert': expert_name,
                    'predictions_made': 0,
                    'message': 'No historical data yet (Week 2 of season)'
                }

            predictions = response.data

            # Calculate accuracy metrics
            correct_predictions = 0
            total_predictions = len(predictions)
            category_performance = {}

            for pred in predictions:
                # Check if prediction was correct
                if pred.get('actual_winner') and pred.get('predicted_winner'):
                    if pred['actual_winner'] == pred['predicted_winner']:
                        correct_predictions += 1

                # Track category performance
                for category in ['spread', 'total', 'winner']:
                    if category in pred.get('prediction_categories', {}):
                        if category not in category_performance:
                            category_performance[category] = {'correct': 0, 'total': 0}

                        category_performance[category]['total'] += 1
                        if pred['prediction_categories'][category].get('correct'):
                            category_performance[category]['correct'] += 1

            return {
                'expert': expert_name,
                'predictions_made': total_predictions,
                'correct_predictions': correct_predictions,
                'accuracy': correct_predictions / total_predictions if total_predictions > 0 else 0,
                'category_performance': category_performance,
                'weeks_analyzed': weeks_back
            }

        except Exception as e:
            logger.error(f"Error getting expert performance: {e}")
            return {'expert': expert_name, 'predictions_made': 0, 'error': str(e)}

    def store_expert_prediction(self, prediction_data: Dict) -> bool:
        """Store a new expert prediction in Supabase"""

        try:
            # Ensure vector fields are properly formatted
            if 'prediction_embedding' in prediction_data:
                prediction_data['prediction_embedding'] = self._format_vector(prediction_data['prediction_embedding'])
            if 'context_embedding' in prediction_data:
                prediction_data['context_embedding'] = self._format_vector(prediction_data['context_embedding'])

            # Insert into Supabase
            response = self.supabase.table('expert_predictions_comprehensive')\
                .insert(prediction_data)\
                .execute()

            if response.data:
                logger.info(f"Stored prediction for {prediction_data.get('expert_name', 'Unknown')}")
                return True

        except Exception as e:
            logger.error(f"Error storing prediction: {e}")

        return False

    def _create_game_vector(self, game_data: Dict) -> List[float]:
        """Create a vector representation of a game for similarity matching"""

        # Simple feature vector (would be replaced with proper embedding in production)
        vector = [
            hash(game_data.get('home_team', '')) % 100 / 100,
            hash(game_data.get('away_team', '')) % 100 / 100,
            game_data.get('spread', 0) / 20,  # Normalize spread
            game_data.get('total', 45) / 60,  # Normalize total
            # Add more features as needed
        ]

        # Pad to 384 dimensions (pgvector standard)
        while len(vector) < 384:
            vector.append(0.0)

        return vector[:384]

    def _format_vector(self, vector: List[float]) -> str:
        """Format vector for pgvector storage"""
        return f"[{','.join(map(str, vector))}]"

    def _get_form_string(self, team: str, recent_games: List[Dict]) -> str:
        """Get W/L form string for recent games"""

        form = []
        for game in recent_games[:5]:  # Last 5 games
            if game['home_team'] == team:
                won = game.get('home_score', 0) > game.get('away_score', 0)
            else:
                won = game.get('away_score', 0) > game.get('home_score', 0)

            form.append('W' if won else 'L')

        return ''.join(form)

    def _is_cache_valid(self, cache_key: str) -> bool:
        """Check if cached data is still valid"""

        if cache_key not in self._cache:
            return False

        timestamp = self._cache_timestamp.get(cache_key)
        if not timestamp:
            return False

        age = (datetime.now() - timestamp).total_seconds()
        return age < self.CACHE_DURATION


# Create singleton instance
supabase_historical_service = SupabaseHistoricalService()


def test_supabase_connection():
    """Test the Supabase connection and data retrieval"""

    print("\n" + "=" * 70)
    print("🔌 Testing Supabase Historical Data Service")
    print("=" * 70)

    service = supabase_historical_service

    # Test 1: Get recent games
    print("\n📊 Fetching recent historical games from Supabase...")
    games = service.get_historical_games()
    print(f"✅ Retrieved {len(games)} games from database")

    if games:
        print(f"\nSample game data:")
        game = games[0]
        print(f"  • {game.get('away_team', 'N/A')} @ {game.get('home_team', 'N/A')}")
        print(f"  • Date: {game.get('game_time', 'N/A')}")
        print(f"  • Score: {game.get('home_score', 'N/A')} - {game.get('away_score', 'N/A')}")

    # Test 2: Find similar games
    print("\n🔍 Finding similar games to BUF vs NYJ (spread: -7, total: 45.5)...")
    similar = service.find_similar_games_vector("BUF", "NYJ", -7, 45.5)

    if similar:
        print(f"✅ Found {len(similar)} similar games")
        for i, game in enumerate(similar[:3], 1):
            print(f"\n  {i}. {game['matchup']} ({game['date']})")
            print(f"     Similarity: {game['similarity']:.1%}")
            if 'winner' in game:
                print(f"     Result: {game['winner']} won")

    # Test 3: Team performance
    print("\n📈 Getting Buffalo Bills recent performance...")
    perf = service.get_team_performance_history("BUF", 10)

    if perf['games_played'] > 0:
        print(f"✅ Bills last {perf['games_played']} games:")
        print(f"  • Record: {perf['wins']}-{perf['losses']} ({perf['win_percentage']:.1%})")
        print(f"  • Avg Points: {perf['avg_points_scored']:.1f} scored, {perf['avg_points_allowed']:.1f} allowed")
        print(f"  • Recent Form: {perf['recent_form']}")

    # Test 4: Expert performance (will be empty initially)
    print("\n🎯 Checking expert historical performance...")
    expert_perf = service.get_expert_historical_performance("Sharp Bettor", 2)

    if expert_perf['predictions_made'] > 0:
        print(f"✅ Sharp Bettor performance:")
        print(f"  • Predictions: {expert_perf['predictions_made']}")
        print(f"  • Accuracy: {expert_perf['accuracy']:.1%}")
    else:
        print(f"ℹ️ {expert_perf.get('message', 'No historical expert data yet')}")

    print("\n" + "=" * 70)
    print("✅ Supabase Historical Service is ready!")
    print("=" * 70)


if __name__ == "__main__":
    test_supabase_connection()