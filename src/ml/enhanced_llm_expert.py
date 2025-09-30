"""
Enhanced LLM Expert Agent with Real Data Integration

Extends LLMExpertAgent to fetch actual team stats, odds, and injuries
from ExpertDataAccessLayer before making predictions.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from typing import Dict, Any, Optional
from src.ml.llm_expert_agent import LLMExpertAgent
from src.services.expert_data_access_layer import ExpertDataAccessLayer
import json


class EnhancedLLMExpertAgent(LLMExpertAgent):
    """
    LLM Expert Agent that uses REAL data from APIs.

    Fetches actual team statistics, betting odds, and injury reports
    before generating predictions, giving the AI meaningful context.
    """

    def __init__(self, supabase_client, expert_config: Dict[str, Any], current_bankroll: float = 1000.0):
        super().__init__(supabase_client, expert_config, current_bankroll)
        self.data_layer = ExpertDataAccessLayer()
        print(f"✅ Enhanced LLM Expert initialized with real data access")

    def build_enhanced_prompt(self, game_data) -> str:
        """
        Build prompt with REAL game data from APIs.

        Args:
            game_data: GameData object from ExpertDataAccessLayer

        Returns:
            Enhanced prompt with real statistics
        """

        home_team = game_data.home_team
        away_team = game_data.away_team

        # Build personality description (same as parent)
        personality_desc = f"""
You are {self.expert_name}, an NFL prediction expert with the following personality traits:
- Optimism: {self.personality_traits.get('optimism', 0.5)}
- Market Trust: {self.personality_traits.get('market_trust', 0.5)}
- Chaos Comfort: {self.personality_traits.get('chaos_comfort', 0.5)}
- Value Seeking: {self.personality_traits.get('value_seeking', 0.5)}
- Risk Tolerance: {self.personality_traits.get('risk_tolerance', 0.5)}
- Analytics Trust: {self.personality_traits.get('analytics_trust', 0.5)}
- Confidence Level: {self.personality_traits.get('confidence_level', 0.5)}
- Contrarian Tendency: {self.personality_traits.get('contrarian_tendency', 0.5)}

Current Bankroll: ${self.current_bankroll}
"""

        # Build game info with REAL stats
        game_desc = f"""
Game Information:
- Matchup: {away_team} @ {home_team}
- Week: {game_data.week}, Season: {game_data.season}
- Venue: {game_data.venue}
- Kickoff: {game_data.kickoff_time or 'TBD'}
"""

        # Add real team statistics
        if game_data.team_stats and 'home_stats' in game_data.team_stats:
            home_stats = game_data.team_stats['home_stats']
            away_stats = game_data.team_stats['away_stats']

            game_desc += f"""
{home_team} (Home) Stats:
- Record: {home_stats.get('wins', 0)}-{home_stats.get('losses', 0)}
- Points Per Game: {home_stats.get('points_avg', 0):.1f}
- Points Allowed Per Game: {home_stats.get('points_allowed_avg', 0):.1f}
- Total Yards Per Game: {home_stats.get('total_yards_avg', 0):.1f}
- Passing Yards Per Game: {home_stats.get('passing_yards_avg', 0):.1f}
- Rushing Yards Per Game: {home_stats.get('rushing_yards_avg', 0):.1f}
- Turnover Differential: {home_stats.get('turnover_diff', 0):.1f}
- Third Down %: {home_stats.get('third_down_pct', 0):.1f}%
- Red Zone %: {home_stats.get('red_zone_pct', 0):.1f}%

{away_team} (Away) Stats:
- Record: {away_stats.get('wins', 0)}-{away_stats.get('losses', 0)}
- Points Per Game: {away_stats.get('points_avg', 0):.1f}
- Points Allowed Per Game: {away_stats.get('points_allowed_avg', 0):.1f}
- Total Yards Per Game: {away_stats.get('total_yards_avg', 0):.1f}
- Passing Yards Per Game: {away_stats.get('passing_yards_avg', 0):.1f}
- Rushing Yards Per Game: {away_stats.get('rushing_yards_avg', 0):.1f}
- Turnover Differential: {away_stats.get('turnover_diff', 0):.1f}
- Third Down %: {away_stats.get('third_down_pct', 0):.1f}%
- Red Zone %: {away_stats.get('red_zone_pct', 0):.1f}%
"""

        # Add betting odds if available
        if game_data.odds:
            game_desc += f"""
