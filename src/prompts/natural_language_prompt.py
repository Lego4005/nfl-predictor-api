"""
Natural Language NFL Prediction Prompt (No JSON constraints)

Uses simple delimited format for easy parsing without structured output overhead.
Enhanced with comprehensive AI prompt generation for 30+ prediction categories.
"""

from typing import List, Dict, Any, Tuple
from datetime import datetime
import json


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


def parse_comprehensive_ai_response(response_text: str, expert_id: str, expert_config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Parse comprehensive AI response with robust JSON parsing and validation.

    This function handles different model output formats and implements fallback parsing
    for malformed responses. It validates all prediction categories and confidence levels
    using the ComprehensiveExpertPrediction structure.

    Args:
        response_text: Raw AI response text
        expert_id: Expert identifier for context
        expert_config: Expert configuration for fallback values

    Returns:
        Dictionary containing parsed and validated predictions
    """
    import re

    # Initialize comprehensive prediction structure
    parsed_prediction = {
        'analysis_text': '',
        'confidence_overall': 0.6,
        'key_factors': [],
        'reasoning': '',
        'memory_influence': '',
        'predictions': {
            # Core predictions
            'winner': 'home',
            'winner_confidence': 0.55,
            'spread': 0.0,
            'spread_confidence': 0.52,
            'total': 'over',
            'total_points': 45.5,
            'total_confidence': 0.50,
            'exact_score': '24-21',
            'margin': 3,

            # Quarter predictions
            'q1_home': 7, 'q1_away': 3,
            'q2_home': 10, 'q2_away': 7,
            'q3_home': 3, 'q3_away': 7,
            'q4_home': 4, 'q4_away': 4,
            'first_half_winner': 'home',
            'highest_scoring_quarter': 2,

            # Situational predictions
            'turnover_diff': 0,
            'red_zone_eff': 0.6,
            'third_down_conv': 0.4,
            'time_of_poss': 30.5,
            'total_sacks': 3,
            'total_penalties': 8,

            # Environmental impact
            'weather_impact': 0.3,
            'injury_impact': 0.4,
            'momentum_factor': 0.5,
            'special_teams': 0.5,
            'coaching_edge': 0.5
        },
        'parsing_success': False,
        'parsing_errors': []
    }

    try:
        # Step 1: Extract analysis text
        analysis_match = re.search(r'ANALYSIS:\s*(.+?)(?=\n(?:CORE PREDICTIONS|WINNER|$))', response_text, re.IGNORECASE | re.DOTALL)
        if analysis_match:
            parsed_prediction['analysis_text'] = analysis_match.group(1).strip()
            parsed_prediction['reasoning'] = parsed_prediction['analysis_text']
        else:
            # Fallback: use first paragraph as analysis
            first_paragraph = response_text.split('\n\n')[0][:300]
            parsed_prediction['analysis_text'] = first_paragraph
            parsed_prediction['reasoning'] = first_paragraph
            parsed_prediction['parsing_errors'].append("No ANALYSIS section found")

        # Step 2: Parse core predictions
        _parse_core_predictions(response_text, parsed_prediction)

        # Step 3: Parse quarter predictions
        _parse_quarter_predictions(response_text, parsed_prediction)

        # Step 4: Parse situational predictions
        _parse_situational_predictions(response_text, parsed_prediction)

        # Step 5: Parse environmental predictions
        _parse_environmental_predictions(response_text, parsed_prediction)

        # Step 6: Parse meta information
        _parse_meta_information(response_text, parsed_prediction)

        # Step 7: Validate all predictions
        validation_errors = _validate_parsed_predictions(parsed_prediction)
        parsed_prediction['parsing_errors'].extend(validation_errors)

        # Mark as successful if no critical errors
        parsed_prediction['parsing_success'] = len([e for e in parsed_prediction['parsing_errors'] if 'critical' in e.lower()]) == 0

        logger.info(f"✅ Parsed comprehensive response for {expert_config.get('name', expert_id)}: "
                   f"{len(parsed_prediction['parsing_errors'])} warnings")

        return parsed_prediction

    except Exception as e:
        logger.error(f"❌ Critical parsing error for {expert_config.get('name', expert_id)}: {e}")
        parsed_prediction['parsing_errors'].append(f"Critical parsing error: {str(e)}")
        parsed_prediction['parsing_success'] = False
        return parsed_prediction


def _parse_core_predictions(response_text: str, parsed_prediction: Dict[str, Any]) -> None:
    """Parse core game predictions (winner, spread, total, etc.)"""

    # Winner prediction
    winner_match = re.search(r'WINNER:\s*(home|away)', response_text, re.IGNORECASE)
    if winner_match:
        parsed_prediction['predictions']['winner'] = winner_match.group(1).lower()

    # Winner confidence
    winner_conf_match = re.search(r'WINNER_CONFIDENCE:\s*(\d+)', response_text, re.IGNORECASE)
    if winner_conf_match:
        conf = int(winner_conf_match.group(1))
        parsed_prediction['predictions']['winner_confidence'] = max(0.5, min(0.95, conf / 100.0))

    # Spread prediction
    spread_match = re.search(r'SPREAD:\s*([-+]?\d+\.?\d*)', response_text, re.IGNORECASE)
    if spread_match:
        parsed_prediction['predictions']['spread'] = float(spread_match.group(1))

    # Spread confidence
    spread_conf_match = re.search(r'SPREAD_CONFIDENCE:\s*(\d+)', response_text, re.IGNORECASE)
    if spread_conf_match:
        conf = int(spread_conf_match.group(1))
        parsed_prediction['predictions']['spread_confidence'] = max(0.5, min(0.95, conf / 100.0))

    # Total prediction
    total_match = re.search(r'TOTAL:\s*(over|under)', response_text, re.IGNORECASE)
    if total_match:
        parsed_prediction['predictions']['total'] = total_match.group(1).lower()

    # Total points
    total_points_match = re.search(r'TOTAL_POINTS:\s*(\d+\.?\d*)', response_text, re.IGNORECASE)
    if total_points_match:
        parsed_prediction['predictions']['total_points'] = float(total_points_match.group(1))

    # Total confidence
    total_conf_match = re.search(r'TOTAL_CONFIDENCE:\s*(\d+)', response_text, re.IGNORECASE)
    if total_conf_match:
        conf = int(total_conf_match.group(1))
        parsed_prediction['predictions']['total_confidence'] = max(0.5, min(0.95, conf / 100.0))

    # Exact score
    exact_score_match = re.search(r'EXACT_SCORE:\s*(\d+[-–]\d+)', response_text, re.IGNORECASE)
    if exact_score_match:
        parsed_prediction['predictions']['exact_score'] = exact_score_match.group(1).replace('–', '-')

    # Margin
    margin_match = re.search(r'MARGIN:\s*(\d+)', response_text, re.IGNORECASE)
    if margin_match:
        parsed_prediction['predictions']['margin'] = int(margin_match.group(1))


def _parse_quarter_predictions(response_text: str, parsed_prediction: Dict[str, Any]) -> None:
    """Parse quarter-by-quarter predictions"""

    # Quarter scores
    quarter_patterns = {
        'q1_home': r'Q1_HOME:\s*(\d+)',
        'q1_away': r'Q1_AWAY:\s*(\d+)',
        'q2_home': r'Q2_HOME:\s*(\d+)',
        'q2_away': r'Q2_AWAY:\s*(\d+)',
        'q3_home': r'Q3_HOME:\s*(\d+)',
        'q3_away': r'Q3_AWAY:\s*(\d+)',
        'q4_home': r'Q4_HOME:\s*(\d+)',
        'q4_away': r'Q4_AWAY:\s*(\d+)'
    }

    for key, pattern in quarter_patterns.items():
        match = re.search(pattern, response_text, re.IGNORECASE)
        if match:
            parsed_prediction['predictions'][key] = int(match.group(1))

    # First half winner
    first_half_match = re.search(r'FIRST_HALF_WINNER:\s*(home|away|tie)', response_text, re.IGNORECASE)
    if first_half_match:
        parsed_prediction['predictions']['first_half_winner'] = first_half_match.group(1).lower()

    # Highest scoring quarter
    highest_q_match = re.search(r'HIGHEST_SCORING_QUARTER:\s*([1-4])', response_text, re.IGNORECASE)
    if highest_q_match:
        parsed_prediction['predictions']['highest_scoring_quarter'] = int(highest_q_match.group(1))


def _parse_situational_predictions(response_text: str, parsed_prediction: Dict[str, Any]) -> None:
    """Parse situational predictions (turnovers, red zone, etc.)"""

    # Turnover differential
    turnover_match = re.search(r'TURNOVER_DIFF:\s*([-+]?\d+)', response_text, re.IGNORECASE)
    if turnover_match:
        parsed_prediction['predictions']['turnover_diff'] = int(turnover_match.group(1))

    # Red zone efficiency
    red_zone_match = re.search(r'RED_ZONE_EFF:\s*(\d*\.?\d+)', response_text, re.IGNORECASE)
    if red_zone_match:
        parsed_prediction['predictions']['red_zone_eff'] = float(red_zone_match.group(1))

    # Third down conversion
    third_down_match = re.search(r'THIRD_DOWN_CONV:\s*(\d*\.?\d+)', response_text, re.IGNORECASE)
    if third_down_match:
        parsed_prediction['predictions']['third_down_conv'] = float(third_down_match.group(1))

    # Time of possession
    top_match = re.search(r'TIME_OF_POSS:\s*(\d+\.?\d*)', response_text, re.IGNORECASE)
    if top_match:
        parsed_prediction['predictions']['time_of_poss'] = float(top_match.group(1))

    # Total sacks
    sacks_match = re.search(r'TOTAL_SACKS:\s*(\d+)', response_text, re.IGNORECASE)
    if sacks_match:
        parsed_prediction['predictions']['total_sacks'] = int(sacks_match.group(1))

    # Total penalties
    penalties_match = re.search(r'TOTAL_PENALTIES:\s*(\d+)', response_text, re.IGNORECASE)
    if penalties_match:
        parsed_prediction['predictions']['total_penalties'] = int(penalties_match.group(1))


def _parse_environmental_predictions(response_text: str, parsed_prediction: Dict[str, Any]) -> None:
    """Parse environmental impact predictions"""

    environmental_patterns = {
        'weather_impact': r'WEATHER_IMPACT:\s*(\d*\.?\d+)',
        'injury_impact': r'INJURY_IMPACT:\s*(\d*\.?\d+)',
        'momentum_factor': r'MOMENTUM_FACTOR:\s*(\d*\.?\d+)',
        'special_teams': r'SPECIAL_TEAMS:\s*(\d*\.?\d+)',
        'coaching_edge': r'COACHING_EDGE:\s*(\d*\.?\d+)'
    }

    for key, pattern in environmental_patterns.items():
        match = re.search(pattern, response_text, re.IGNORECASE)
        if match:
            value = float(match.group(1))
            parsed_prediction['predictions'][key] = max(0.0, min(1.0, value))


def _parse_meta_information(response_text: str, parsed_prediction: Dict[str, Any]) -> None:
    """Parse meta information (key factors, memory influence, overall confidence)"""

    # Key factors
    key_factors_match = re.search(r'KEY_FACTORS:\s*\[([^\]]+)\]', response_text, re.IGNORECASE)
    if key_factors_match:
        factors_text = key_factors_match.group(1)
        # Split by comma and clean up
        factors = [f.strip().strip('"\'') for f in factors_text.split(',')]
        parsed_prediction['key_factors'] = factors[:5]  # Limit to 5 factors
    else:
        # Fallback: look for factors in a different format
        factors_match = re.search(r'KEY_FACTORS:\s*(.+?)(?=\n[A-Z_]+:|$)', response_text, re.IGNORECASE | re.DOTALL)
        if factors_match:
            factors_text = factors_match.group(1).strip()
            # Try to extract factors from text
            factors = [f.strip() for f in factors_text.replace('[', '').replace(']', '').split(',')]
            parsed_prediction['key_factors'] = factors[:5]

    # Memory influence
    memory_match = re.search(r'MEMORY_INFLUENCE:\s*(.+?)(?=\n[A-Z_]+:|$)', response_text, re.IGNORECASE | re.DOTALL)
    if memory_match:
        parsed_prediction['memory_influence'] = memory_match.group(1).strip()

    # Overall confidence
    overall_conf_match = re.search(r'CONFIDENCE_OVERALL:\s*(\d+)', response_text, re.IGNORECASE)
    if overall_conf_match:
        conf = int(overall_conf_match.group(1))
        parsed_prediction['confidence_overall'] = max(0.5, min(0.95, conf / 100.0))


def _validate_parsed_predictions(parsed_prediction: Dict[str, Any]) -> List[str]:
    """Validate parsed predictions and return list of validation errors"""

    errors = []
    predictions = parsed_prediction['predictions']

    # Validate core predictions
    if predictions['winner'] not in ['home', 'away']:
        errors.append(f"Invalid winner prediction: {predictions['winner']}")

    if not (0.5 <= predictions['winner_confidence'] <= 0.95):
        errors.append(f"Winner confidence out of range: {predictions['winner_confidence']}")

    if predictions['total'] not in ['over', 'under']:
        errors.append(f"Invalid total prediction: {predictions['total']}")

    if not (30.0 <= predictions['total_points'] <= 70.0):
        errors.append(f"Total points out of reasonable range: {predictions['total_points']}")

    # Validate quarter scores
    for quarter in ['q1', 'q2', 'q3', 'q4']:
        home_key = f'{quarter}_home'
        away_key = f'{quarter}_away'

        if home_key in predictions and not (0 <= predictions[home_key] <= 35):
            errors.append(f"Quarter score out of range: {home_key}={predictions[home_key]}")

        if away_key in predictions and not (0 <= predictions[away_key] <= 35):
            errors.append(f"Quarter score out of range: {away_key}={predictions[away_key]}")

    # Validate situational predictions
    if 'turnover_diff' in predictions and not (-5 <= predictions['turnover_diff'] <= 5):
        errors.append(f"Turnover differential out of range: {predictions['turnover_diff']}")

    if 'red_zone_eff' in predictions and not (0.0 <= predictions['red_zone_eff'] <= 1.0):
        errors.append(f"Red zone efficiency out of range: {predictions['red_zone_eff']}")

    # Validate environmental factors
    environmental_keys = ['weather_impact', 'injury_impact', 'momentum_factor', 'special_teams', 'coaching_edge']
    for key in environmental_keys:
        if key in predictions and not (0.0 <= predictions[key] <= 1.0):
            errors.append(f"Environmental factor out of range: {key}={predictions[key]}")

    # Validate overall confidence
    if not (0.5 <= parsed_prediction['confidence_overall'] <= 0.95):
        errors.append(f"Overall confidence out of range: {parsed_prediction['confidence_overall']}")

    return errors


def create_fallback_parsed_response(expert_id: str, expert_config: Dict[str, Any], error_msg: str = None) -> Dict[str, Any]:
    """
    Create a fallback parsed response when parsing fails completely.

    This ensures the system can continue operating even when AI responses
    are completely unparseable.
    """

    expert_name = expert_config.get('name', expert_id)
    error_context = f" Error: {error_msg}" if error_msg else ""

    return {
        'analysis_text': f"Fallback analysis for {expert_name}.{error_context}",
        'confidence_overall': 0.5,
        'key_factors': ['Fallback analysis', 'Parsing failed'],
        'reasoning': f"Using fallback prediction for {expert_name} due to parsing issues",
        'memory_influence': 'Unable to process due to parsing errors',
        'predictions': {
            # Safe default predictions
            'winner': 'home',
            'winner_confidence': 0.55,
            'spread': 0.0,
            'spread_confidence': 0.52,
            'total': 'over',
            'total_points': 45.0,
            'total_confidence': 0.50,
            'exact_score': '24-21',
            'margin': 3,

            # Quarter predictions
            'q1_home': 7, 'q1_away': 3,
            'q2_home': 10, 'q2_away': 7,
            'q3_home': 3, 'q3_away': 7,
            'q4_home': 4, 'q4_away': 4,
            'first_half_winner': 'home',
            'highest_scoring_quarter': 2,

            # Situational predictions
            'turnover_diff': 0,
            'red_zone_eff': 0.6,
            'third_down_conv': 0.4,
            'time_of_poss': 30.0,
            'total_sacks': 3,
            'total_penalties': 8,

            # Environmental impact
            'weather_impact': 0.3,
            'injury_impact': 0.4,
            'momentum_factor': 0.5,
            'special_teams': 0.5,
            'coaching_edge': 0.5
        },
        'parsing_success': False,
        'parsing_errors': [f'Complete parsing failure: {error_msg}' if error_msg else 'Complete parsing failure']
    }


def build_comprehensive_ai_prompt(
    expert_id: str,
    expert_config: Dict[str, Any],
    memories: List[Dict[str, Any]],
    game_context: Any,
    personality_profile: Any = None
) -> Tuple[str, str]:
    """
    Build comprehensive AI prompt for expert analysis with all 30+ prediction categories.

    This function creates expert-specific system prompts using PersonalityProfile traits
    and builds dynamic user prompts that include game context and retrieved memories.

    Args:
        expert_id: Expert identifier (e.g., 'conservative_analyzer')
        expert_config: Expert configuration from model mapping
        memories: Retrieved episodic memories with similarity scores
        game_context: GameContext object with all game data
        personality_profile: PersonalityProfile object (optional)

    Returns:
        Tuple of (system_prompt, user_prompt) for AI model
    """

    # Build expert-specific system prompt using personality traits
    system_prompt = _build_expert_system_prompt(expert_id, expert_config, personality_profile)

    # Build dynamic user prompt with game context and memories
    user_prompt = _build_comprehensive_user_prompt(expert_config, memories, game_context)

    return system_prompt, user_prompt


def _build_expert_system_prompt(expert_id: str, expert_config: Dict[str, Any], personality_profile: Any = None) -> str:
    """
    Create expert-specific system prompts using PersonalityProfile traits.

    This builds prompts that reflect the expert's personality, analytical focus,
    and decision-making style for consistent AI behavior.
    """

    expert_name = expert_config['name']
    personality = expert_config['personality']
    specialty = expert_config['specialty']

    # Base system prompt with expert identity
    system_prompt = f"""You are {expert_name}, a specialized NFL prediction expert with a unique analytical approach.

CORE IDENTITY:
- Expert ID: {expert_id}
- Personality: {personality}
- Specialty: {specialty}

ANALYTICAL APPROACH:"""

    # Add personality-specific traits if available
    if personality_profile and hasattr(personality_profile, 'traits'):
        system_prompt += "\n- Personality Traits:"

        # Extract key personality dimensions
        for trait_name, trait in personality_profile.traits.items():
            if hasattr(trait, 'value') and hasattr(trait, 'influence_weight'):
                if trait.influence_weight > 0.6:  # Only include influential traits
                    trait_desc = _get_trait_description(trait_name, trait.value)
                    system_prompt += f"\n  • {trait_name}: {trait_desc} (influence: {trait.influence_weight:.1f})"

    # Add expert-specific analytical focus based on expert_id
    analytical_focus = _get_expert_analytical_focus(expert_id)
    system_prompt += f"\n\nANALYTICAL FOCUS:\n{analytical_focus}"

    # Add prediction methodology
    system_prompt += f"""

PREDICTION METHODOLOGY:
You analyze NFL games through your unique lens and provide comprehensive predictions across multiple categories:

1. CORE GAME OUTCOMES: Winner, spread, total points, moneyline, exact score, margin
2. QUARTER-BY-QUARTER: Q1-Q4 scoring, first half winner, highest scoring quarter
3. PLAYER PROPS: QB stats, RB stats, WR stats (yards, TDs, attempts, etc.)
4. SITUATIONAL: Turnovers, red zone efficiency, 3rd down conversion, time of possession
5. ENVIRONMENTAL: Weather impact, injury impact, momentum, special teams, coaching

MEMORY INTEGRATION:
- Use your past experiences (episodic memories) to inform current predictions
- Learn from similar game situations and outcomes
- Apply lessons learned from previous successes and failures
- Weight memories based on similarity and recency

RESPONSE REQUIREMENTS:
- Provide structured analysis with clear reasoning
- Include confidence levels for all predictions (0-100 scale)
- Explain key factors driving your analysis
- Reference relevant memories when applicable
- Maintain consistency with your personality and specialty"""

    return system_prompt


def _build_comprehensive_user_prompt(expert_config: Dict[str, Any], memories: List[Dict[str, Any]], game_context: Any) -> str:
    """
    Build dynamic user prompts that include game context and retrieved memories.

    This creates comprehensive prompts with all available game data, betting context,
    and formatted memory context to help AI understand relevant past experiences.
    """

    expert_name = expert_config['name']

    # Start with game context
    user_prompt = f"""Analyze this NFL matchup using your expertise as {expert_name}:

GAME MATCHUP:
{game_context.away_team} @ {game_context.home_team}
Season: {game_context.season}, Week: {game_context.week}
Date: {game_context.game_date}
Game ID: {game_context.game_id}

GAME CONTEXT:
- Divisional Game: {'Yes' if game_context.is_divisional else 'No'}
- Primetime Game: {'Yes' if game_context.is_primetime else 'No'}
- Playoff Implications: {'Yes' if game_context.playoff_implications else 'No'}"""

    # Add betting context if available
    if hasattr(game_context, 'current_spread') and game_context.current_spread is not None:
        user_prompt += f"""

BETTING LINES:
- Current Spread: {game_context.current_spread} (negative = home favored)
- Opening Spread: {game_context.opening_spread or 'N/A'}
- Total Line: {game_context.total_line or 'N/A'}
- Public Betting %: {game_context.public_betting_percentage or 'N/A'}%"""

    # Add team statistics if available
    if hasattr(game_context, 'home_team_stats') and game_context.home_team_stats:
        user_prompt += f"""

TEAM STATISTICS:
HOME TEAM ({game_context.home_team}):
{_format_team_stats(game_context.home_team_stats)}

AWAY TEAM ({game_context.away_team}):
{_format_team_stats(game_context.away_team_stats)}"""

    # Add environmental factors
    user_prompt += _format_environmental_factors(game_context)

    # Add injury reports if available
    if hasattr(game_context, 'home_injuries') or hasattr(game_context, 'away_injuries'):
        user_prompt += _format_injury_reports(game_context)

    # Add memory context - this is crucial for AI learning
    if memories:
        user_prompt += _format_memory_context(memories, expert_name)
    else:
        user_prompt += f"""

🧠 EPISODIC MEMORIES:
No relevant past experiences found for this matchup. You'll be analyzing this game fresh."""

    # Add structured output requirements for all 30+ categories
    user_prompt += """

REQUIRED ANALYSIS:
Provide comprehensive predictions across ALL categories using this EXACT format:

ANALYSIS: [Your detailed reasoning - 3-4 sentences explaining your key insights]

CORE PREDICTIONS:
WINNER: [home/away]
WINNER_CONFIDENCE: [50-95]
SPREAD: [home team perspective, e.g., -3.5 or +7.0]
SPREAD_CONFIDENCE: [50-95]
TOTAL: [over/under]
TOTAL_POINTS: [projected total, e.g., 47.5]
TOTAL_CONFIDENCE: [50-95]
EXACT_SCORE: [e.g., 24-21]
MARGIN: [winning margin, e.g., 3]

QUARTER PREDICTIONS:
Q1_HOME: [0-21]
Q1_AWAY: [0-21]
Q2_HOME: [0-21]
Q2_AWAY: [0-21]
Q3_HOME: [0-21]
Q3_AWAY: [0-21]
Q4_HOME: [0-21]
Q4_AWAY: [0-21]
FIRST_HALF_WINNER: [home/away/tie]
HIGHEST_SCORING_QUARTER: [1/2/3/4]

SITUATIONAL PREDICTIONS:
TURNOVER_DIFF: [-3 to +3, home team perspective]
RED_ZONE_EFF: [0.0-1.0, combined efficiency]
THIRD_DOWN_CONV: [0.0-1.0, combined conversion rate]
TIME_OF_POSS: [home team minutes, e.g., 32.5]
TOTAL_SACKS: [combined sacks, e.g., 4]
TOTAL_PENALTIES: [combined penalties, e.g., 12]

ENVIRONMENTAL IMPACT:
WEATHER_IMPACT: [0.0-1.0, how much weather affects game]
INJURY_IMPACT: [0.0-1.0, how much injuries affect outcome]
MOMENTUM_FACTOR: [0.0-1.0, momentum advantage]
SPECIAL_TEAMS: [0.0-1.0, special teams impact]
COACHING_EDGE: [0.0-1.0, coaching advantage]

KEY_FACTORS: [List 3-5 most important factors]
MEMORY_INFLUENCE: [How past experiences influenced this analysis]
CONFIDENCE_OVERALL: [50-95, your overall confidence in this analysis]

Example format:
ANALYSIS: Chiefs have strong home advantage and better offensive efficiency. Ravens defense is solid but Chiefs passing attack should exploit secondary weaknesses. Weather conditions favor the over.

CORE PREDICTIONS:
WINNER: home
WINNER_CONFIDENCE: 68
SPREAD: -6.5
SPREAD_CONFIDENCE: 62
TOTAL: over
TOTAL_POINTS: 48.5
TOTAL_CONFIDENCE: 71
EXACT_SCORE: 28-21
MARGIN: 7

[Continue with all other categories...]"""

    return user_prompt


def _get_trait_description(trait_name: str, trait_value: float) -> str:
    """Convert personality trait values to descriptive text."""

    trait_descriptions = {
        'risk_tolerance': {
            0.8: 'Very high risk tolerance', 0.6: 'High risk tolerance',
            0.4: 'Moderate risk tolerance', 0.2: 'Low risk tolerance', 0.0: 'Very conservative'
        },
        'contrarian_tendency': {
            0.8: 'Strong contrarian', 0.6: 'Moderately contrarian',
            0.4: 'Balanced approach', 0.2: 'Follows consensus', 0.0: 'Strong consensus follower'
        },
        'analytics_trust': {
            0.8: 'Heavy analytics focus', 0.6: 'Analytics-driven',
            0.4: 'Balanced analytics/intuition', 0.2: 'Intuition-focused', 0.0: 'Pure gut instinct'
        },
        'recent_bias': {
            0.8: 'Heavy recency weighting', 0.6: 'Recent form important',
            0.4: 'Balanced historical view', 0.2: 'Long-term focused', 0.0: 'Historical patterns only'
        },
        'optimism': {
            0.8: 'Very optimistic outlook', 0.6: 'Generally optimistic',
            0.4: 'Balanced perspective', 0.2: 'Generally pessimistic', 0.0: 'Very pessimistic'
        }
    }

    if trait_name not in trait_descriptions:
        return f"{trait_value:.1f} intensity"

    # Find closest description
    descriptions = trait_descriptions[trait_name]
    closest_value = min(descriptions.keys(), key=lambda x: abs(x - trait_value))
    return descriptions[closest_value]


def _get_expert_analytical_focus(expert_id: str) -> str:
    """Get expert-specific analytical focus based on their specialty."""

    focus_mapping = {
        'conservative_analyzer': """
- Emphasize statistical analysis and historical patterns
- Focus on risk management and probability assessment
- Weight defensive metrics heavily in analysis
- Prefer safer, higher-probability predictions
- Analyze injury impact and roster depth carefully""",

        'risk_taking_gambler': """
- Look for high-upside, contrarian opportunities
- Focus on explosive offensive potential and big plays
- Weight recent momentum and hot streaks heavily
- Seek out upset potential and undervalued situations
- Analyze coaching aggressiveness and game script""",

        'contrarian_rebel': """
- Identify market inefficiencies and public bias
- Focus on fading popular narratives and media hype
- Weight line movement and sharp money indicators
- Look for situations where public is wrong
- Analyze contrarian angles and unpopular picks""",

        'value_hunter': """
- Seek undervalued teams and overlooked factors
- Focus on situational advantages and hidden edges
- Weight coaching matchups and scheme advantages
- Look for teams with improving fundamentals
- Analyze market pricing vs. true probability""",

        'momentum_rider': """
- Emphasize recent form and trending patterns
- Focus on team momentum and confidence levels
- Weight recent game results and performance trends
- Look for teams riding hot or cold streaks
- Analyze psychological factors and team chemistry""",

        'fundamentalist_scholar': """
- Deep dive into advanced statistics and metrics
- Focus on underlying fundamentals and efficiency
- Weight long-term trends and regression analysis
- Look for sustainable competitive advantages
- Analyze coaching philosophy and system fit""",

        'chaos_theory_believer': """
- Embrace unpredictability and random events
- Focus on variance and unexpected outcomes
- Weight chaos factors like weather and injuries
- Look for games with high upset potential
- Analyze butterfly effect scenarios""",

        'gut_instinct_expert': """
- Trust intuitive feel for game flow and matchups
- Focus on intangible factors and team chemistry
- Weight emotional and psychological elements
- Look for situational advantages and motivation
- Analyze coaching decisions and in-game adjustments""",

        'statistics_purist': """
- Pure mathematical and statistical analysis
- Focus on quantitative metrics and models
- Weight efficiency ratings and advanced stats
- Look for statistical edges and correlations
- Analyze regression candidates and outliers""",

        'trend_reversal_specialist': """
- Identify trend reversals and inflection points
- Focus on teams due for performance changes
- Weight mean reversion and regression factors
- Look for overvalued/undervalued situations
- Analyze cyclical patterns and timing""",

        'popular_narrative_fader': """
- Fade popular media narratives and storylines
- Focus on objective analysis vs. public perception
- Weight contrarian indicators and market sentiment
- Look for overhyped and overlooked situations
- Analyze narrative bias and media influence""",

        'sharp_money_follower': """
- Follow professional betting patterns and line movement
- Focus on market efficiency and sharp indicators
- Weight reverse line movement and steam moves
- Look for where smart money is positioned
- Analyze betting market dynamics""",

        'underdog_champion': """
- Champion underdog potential and upset scenarios
- Focus on situational advantages for underdogs
- Weight motivation and desperation factors
- Look for teams with nothing to lose
- Analyze point spread value and dog advantages""",

        'consensus_follower': """
- Follow expert consensus and popular opinion
- Focus on widely agreed upon analysis
- Weight majority viewpoints and common factors
- Look for safe, consensus plays
- Analyze where experts agree most strongly""",

        'market_inefficiency_exploiter': """
- Exploit pricing errors and market inefficiencies
- Focus on arbitrage opportunities and value gaps
- Weight market dynamics and pricing models
- Look for mispriced lines and betting opportunities
- Analyze market psychology and behavioral biases"""
    }

    return focus_mapping.get(expert_id, "- General NFL analysis and prediction methodology")


def _format_team_stats(team_stats: Dict[str, Any]) -> str:
    """Format team statistics for prompt inclusion."""
    if not team_stats:
        return "- Statistics not available"

    formatted = ""
    stat_mappings = {
        'wins': 'Record (W)',
        'losses': 'Record (L)',
        'points_per_game': 'Points/Game',
        'points_allowed_per_game': 'Points Allowed/Game',
        'yards_per_game': 'Yards/Game',
        'yards_allowed_per_game': 'Yards Allowed/Game',
        'turnover_differential': 'Turnover Diff',
        'coach': 'Head Coach',
        'qb': 'Starting QB',
        'rest_days': 'Rest Days'
    }

    for key, label in stat_mappings.items():
        if key in team_stats and team_stats[key] is not None:
            formatted += f"- {label}: {team_stats[key]}\n"

    return formatted.strip()


def _format_environmental_factors(game_context: Any) -> str:
    """Format environmental factors like weather and venue."""
    env_section = ""

    # Weather conditions
    if hasattr(game_context, 'weather_conditions') and game_context.weather_conditions:
        weather = game_context.weather_conditions
        env_section += f"""

WEATHER CONDITIONS:
- Temperature: {weather.get('temperature', 'N/A')}°F
- Wind Speed: {weather.get('wind_speed', 'N/A')} mph
- Conditions: {weather.get('conditions', 'N/A')}
- Precipitation: {weather.get('precipitation', 'None')}"""

    # Stadium information
    if hasattr(game_context, 'stadium_info') and game_context.stadium_info:
        stadium = game_context.stadium_info
        env_section += f"""

VENUE INFORMATION:
- Stadium: {stadium.get('name', 'N/A')}
- Surface: {stadium.get('surface', 'N/A')}
- Roof: {stadium.get('roof_type', 'N/A')}
- Capacity: {stadium.get('capacity', 'N/A')}"""

    return env_section


def _format_injury_reports(game_context: Any) -> str:
    """Format injury reports for both teams."""
    injury_section = ""

    if hasattr(game_context, 'home_injuries') and game_context.home_injuries:
        injury_section += f"""

INJURY REPORT - {game_context.home_team}:"""
        for injury in game_context.home_injuries[:5]:  # Limit to top 5
            player = injury.get('player', 'Unknown')
            position = injury.get('position', 'N/A')
            status = injury.get('status', 'N/A')
            injury_section += f"\n- {player} ({position}): {status}"

    if hasattr(game_context, 'away_injuries') and game_context.away_injuries:
        injury_section += f"""

INJURY REPORT - {game_context.away_team}:"""
        for injury in game_context.away_injuries[:5]:  # Limit to top 5
            player = injury.get('player', 'Unknown')
            position = injury.get('position', 'N/A')
            status = injury.get('status', 'N/A')
            injury_section += f"\n- {player} ({position}): {status}"

    return injury_section


def _format_memory_context(memories: List[Dict[str, Any]], expert_name: str) -> str:
    """
    Add memory context formatting to help AI understand relevant past experiences.

    This formats retrieved episodic memories in a way that helps the AI model
    understand and apply lessons from similar past situations.
    """

    if not memories:
        return ""

    memory_section = f"""

🧠 YOUR EPISODIC MEMORIES ({len(memories)} relevant experiences):
These are your past experiences with similar games. Learn from them!

"""

    for i, memory in enumerate(memories[:5], 1):  # Limit to top 5 memories
        # Extract memory details safely
        memory_id = memory.get('memory_id', f'memory_{i}')
        similarity_score = memory.get('similarity_score', 0.5)
        memory_type = memory.get('memory_type', 'unknown')

        # Get teams from contextual factors
        contextual_factors = memory.get('contextual_factors', [])
        teams = {'home_team': 'Unknown', 'away_team': 'Unknown'}

        for factor in contextual_factors:
            if isinstance(factor, dict):
                factor_name = factor.get('factor', '')
                if factor_name in ['home_team', 'away_team']:
                    teams[factor_name] = factor.get('value', 'Unknown')

        # Get prediction and outcome data
        prediction_data = memory.get('prediction_data', {})
        actual_outcome = memory.get('actual_outcome', {})

        # Parse JSON strings if needed
        if isinstance(prediction_data, str):
            try:
                prediction_data = json.loads(prediction_data)
            except:
                prediction_data = {}

        if isinstance(actual_outcome, str):
            try:
                actual_outcome = json.loads(actual_outcome)
            except:
                actual_outcome = {}

        # Determine if prediction was correct
        pred_winner = prediction_data.get('winner', 'unknown')
        actual_winner = actual_outcome.get('winner', 'unknown')
        was_correct = pred_winner == actual_winner

        # Get lessons learned
        lessons = memory.get('lessons_learned', [])
        if isinstance(lessons, str):
            try:
                lessons = json.loads(lessons)
            except:
                lessons = [lessons] if lessons else []

        memory_section += f"""MEMORY {i} (Similarity: {similarity_score:.1f}, Type: {memory_type}):
Game: {teams['away_team']} @ {teams['home_team']}
Your Prediction: {pred_winner} (confidence: {prediction_data.get('confidence', 0.5):.0%})
Actual Result: {actual_winner} {'✅ CORRECT' if was_correct else '❌ WRONG'}
"""

        # Add key lessons
        if lessons:
            memory_section += "Key Lessons:\n"
            for lesson in lessons[:2]:  # Top 2 lessons
                if isinstance(lesson, dict):
                    lesson_text = lesson.get('lesson', 'No lesson recorded')
                else:
                    lesson_text = str(lesson)
                memory_section += f"  • {lesson_text}\n"

        memory_section += "\n"

    memory_section += f"""💡 MEMORY GUIDANCE:
- Use these experiences to inform your current analysis
- Pay attention to patterns from similar game situations
- Learn from both your successes and mistakes
- Weight recent memories more heavily than old ones
- Apply lessons learned to improve prediction accuracy

"""

    return memory_section
