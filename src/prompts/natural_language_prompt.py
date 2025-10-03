"""
Natural Language NFL Prediction Prompt (No JSON constraints)

Uses simple delimited format for easy parsing without structured output overhead.
"""

from typing import List, Dict, Any


def build_natural_language_prompt(
    expert_personality: str,
    game_data: Any,
    episodic_memories: List[Dict[str, Any]]
) -> tuple[str, str]:
    """
    Build a natural language prediction prompt optimized for speed.

    Uses simple delimited format instead of JSON to avoid structured output overhead.
    """

    # Build memory context if available
    memory_context = ""
    if episodic_memories:
        memory_context = "\n\n🧠 YOUR PAST EXPERIENCES (Learn from these!):\n"
        for i, mem in enumerate(episodic_memories[:3], 1):
            # Extract memory data
            pred_data = mem.get('prediction_data', {})
            actual = mem.get('actual_outcome', {})
            lessons = mem.get('lessons_learned', [])
            context = mem.get('contextual_factors', [])

            # Get teams from context
            teams = {}
            for factor in context:
                if factor.get('factor') in ['home_team', 'away_team']:
                    teams[factor['factor']] = factor['value']

            game_desc = f"{teams.get('away_team', '?')} @ {teams.get('home_team', '?')}"

            # Check if prediction was correct
            pred_winner = pred_data.get('winner')
            actual_winner = actual.get('winner')
            was_correct = pred_winner == actual_winner

            memory_context += f"\n{i}. Game: {game_desc}"
            memory_context += f"\n   You predicted: {pred_winner} (confidence: {pred_data.get('confidence', 0):.0%})"
            memory_context += f"\n   Actual winner: {actual_winner} ({actual.get('away_score', '?')}-{actual.get('home_score', '?')})"
            memory_context += f"\n   Result: {'✅ CORRECT' if was_correct else '❌ WRONG'}"

            # Add lessons learned
            if lessons:
                memory_context += f"\n   Lessons learned:"
                for lesson in lessons[:2]:  # Top 2 lessons
                    memory_context += f"\n     • {lesson.get('lesson', 'N/A')}"

            memory_context += "\n"

        memory_context += "\n💡 Use these experiences to improve your prediction!\n"

    system_message = f"""{expert_personality}

You are competing against other experts. Your accuracy determines your influence.
Analyze the game carefully and make your prediction."""

    user_message = f"""Analyze this NFL matchup:

GAME: {game_data.away_team} @ {game_data.home_team}
Season {game_data.season}, Week {game_data.week}, {game_data.game_date}

HOME TEAM ({game_data.home_team}):
- Record: {getattr(game_data.home_team_stats, 'wins', 0)}-{getattr(game_data.home_team_stats, 'losses', 0)}
- Coach: {getattr(game_data.home_team_stats, 'coach', 'Unknown')}
- QB: {getattr(game_data.home_team_stats, 'qb', 'Unknown')}
- Rest: {getattr(game_data.home_team_stats, 'rest_days', 7)} days
- Points Per Game: {getattr(game_data.home_team_stats, 'points_per_game', 'N/A')}
- Points Allowed: {getattr(game_data.home_team_stats, 'points_allowed_per_game', 'N/A')}

AWAY TEAM ({game_data.away_team}):
- Record: {getattr(game_data.away_team_stats, 'wins', 0)}-{getattr(game_data.away_team_stats, 'losses', 0)}
- Coach: {getattr(game_data.away_team_stats, 'coach', 'Unknown')}
- QB: {getattr(game_data.away_team_stats, 'qb', 'Unknown')}
- Rest: {getattr(game_data.away_team_stats, 'rest_days', 7)} days
- Points Per Game: {getattr(game_data.away_team_stats, 'points_per_game', 'N/A')}
- Points Allowed: {getattr(game_data.away_team_stats, 'points_allowed_per_game', 'N/A')}

VENUE:
- Stadium: {getattr(game_data.venue_info, 'stadium_name', 'Unknown')}
- Surface: {getattr(game_data.venue_info, 'surface', 'grass')}
- Roof: {getattr(game_data.venue_info, 'roof', 'outdoor')}
- Division Game: {'Yes' if getattr(game_data.venue_info, 'is_division_game', False) else 'No'}

WEATHER:
- Temperature: {getattr(game_data.weather_conditions, 'temperature', 'N/A')}°F
- Wind: {getattr(game_data.weather_conditions, 'wind_speed', 'N/A')} mph
- Conditions: {getattr(game_data.weather_conditions, 'conditions', 'N/A')}

BETTING LINES:
- Spread: {getattr(game_data.public_betting, 'spread', 'N/A')} (negative = home favored)
- Total: {getattr(game_data.public_betting, 'total', 'N/A')}
{memory_context}

Provide your prediction in this EXACT format:

ANALYSIS: [Your 2-3 sentence reasoning]
WINNER: [home or away]
CONFIDENCE: [50-90]
SPREAD: [-14 to 14]
TOTAL: [35-65]

Example:
ANALYSIS: Chiefs have strong home advantage and better offensive stats. Ravens defense is solid but Chiefs offense should prevail.
WINNER: home
CONFIDENCE: 68
SPREAD: -6.5
TOTAL: 47"""

    return system_message, user_message