Betting Lines:
- Spread: {home_team} {game_data.odds.get('spread', {}).get('home', 'N/A')}
- Total (O/U): {game_data.odds.get('total', {}).get('line', 'N/A')}
- Moneyline: {home_team} {game_data.odds.get('moneyline', {}).get('home', 'N/A')}, {away_team} {game_data.odds.get('moneyline', {}).get('away', 'N/A')}
- Book: {game_data.odds.get('bookmaker', 'Unknown')}
"""

        # Add injury information if available
        if game_data.injuries and len(game_data.injuries) > 0:
            game_desc += f"""
Key Injuries:
"""
            for injury in game_data.injuries[:5]:  # Top 5 injuries
                game_desc += f"- {injury.get('team')}: {injury.get('player')} ({injury.get('position')}) - {injury.get('status')}\n"

        # Add weather if available
        if game_data.weather:
            game_desc += f"""
Weather Conditions:
- Temperature: {game_data.weather.get('temperature', 'N/A')}°F
- Wind: {game_data.weather.get('wind_speed', 'N/A')} mph
- Conditions: {game_data.weather.get('conditions', 'N/A')}
"""

        # Build full prompt
        prompt = f"""{personality_desc}

{game_desc}

Based on your personality traits and the REAL game data provided, make your prediction for this NFL game.

Consider:
1. Your personality traits (e.g., if you have high analytics_trust, rely more on stats)
2. Your risk tolerance when deciding bet size
3. Your contrarian tendency when evaluating popular picks
4. Your current bankroll when sizing your bet
5. The ACTUAL team performance data (not guesses!)

Output your prediction as a JSON object with this exact structure:
{{
    "winner": "TEAM_NAME",
    "confidence": 0.65,
    "bet_amount": 50.00,
    "reasoning": "Your detailed reasoning for this prediction...",
    "key_factors": [
        {{"factor": "defensive_strength", "value": 0.9, "description": "Specific stat difference"}},
        {{"factor": "offensive_efficiency", "value": 0.7, "description": "Specific stat difference"}},
        {{"factor": "home_advantage", "value": 0.6, "description": "Home field impact"}}
    ]
}}

Where:
- winner: The team you predict will win (exact team name: {home_team} or {away_team})
- confidence: Your confidence level (0.0 to 1.0)
- bet_amount: How much to bet from your ${self.current_bankroll} bankroll
- reasoning: Detailed explanation of your prediction (reference specific stats!)
- key_factors: Array of factor objects, each with:
  * factor: One of these standard categories:
    - "defensive_strength" (points allowed, defensive efficiency)
    - "offensive_efficiency" (scoring ability, yards per game)
    - "red_zone_efficiency" (red zone conversion rates)
    - "third_down_conversion" (third down success rates)
    - "turnover_differential" (turnover margin advantage)
    - "home_advantage" (home field impact)
    - "recent_momentum" (win/loss streaks, recent form)
    - "special_teams" (kicking, returns, field position)
  * value: Importance of this factor (0.0-1.0, where 1.0 = critically important, 0.5 = moderate, 0.3 = minor)
  * description: Brief explanation of the specific stat (e.g., "PHI allows 11 PPG less than DAL")

