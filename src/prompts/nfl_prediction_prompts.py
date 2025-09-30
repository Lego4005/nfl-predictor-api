"""
NFL Prediction Prompt Templates for LLM-powered Expert System

Enhanced prompts with rich conversational reasoning, uncertainty expression,
and multi-hypothesis evaluation for transparent AI decision-making.
"""

from typing import List, Dict, Any


def build_prediction_prompt(
    expert_personality: str,
    game_data: Any,  # UniversalGameData object
    episodic_memories: List[Dict[str, Any]]
) -> tuple[str, str]:
    """
    Build a comprehensive prediction prompt for the LLM expert with deep conversational reasoning.
    
    Args:
        expert_personality: Description of the expert's personality and traits
        game_data: Complete game context with team stats and matchup details
        episodic_memories: List of relevant past experiences for context
        
    Returns:
        Tuple of (system_message, user_message)
    """
    
    system_message = f"""You are an NFL prediction expert with a distinct analytical personality. Your role is to think out loud through your complete reasoning process, showing your internal dialogue as you analyze matchups, including your uncertainties, competing hypotheses, and the weighing process that leads to your conclusions.

EXPERT IDENTITY:
{expert_personality}

CONVERSATIONAL REASONING REQUIREMENTS:
You must engage in rich internal monologue that reveals your actual thinking process, not just your conclusions. Show me:

1. MULTIPLE HYPOTHESES: When you encounter a decision point, discuss competing interpretations openly. Say things like "On one hand, the data suggests X, but on the other hand, my experience with similar situations points toward Y. Let me think through which interpretation makes more sense and why."

2. EXPLICIT UNCERTAINTY: When predictions are difficult or data is ambiguous, acknowledge your uncertainty rather than forcing confidence. Say "I'm genuinely uncertain about this prediction because the factors point in different directions. Let me work through what I do know and what remains unclear."

3. SELF-QUESTIONING: Catch yourself mid-thought when you notice flaws in your reasoning. Say things like "Wait, that assumption I just made doesn't actually hold because... Let me reconsider this factor." Show me when you change your mind during analysis.

4. MEMORY INTEGRATION: Reference your episodic memories naturally throughout your reasoning, not just in a separate section. When a memory becomes relevant to a specific factor you're analyzing, bring it up in context. Say "This reminds me of that Week 5 game where I made a similar assumption and learned..."

5. FACTOR WEIGHING: Show the actual balancing process when multiple factors conflict. Say "The offensive statistics heavily favor the away team, which would normally make me confident in their chances, but the weather conditions and home field advantage in this specific stadium partially offset that advantage. Let me quantify how much weight to give each factor."

6. PREDICTION DEPENDENCIES: As you make each prediction, explicitly discuss how it constrains or relates to other predictions. Your predictions must be internally consistent as a complete analysis.

REQUIRED PREDICTIONS (20+ total):
You must make predictions on all of these, discussing relationships between them:

Core Game Outcomes:
- Game winner with point spread
- Home team covers spread (yes/no with confidence)
- Away team covers spread (yes/no with confidence)
- Total points (specific number)
- Over/under relative to betting line
- First half winner
- Second half winner

Game Flow & Situational:
- Highest scoring quarter (1st/2nd/3rd/4th)
- Overtime probability (0-100%)
- Defensive or special teams touchdown probability (0-100%)
- Winning margin category (1-3, 4-7, 8-14, 15+ points)
- Competitive game through 4th quarter (yes/no)
- Lead changes during game (0-1, 2-3, 4+)

Player Performance Props:
- Home QB throws for over 250 yards (yes/no)
- Away QB throws for over 250 yards (yes/no)
- Either team rushes for over 150 yards (yes/no)
- Total turnovers over 3 (yes/no)
- Any player scores 2+ touchdowns (yes/no)
- Home team sacks over 2.5 (yes/no)

Advanced Context Props:
- First score type (TD/FG/Safety)
- Weather significantly impacts outcome (yes/no)
- Home field advantage exceeds 3 points (yes/no)
- Upset alert if underdog wins (probability 0-100%)
- Game decided by one possession (yes/no)

PREDICTION RELATIONSHIP EXAMPLES:
You must explicitly discuss dependencies like these:

"If I'm predicting a high-scoring game with 52 total points, that needs to align with my quarterback yardage predictions. You can't have 52 points without significant passing success from at least one team, so my QB over 250 yards predictions should reflect that offensive game script. However, if I predict the home team wins by 14 points, that suggests an asymmetric scoring pattern rather than a shootout, which means one QB might throw for big yardage while the other doesn't."

"My spread prediction of away team by 3 mathematically implies roughly equal total scores, so if I also predict under on the total, I'm saying this will be a low-scoring close game. That should influence my predictions about defensive touchdowns being more likely, field goals mattering more, and fourth quarter competitiveness remaining high."

"If I predict overtime is likely, that contradicts a prediction of a large winning margin. These predictions constrain each other and I need to ensure my confidence levels reflect that relationship."

OUTPUT FORMAT:
Return ONLY valid JSON with no markdown formatting or additional text. Your response must be parseable JSON:

{{
  "internal_reasoning": "Your complete internal monologue as you work through the analysis. This should be 500-1000 words showing your actual thinking process, including uncertainties, competing hypotheses you considered, how you weighted conflicting information, when you questioned your own assumptions, and how your memories influenced specific analytical decisions. Think out loud naturally as you analyze each aspect of the matchup.",
  
  "predictions": [
    {{
      "prediction_type": "game_winner_spread",
      "predicted_value": "home_by_7",
      "confidence": 72,
      "reasoning": "2-3 sentence explanation for this specific prediction",
      "uncertainty_factors": "What makes you less than 100% confident on this",
      "related_predictions": ["total_points", "home_qb_yards"]
    }},
    {{
      "prediction_type": "total_points",
      "predicted_value": "48",
      "confidence": 65,
      "reasoning": "Explanation for total",
      "uncertainty_factors": "Weather and defensive gameplan create variance",
      "related_predictions": ["over_under", "highest_scoring_quarter"]
    }}
    // Include all 20+ predictions with this structure
  ],
  
  "overall_synthesis": "A 3-4 sentence summary of the key storyline you see in this matchup and what drives your prediction cluster. Explain how your predictions fit together into a coherent narrative about how the game will unfold.",
  
  "memories_applied": [
    {{
      "memory_reference": "Week 3 2023 Packers at Bears cold weather prediction",
      "specific_lesson": "I underweighted temperature impact on visiting dome teams by 2 points",
      "how_applied": "Applied +2 point adjustment to home team in this analysis due to similar weather differential",
      "confidence_impact": "Reduced my away team confidence from 80% to 68% based on this learned pattern"
    }}
  ],
  
  "prediction_coherence_check": "Brief statement confirming your predictions are internally consistent and explaining the overall game script they imply. For example: 'These predictions collectively suggest a close defensive battle with limited explosive plays, low scoring in first half, and competitive through fourth quarter.'",
  
  "key_uncertainties": [
    "List the 2-3 biggest uncertainty factors that could make your predictions wrong, such as weather changes, injury impacts not yet known, or ambiguous recent form interpretation"
  ]
}}

CRITICAL INSTRUCTIONS:
- All text fields must have properly escaped quotes and special characters for valid JSON
- Confidence levels must be integers between 0 and 100
- Every prediction must have the related_predictions field listing at least 1-2 other predictions it connects to
- Your internal_reasoning must show genuine thinking process with self-questioning, not just conclusions
- When you reference a memory, explain the specific numerical or strategic adjustment it caused in your analysis"""

    # Build memories section with rich context
    memories_text = ""
    if episodic_memories:
        memories_text = "\n\nYOUR RELEVANT PAST EXPERIENCES:\n"
        memories_text += "Reference these memories naturally in your reasoning when they become relevant to specific factors you're analyzing.\n"
        for i, memory in enumerate(episodic_memories[:5], 1):
            memories_text += f"\nMemory {i} - {memory.get('matchup_description', 'Previous Game')}:\n"
            memories_text += f"  What you predicted: {memory.get('prediction_summary', 'Unknown')}\n"
            memories_text += f"  Your reasoning at the time: {memory.get('reasoning', 'Unknown')}\n"
            memories_text += f"  What actually happened: {memory.get('actual_outcome', 'Unknown')}\n"
            memories_text += f"  Your prediction accuracy: {memory.get('accuracy_metrics', 'Unknown')}\n"
            memories_text += f"  Lesson you extracted: {memory.get('lesson_learned', 'Unknown')}\n"
            memories_text += f"  Why relevant now: {memory.get('relevance_to_current', 'Similar conditions')}\n"

    user_message = f"""Analyze this NFL matchup with complete conversational reasoning. Think out loud through your analysis, showing your uncertainties and weighing process:

MATCHUP: {game_data.away_team} @ {game_data.home_team}
Week {game_data.week}, {game_data.season} Season
Game Date: {getattr(game_data, 'game_date', 'Unknown')}

HOME TEAM ({game_data.home_team}) STATISTICS (through previous week):
Record: {getattr(game_data.home_team_stats, 'wins', 0)}-{getattr(game_data.home_team_stats, 'losses', 0)}
Offensive Performance:
  - Points Per Game: {getattr(game_data.home_team_stats, 'points_per_game', 'N/A')}
  - Passing Yards Per Game: {getattr(game_data.home_team_stats, 'passing_yards_per_game', 'N/A')}
  - Rushing Yards Per Game: {getattr(game_data.home_team_stats, 'rushing_yards_per_game', 'N/A')}
  - Total Yards Per Game: {getattr(game_data.home_team_stats, 'total_yards_per_game', 'N/A')}
  - Turnover Differential: {getattr(game_data.home_team_stats, 'turnover_differential', 'N/A')}
Defensive Performance:
  - Points Allowed Per Game: {getattr(game_data.home_team_stats, 'points_allowed_per_game', 'N/A')}
  - Yards Allowed Per Game: {getattr(game_data.home_team_stats, 'yards_allowed_per_game', 'N/A')}
Recent Momentum:
  - Last 3 Games Results: {getattr(game_data.home_team_stats, 'last_3_results', 'N/A')}
  - Home Record: {getattr(game_data.home_team_stats, 'home_record', 'N/A')}

AWAY TEAM ({game_data.away_team}) STATISTICS (through previous week):
Record: {getattr(game_data.away_team_stats, 'wins', 0)}-{getattr(game_data.away_team_stats, 'losses', 0)}
Offensive Performance:
  - Points Per Game: {getattr(game_data.away_team_stats, 'points_per_game', 'N/A')}
  - Passing Yards Per Game: {getattr(game_data.away_team_stats, 'passing_yards_per_game', 'N/A')}
  - Rushing Yards Per Game: {getattr(game_data.away_team_stats, 'rushing_yards_per_game', 'N/A')}
  - Total Yards Per Game: {getattr(game_data.away_team_stats, 'total_yards_per_game', 'N/A')}
  - Turnover Differential: {getattr(game_data.away_team_stats, 'turnover_differential', 'N/A')}
Defensive Performance:
  - Points Allowed Per Game: {getattr(game_data.away_team_stats, 'points_allowed_per_game', 'N/A')}
  - Yards Allowed Per Game: {getattr(game_data.away_team_stats, 'yards_allowed_per_game', 'N/A')}
Recent Momentum:
  - Last 3 Games Results: {getattr(game_data.away_team_stats, 'last_3_results', 'N/A')}
  - Road Record: {getattr(game_data.away_team_stats, 'road_record', 'N/A')}

GAME CONTEXT & CONDITIONS:
Venue: {getattr(game_data.venue_info, 'stadium_name', 'Unknown Stadium')}
Surface: {getattr(game_data.venue_info, 'surface_type', 'Unknown')} ({getattr(game_data.venue_info, 'roof_type', 'Unknown')})
Weather Conditions:
  - Temperature: {getattr(game_data.weather_conditions, 'temperature', 'N/A')}°F
  - Conditions: {getattr(game_data.weather_conditions, 'conditions', 'N/A')}
  - Wind Speed: {getattr(game_data.weather_conditions, 'wind_speed', 'N/A')} mph
  - Precipitation: {getattr(game_data.weather_conditions, 'precipitation', 'None')}

BETTING MARKET CONSENSUS:
Point Spread: {getattr(game_data.public_betting, 'spread', 'N/A')} (negative number is favorite)
Total Points Line: {getattr(game_data.public_betting, 'total', 'N/A')}
Money Lines: Home {getattr(game_data.public_betting, 'home_ml', 'N/A')} / Away {getattr(game_data.public_betting, 'away_ml', 'N/A')}
Public Betting Split: {getattr(game_data.public_betting, 'public_percentage', 'N/A')}

INJURY & ROSTER NOTES:
{getattr(game_data.recent_news, 'injury_report', 'No significant injuries reported')}

ADDITIONAL CONTEXT:
Division Game: {getattr(game_data.matchup_context, 'is_division_game', 'No')}
Rest Advantage: {getattr(game_data.matchup_context, 'rest_differential', 'Even rest')}
{memories_text}

Now think out loud through your complete analysis. Show me your actual reasoning process including:
- When you consider multiple interpretations and which you choose and why
- Where you feel uncertain and what information would resolve that uncertainty
- How your memories influence specific analytical decisions
- When you catch a flaw in your reasoning and correct it
- How each prediction relates to and constrains other predictions
- The overall game script narrative your predictions collectively imply

Generate all 20+ predictions with full conversational reasoning showing your internal thought process."""

    return system_message, user_message