def parse_natural_language_response(response_text: str) -> Dict[str, Any]:
    """
    Parse natural language response - handles both formatted and reasoning-style outputs.
    """
    import re

    prediction = {
        'reasoning': response_text[:200],  # Default to first 200 chars
        'winner': 'home',
        'confidence': 0.55,
        'spread': 0.0,
        'total': 45.0
    }

    # Try formatted fields first
    analysis_match = re.search(r'ANALYSIS:\s*(.+?)(?=\n(?:WINNER|CONFIDENCE|SPREAD|TOTAL):|$)', response_text, re.IGNORECASE | re.DOTALL)
    if analysis_match:
        prediction['reasoning'] = analysis_match.group(1).strip()

    winner_match = re.search(r'WINNER:\s*(home|away)', response_text, re.IGNORECASE)
    if winner_match:
        prediction['winner'] = winner_match.group(1).lower()
    else:
        # Fallback: look for "Chiefs win" or similar
        if re.search(r'\b(Chiefs|home)\s+(win|wins|should win|likely)', response_text, re.IGNORECASE):
            prediction['winner'] = 'home'
        elif re.search(r'\b(Ravens|away)\s+(win|wins|should win|likely)', response_text, re.IGNORECASE):
            prediction['winner'] = 'away'

    confidence_match = re.search(r'CONFIDENCE:\s*(\d+)', response_text, re.IGNORECASE)
    if confidence_match:
        conf = int(confidence_match.group(1))
        prediction['confidence'] = max(0, min(100, conf)) / 100.0
    else:
        # Fallback: infer from language
        if re.search(r'\b(confident|strong|likely)\b', response_text, re.IGNORECASE):
            prediction['confidence'] = 0.68
        elif re.search(r'\b(moderate)\b', response_text, re.IGNORECASE):
            prediction['confidence'] = 0.60

    spread_match = re.search(r'SPREAD:\s*([-+]?\d+\.?\d*)', response_text, re.IGNORECASE)
    if spread_match:
        prediction['spread'] = float(spread_match.group(1))
    else:
        # Look for "by 3-6 points" or "-4 or -5"
        spread_range = re.search(r'by\s+(?:margin\s+of\s+)?(\d+)[-–](\d+)\s+points', response_text, re.IGNORECASE)
        if spread_range:
            avg = (int(spread_range.group(1)) + int(spread_range.group(2))) / 2
            prediction['spread'] = -avg if prediction['winner'] == 'home' else avg

    total_match = re.search(r'TOTAL:\s*(\d+\.?\d*)', response_text, re.IGNORECASE)
    if total_match:
        prediction['total'] = float(total_match.group(1))
    else:
        # Look for "48-50" or "near 48"
        total_range = re.search(r'(?:total|points).*?(\d{2})[-–](\d{2})', response_text, re.IGNORECASE)
        if total_range:
            prediction['total'] = (int(total_range.group(1)) + int(total_range.group(2))) / 2

    return prediction