Respond ONLY with the JSON object, no other text."""

        return prompt

    async def predict_with_real_data(self, game_id: str, home_team: str = None, away_team: str = None,
                                    week: int = None, season: int = None) -> Optional[Dict[str, Any]]:
        """
        Generate prediction using REAL data from APIs.

        Args:
            game_id: Game identifier (UUID or formatted)
            home_team: Home team abbreviation (required if game_id is UUID)
            away_team: Away team abbreviation (required if game_id is UUID)
            week: Week number (required if game_id is UUID)
            season: Season year (required if game_id is UUID)

        Returns:
            Prediction dict with winner, confidence, bet_amount, reasoning, factors
        """

        print(f"\n{'='*80}")
        print(f"🎯 {self.expert_name} ({self.expert_id}) making prediction with REAL data")
        print(f"{'='*80}")

        try:
            # Step 1: Fetch REAL game data
            print(f"📊 Fetching real data for game {game_id}...")
            game_data = await self.data_layer.get_expert_data_view(
                expert_id=self.expert_id,
                game_id=game_id,
                home_team=home_team,
                away_team=away_team,
                week=week,
                season=season
            )

            if not game_data:
                print(f"❌ Could not fetch game data")
                return None

            print(f"✅ Data fetched: {game_data.away_team} @ {game_data.home_team}")

            # Debug: Check what data we got
            print(f"📊 Team stats available: {bool(game_data.team_stats)}")
            print(f"📊 Odds available: {bool(game_data.odds)}")
            if game_data.team_stats and 'home_stats' in game_data.team_stats:
                home_stats = game_data.team_stats['home_stats']
                print(f"📊 Home team PPG: {home_stats.get('points_avg', 'N/A')}")

            # Step 2: Build enhanced prompt with real stats
            prompt = self.build_enhanced_prompt(game_data)

            # Step 3: Generate prediction using LLM (call parent's method directly with our prompt)
            from claude_code_sdk import query
            import json

            response_text = ""
            async for message in query(prompt=prompt):
                if hasattr(message, 'content') and isinstance(message.content, list):
                    for block in message.content:
                        if hasattr(block, 'text'):
                            response_text += block.text

            print(f"📝 Claude response ({len(response_text)} chars): {response_text[:200]}...")

            # Parse JSON from response
            if "```json" in response_text:
                json_start = response_text.find("```json") + 7
                json_end = response_text.find("```", json_start)
                json_text = response_text[json_start:json_end].strip()
            elif "```" in response_text:
                json_start = response_text.find("```") + 3
                json_end = response_text.find("```", json_start)
                json_text = response_text[json_start:json_end].strip()
            else:
                json_text = response_text.strip()

            prediction = json.loads(json_text)

            if not prediction:
                return None

            # Add metadata
            prediction['game_id'] = game_id
            prediction['used_real_data'] = True

            return prediction

        except Exception as e:
            print(f"❌ Error in enhanced prediction: {e}")
            import traceback
            traceback.print_exc()
            return None

    async def predict(self, game_id: str, game_data: Dict[str, Any] = None, **kwargs) -> Optional[Dict[str, Any]]:
        """
        Override parent predict() to use real data.

        Args:
            game_id: Game identifier
            game_data: Dict with game details (home_team, away_team, week, season, venue)
            **kwargs: Additional parameters (home_team, away_team, week, season, venue)

        Returns:
            Prediction dict if successful, None otherwise
        """

        # Extract parameters from game_data if provided
        if game_data:
            home_team = kwargs.get('home_team') or game_data.get('home_team')
            away_team = kwargs.get('away_team') or game_data.get('away_team')
            week = kwargs.get('week') or game_data.get('week')
            season = kwargs.get('season') or game_data.get('season')
        else:
            home_team = kwargs.get('home_team')
            away_team = kwargs.get('away_team')
            week = kwargs.get('week')
            season = kwargs.get('season')

        # Use enhanced prediction with real data
        prediction = await self.predict_with_real_data(
            game_id, home_team, away_team, week, season
        )

        if not prediction:
            return None

        # Store prediction (same as parent)
        stored = await self.store_prediction(game_id, prediction)

        if stored:
            print(f"✅ Prediction with REAL data complete and stored!")
            return prediction
        else:
            print(f"⚠️ Prediction generated but storage failed")
            return prediction