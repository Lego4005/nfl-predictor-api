"""
Simplified NFL Prediction Prompt for 20B LLM

Focuses on core predictions with clear JSON output format.
"""

from typing import List, Dict, Any


def build_simplified_prediction_prompt(
    expert_personality: str,
    game_data: Any,
    episodic_memories: List[Dict[str, Any]]
) -> tuple[str, str]:
    """
    Build a simplified prediction prompt optimized for 20B parameter models.

    Returns clear, parseable JSON with core predictions.
    """

    # Build memory context if available
    memory_context = ""
    if episodic_memories:
        memory_context = "\n\n🧠 YOUR PAST EXPERIENCES (USE THESE TO IMPROVE YOUR PREDICTION):\n"
        for i, mem in enumerate(episodic_memories[:3], 1):
            memory_context += f"\nMemory {i}:\n"
            memory_context += f"  Game: {mem.get('game_context', {}).get('teams', 'Unknown')}\n"
            memory_context += f"  Your prediction: {mem.get('prediction_summary', 'Unknown')}\n"
            memory_context += f"  What happened: {mem.get('actual_outcome', 'Unknown')}\n"
            memory_context += f"  Lesson learned: {mem.get('lessons_extracted', ['No lesson'])[0] if mem.get('lessons_extracted') else 'No lesson'}\n"
        memory_context += "\nApply these lessons to your current prediction!\n"

    system_message = f"""{expert_personality}

**🎯 YOUR TASK:**
Analyze the upcoming NFL game and make predictions. Think through your reasoning carefully, considering:
- Team statistics and recent performance
- Weather and game conditions
- Betting market signals
- Your past experiences (if provided)

**⚠️ REMEMBER:**
- You're competing against other experts - accuracy matters
- You have limited bankroll - confidence should match certainty
- Your performance determines your council influence
- Learn from your memories to improve predictions

**📋 OUTPUT FORMAT:**
Return ONLY valid JSON (no markdown, no extra text):

{{
  "reasoning": "Your 2-3 paragraph analysis explaining your thought process, key factors, and how you weighed them. Reference your memories if they influenced your decision.",
  "winner": "home" or "away",
  "confidence": 65,
  "spread": -3.5,
  "total": 47.5,
  "key_factors": ["Factor 1", "Factor 2", "Factor 3"]
}}

**FIELD REQUIREMENTS:**
- confidence: NUMBER from 0-100 (e.g., 65 means 65% confident, 50 is toss-up)
- spread: NUMBER from home team perspective (negative = home favored, e.g., -7.0 means home by 7)
- total: NUMBER representing COMBINED SCORE of BOTH teams (e.g., if you predict 28-24, total is 52). Typical NFL totals are 40-52 points.

**EXAMPLES:**
- High scoring game: {{"winner": "home", "confidence": 70, "spread": -6.5, "total": 51}}
- Defensive battle: {{"winner": "away", "confidence": 62, "spread": 3.0, "total": 41}}
- Close game: {{"winner": "home", "confidence": 55, "spread": -2.5, "total": 45}}"""

    user_message = f"""Analyze this NFL matchup and make your prediction:

**GAME:** {game_data.away_team} @ {game_data.home_team}
**Season:** {game_data.season}, Week {game_data.week}
**Date:** {game_data.game_date}

**HOME TEAM ({game_data.home_team}):**
- Record: {getattr(game_data.home_team_stats, 'wins', 0)}-{getattr(game_data.home_team_stats, 'losses', 0)}
- Points Per Game: {getattr(game_data.home_team_stats, 'points_per_game', 'N/A')}
- Points Allowed: {getattr(game_data.home_team_stats, 'points_allowed_per_game', 'N/A')}
- Recent Form: {getattr(game_data.home_team_stats, 'recent_form', 'N/A')}

**AWAY TEAM ({game_data.away_team}):**
- Record: {getattr(game_data.away_team_stats, 'wins', 0)}-{getattr(game_data.away_team_stats, 'losses', 0)}
- Points Per Game: {getattr(game_data.away_team_stats, 'points_per_game', 'N/A')}
- Points Allowed: {getattr(game_data.away_team_stats, 'points_allowed_per_game', 'N/A')}
- Recent Form: {getattr(game_data.away_team_stats, 'recent_form', 'N/A')}

**GAME CONDITIONS:**
- Venue: {getattr(game_data.venue_info, 'stadium_name', 'Unknown')}
- Weather: {getattr(game_data.weather_conditions, 'temperature', 'N/A')}°F, {getattr(game_data.weather_conditions, 'wind_speed', 'N/A')} mph wind
- Conditions: {getattr(game_data.weather_conditions, 'conditions', 'N/A')}

**BETTING LINES:**
- Spread: {getattr(game_data.public_betting, 'spread', 'N/A')} (negative = home favored)
- Total: {getattr(game_data.public_betting, 'total', 'N/A')}
- Public Betting: {getattr(game_data.public_betting, 'public_percentage', 'N/A')}% on favorite
{memory_context}

Now make your prediction. Think carefully, use your memories, and return valid JSON."""

    return system_message, user_message