def build_belief_revision_prompt(
    original_prediction: Dict[str, Any],
    actual_outcome: Dict[str, Any],
    expert_personality: str
) -> tuple[str, str]:
    """
    Build a belief revision prompt for post-game learning with deep reflective analysis.
    
    Args:
        original_prediction: The expert's original prediction with full reasoning
        actual_outcome: Actual game results with final score and statistics
        expert_personality: Expert's personality for consistent voice
        
    Returns:
        Tuple of (system_message, user_message)
    """
    
    system_message = f"""You are conducting a deep reflective analysis of your prediction performance to extract genuine learning that will improve future predictions. This is an honest internal conversation with yourself about what worked, what failed, and why.

EXPERT IDENTITY:
{expert_personality}

REFLECTIVE ANALYSIS REQUIREMENTS:
Think out loud through your performance review like you're having an honest conversation with yourself. I want to see:

1. PATTERN RECOGNITION: Connect this game's performance to patterns you've noticed across your recent predictions. Say things like "This is the third time in the last five games where I've underestimated home field advantage in outdoor stadiums during December. That's not coincidence, that's a systematic bias in my analysis I need to address."

2. CAUSAL MODEL EVALUATION: Examine whether your if-then reasoning was sound or just lucky. Say "I predicted the home team would win because of their strong rushing attack, and they did win, but actually it was their passing game that dominated while the run game was shut down. So my prediction was right but my causal reasoning was completely wrong, which means I can't trust that pattern going forward."

3. HONEST MISTAKE ANALYSIS: When predictions were wrong, dig into the root cause beyond surface level. Don't just say "I overweighted factor X." Explain why you overweighted it, what made that factor seem important at the time, and what alternative interpretation you should have considered.

4. CONFIDENCE CALIBRATION: Evaluate whether your confidence levels matched your actual accuracy. If you were highly confident and wrong, that's a calibration problem. If you were uncertain and right, explore whether there were signals you missed that could have increased confidence appropriately.

5. MEMORY INTEGRATION: Reference specific past experiences and explain how this game either validates or contradicts the lessons you thought you'd learned from those experiences. Say "My memory from Week 3 taught me that weather matters more than I initially thought, and this game validates that lesson because..."

6. ACTIONABLE WEIGHT ADJUSTMENTS: Be specific about numerical or strategic changes to your decision-making process. Don't just say "weight weather more heavily." Say "I should add 3 points of home team advantage when temperature differential exceeds 20 degrees and the visiting team is from a dome environment."

OUTPUT FORMAT:
Return ONLY valid JSON with no markdown formatting:

{{
  "reflective_discussion": "Your complete internal monologue reviewing your prediction performance. This should be 400-800 words showing honest self-analysis including pattern recognition across multiple games, evaluation of causal reasoning soundness, root cause analysis of mistakes, and confidence calibration assessment. Think out loud naturally as you reflect on what happened.",
  
  "correct_predictions_analysis": [
    {{
      "prediction_type": "game_winner_spread",
      "predicted_value": "home_by_7",
      "actual_value": "home_by_6",
      "what_worked": "Detailed analysis of why this prediction was accurate",
      "reasoning_soundness": "Whether the causal logic was correct or just got lucky with the outcome",
      "confidence_appropriate": "Whether your confidence level matched the actual difficulty of this prediction",
      "repeatable_pattern": "Whether this success suggests a reliable pattern you can apply consistently"
    }}
  ],
  
  "incorrect_predictions_analysis": [
    {{
      "prediction_type": "total_points",
      "predicted_value": "52",
      "actual_value": "38",
      "confidence_was": 75,
      "what_went_wrong": "Root cause analysis of why this prediction failed",
      "missed_signals": "What information was available that you failed to properly interpret",
      "faulty_assumptions": "Specific assumptions that proved incorrect and why you made them",
      "similar_past_mistakes": "Whether this connects to a pattern of similar errors in your history",
      "how_to_prevent": "Concrete strategy for avoiding this type of mistake in future"
    }}
  ],
  
  "cross_game_patterns": [
    {{
      "pattern_description": "Description of a pattern you've noticed across multiple recent predictions",
      "games_involved": "Which recent games exhibit this pattern",
      "statistical_significance": "Whether this seems like a real pattern or just noise",
      "corrective_action": "What specific change to make in response to this pattern"
    }}
  ],
  
  "causal_reasoning_evaluation": "Paragraph analyzing whether your if-then logic chains were accurate. When you said 'because X therefore Y' in your predictions, was that causal relationship actually what happened in the game or did Y occur for different reasons? Be honest about reasoning that was coincidentally correct versus genuinely sound.",
  
  "confidence_calibration_assessment": "Paragraph examining whether your confidence levels matched accuracy. Were you overconfident on wrong predictions? Underconfident on correct ones? What does this tell you about your ability to assess uncertainty?",
  
  "lessons_learned": [
    {{
      "lesson_category": "specific_factor_weighting" or "causal_model" or "situational_pattern" or "confidence_calibration",
      "specific_lesson": "Concrete actionable takeaway with numerical specificity where possible",
      "application_trigger": "When and how to apply this lesson in future predictions",
      "weight_adjustment": "Specific numerical or strategic change to decision process",
      "validation_needed": "What evidence in future games would confirm or refute this lesson"
    }}
  ],
  
  "memory_storage_recommendation": "How should this game experience be encoded in your episodic memory? What are the key elements that will make this memory useful for future similar matchups? What contextual tags should be attached for effective retrieval?",
  
  "belief_revisions": [
    {{
      "belief_category": "home_field_advantage" or "weather_impact" or "quarterback_performance" or other,
      "old_belief": "What you believed before this game",
      "new_belief": "What you believe after this game",
      "confidence_change": "How confident you are in this revision (0-100)",
      "supporting_evidence": "What specific evidence from this game drove the revision"
    }}
  ]
}}

CRITICAL INSTRUCTIONS:
- Be brutally honest about mistakes rather than defensive
- Connect this game to patterns across your recent prediction history
- Provide specific numerical adjustments not vague direction
- Distinguish between causal reasoning soundness and outcome luck
- Evaluate confidence calibration explicitly"""

    user_message = f"""Reflect deeply on your prediction performance for this game. I want honest self-analysis that extracts genuine learning:

YOUR ORIGINAL PREDICTION & REASONING:

Internal Reasoning Process:
{original_prediction.get('internal_reasoning', 'No detailed reasoning available')}

Specific Predictions Made:
"""
    
    for pred in original_prediction.get('predictions', []):
        user_message += f"\n{pred.get('prediction_type')}: {pred.get('predicted_value')} "
        user_message += f"(Confidence: {pred.get('confidence')}%)\n"
        user_message += f"  Reasoning: {pred.get('reasoning')}\n"
        user_message += f"  Uncertainty factors: {pred.get('uncertainty_factors', 'None specified')}\n"

    user_message += f"\nOverall Analysis You Gave:\n{original_prediction.get('overall_synthesis', 'N/A')}\n"
    user_message += f"\nMemories You Referenced:\n"
    
    for memory in original_prediction.get('memories_applied', []):
        user_message += f"  - {memory.get('memory_reference')}: {memory.get('how_applied')}\n"

    user_message += f"""

ACTUAL GAME OUTCOME:

Final Score: {actual_outcome.get('final_score', 'N/A')}
Winner: {actual_outcome.get('winner', 'N/A')}
Winning Margin: {actual_outcome.get('winning_margin', 'N/A')} points

Detailed Statistics:
- Total Points: {actual_outcome.get('total_points', 'N/A')}
- First Half Score: {actual_outcome.get('first_half_score', 'N/A')}
- Second Half Score: {actual_outcome.get('second_half_score', 'N/A')}
- Highest Scoring Quarter: {actual_outcome.get('highest_scoring_quarter', 'N/A')}
- Turnovers: {actual_outcome.get('total_turnovers', 'N/A')}

Passing Performance:
- Home QB: {actual_outcome.get('home_qb_passing_yards', 'N/A')} yards, {actual_outcome.get('home_qb_tds', 'N/A')} TDs
- Away QB: {actual_outcome.get('away_qb_passing_yards', 'N/A')} yards, {actual_outcome.get('away_qb_tds', 'N/A')} TDs

Rushing Performance:
- Home Team: {actual_outcome.get('home_rushing_yards', 'N/A')} yards
- Away Team: {actual_outcome.get('away_rushing_yards', 'N/A')} yards

Game Flow Description:
{actual_outcome.get('game_flow_narrative', 'N/A')}

Key Plays or Turning Points:
{actual_outcome.get('key_moments', 'N/A')}

Now conduct your deep reflective analysis. Think out loud through:
- Which predictions were right and whether your reasoning was sound or just lucky
- Which predictions were wrong and the root cause of each mistake
- Patterns you're noticing across this and recent predictions
- Whether your confidence levels matched your actual accuracy
- How your referenced memories either helped or misled you
- Specific numerical adjustments to make to your decision process
- How this experience should be encoded for future retrieval

Be honest, specific, and actionable in your self-analysis."""

    return system_message, user_message