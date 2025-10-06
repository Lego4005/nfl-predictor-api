"""
Natural Language Prompt Builder for NFL Predictions
Extracted from enhanced_conservative_analyzer.py for reusability
"""
import json
import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)


def build_natural_language_prompt(expert_personality: str, game_data, memories: List[Dict] = None):
    """
    Build system and user prompts for NFL prediction

    Args:
        expert_personality: The expert's personality description
        game_data: Game data object with team stats
        memories: Optional list of relevant memories

    Returns:
        tuple: (system_prompt, user_prompt)
    """
    system_prompt = f"""{expert_personality}

Provide a brief analysis (2-3 sentences) and make these predictions:
1. Winner (home/away)
2. Confidence (0-100)
3. Spread prediction (positive = home favored)
4. Total points prediction

Respond in JSON format:
{{
    "reasoning": "Your 2-3 sentence analysis",
    "winner": "home" or "away",
    "confidence": 65,
    "spread": -3.5,
    "total": 42.5
}}"""

    # Handle different game_data structures
    if hasattr(game_data, 'home_team_stats') and hasattr(game_data, 'away_team_stats'):
        # RealGameData structure
        home_stats = game_data.home_team_stats
        away_stats = game_data.away_team_stats
        home_record = f"{home_stats.wins}-{home_stats.losses}"
        away_record = f"{away_stats.wins}-{away_stats.losses}"
        home_ppg = home_stats.points_per_game
        home_papg = home_stats.points_allowed_per_game
        away_ppg = away_stats.points_per_game
        away_papg = away_stats.points_allowed_per_game
    elif hasattr(game_data, 'team_stats'):
        # Original structure
        home_stats = game_data.team_stats.get('home', {})
        away_stats = game_data.team_stats.get('away', {})
        home_record = f"{getattr(home_stats, 'wins', 0)}-{getattr(home_stats, 'losses', 0)}"
        away_record = f"{getattr(away_stats, 'wins', 0)}-{getattr(away_stats, 'losses', 0)}"
        home_ppg = getattr(home_stats, 'points_per_game', 'N/A')
        home_papg = getattr(home_stats, 'points_allowed_per_game', 'N/A')
        away_ppg = getattr(away_stats, 'points_per_game', 'N/A')
        away_papg = getattr(away_stats, 'points_allowed_per_game', 'N/A')
    else:
        # Fallback
        home_record = "N/A"
        away_record = "N/A"
        home_ppg = "N/A"
        home_papg = "N/A"
        away_ppg = "N/A"
        away_papg = "N/A"

    user_prompt = f"""Analyze this NFL matchup:

GAME: {game_data.away_team} @ {game_data.home_team}

TEAM STATS:
Home ({game_data.home_team}):
- Record: {home_record}
- Points/Game: {home_ppg}
- Points Allowed: {home_papg}

Away ({game_data.away_team}):
- Record: {away_record}
- Points/Game: {away_ppg}
- Points Allowed: {away_papg}

WEATHER: {getattr(game_data, 'weather', {}).get('conditions', 'Clear')}, {getattr(game_data, 'weather', {}).get('temperature', 70)}°F

BETTING LINE: {getattr(game_data, 'line_movement', {}).get('current_line', 'N/A')}"""

    if memories:
        user_prompt += f"\n\nRELEVANT MEMORIES ({len(memories)} found):"
        for i, memory in enumerate(memories[:2]):  # Include top 2 memories
            user_prompt += f"\n{i+1}. {memory.get('prediction_summary', 'Previous prediction')}"

    user_prompt += "\n\nProvide your analysis and predictions in JSON format."

    return system_prompt, user_prompt


def parse_natural_language_response(response_content: str) -> Dict[str, Any]:
    """
    Parse LLM response into structured format

    Args:
        response_content: Raw response content from LLM

    Returns:
        dict: Parsed prediction data
    """
    try:
        # Try to parse as JSON
        content = response_content.strip()

        # Handle potential markdown formatting
        if content.startswith('```json'):
            content = content.replace('```json', '').replace('```', '').strip()
        elif content.startswith('```'):
            content = content.replace('```', '').strip()

        parsed = json.loads(content)

        # Validate required fields
        required_fields = ['reasoning', 'winner', 'confidence', 'spread', 'total']
        for field in required_fields:
            if field not in parsed:
                raise ValueError(f"Missing required field: {field}")

        return {
            'reasoning': parsed['reasoning'],
            'winner': parsed['winner'],
            'confidence': max(0, min(100, int(parsed['confidence']))),
            'spread': float(parsed['spread']),
            'total': float(parsed['total']),
            'llm_powered': True
        }

    except (json.JSONDecodeError, ValueError, KeyError) as e:
        logger.warning(f"⚠️ Failed to parse LLM response: {e}")
        logger.debug(f"Raw response: {response_content[:200]}...")

        # Extract basic info from text if possible
        return _extract_from_text_response(response_content)


def _extract_from_text_response(response_content: str) -> Dict[str, Any]:
    """
    Fallback text extraction when JSON parsing fails

    Args:
        response_content: Raw response content

    Returns:
        dict: Basic prediction data extracted from text
    """
    # Simple text extraction fallback
    content_lower = response_content.lower()

    # Try to extract winner
    winner = 'home'
    if 'away' in content_lower and 'home' not in content_lower:
        winner = 'away'
    elif 'home' in content_lower and 'away' not in content_lower:
        winner = 'home'

    return {
        'reasoning': 'Text parsing fallback - could not parse structured response',
        'winner': winner,
        'confidence': 50,  # Default confidence
        'spread': 0.0,     # Default spread
        'total': 45.0,     # Default total
        'llm_powered': False
    }
