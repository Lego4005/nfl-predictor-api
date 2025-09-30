"""
LLM Expert Agent - Uses Claude Code SDK to generate NFL predictions

This agent takes an expert personality and game data, calls Claude via SDK,
and generates a structured prediction with reasoning.
"""

import os
import json
from datetime import datetime
from typing import Dict, Any, Optional
from claude_code_sdk import query
from dotenv import load_dotenv

load_dotenv()


class LLMExpertAgent:
    """
    Expert agent that uses Claude Code SDK to generate NFL predictions.

    Takes expert personality config and game data, generates prediction
    with reasoning, and stores results in Supabase.

    Uses the Claude Code SDK which authenticates through the current session,
    no API key needed!
    """

    def __init__(self, supabase_client, expert_config: Dict[str, Any], current_bankroll: float = 1000.0):
        """
        Initialize LLM Expert Agent.

        Args:
            supabase_client: Supabase client for database operations
            expert_config: Expert personality configuration from personality_experts table
            current_bankroll: Current bankroll amount for betting decisions
        """
        self.supabase = supabase_client
        self.expert_id = expert_config['expert_id']
        self.expert_name = expert_config['name']
        self.personality_traits = expert_config.get('personality_traits', {})
        self.betting_strategy = expert_config.get('betting_strategy', {})
        self.current_bankroll = current_bankroll

        # No API key needed! Claude Code SDK uses authenticated session
        print(f"✅ LLM Expert Agent initialized using Claude Code SDK")

    def build_prediction_prompt(self, game_data: Dict[str, Any]) -> str:
        """
        Build prompt for Claude API including personality traits and game data.

        Args:
            game_data: Game statistics and information

        Returns:
            Formatted prompt string
        """

        # Extract key game info
        home_team = game_data.get('home_team', 'Unknown')
        away_team = game_data.get('away_team', 'Unknown')
        game_time = game_data.get('game_time', 'Unknown')

        # Build personality description
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

        # Build game info
        game_desc = f"""
Game Information:
- Matchup: {away_team} @ {home_team}
- Game Time: {game_time}
- Home Team Stats: {json.dumps(game_data.get('home_stats', {}), indent=2)}
- Away Team Stats: {json.dumps(game_data.get('away_stats', {}), indent=2)}
"""

        # Add odds if available
        if game_data.get('odds'):
            game_desc += f"\n- Betting Odds: {json.dumps(game_data.get('odds'), indent=2)}"

        # Build full prompt
        prompt = f"""{personality_desc}

{game_desc}

Based on your personality traits and the game data provided, make your prediction for this NFL game.

Consider:
1. Your personality traits (e.g., if you have high analytics_trust, rely more on stats)
2. Your risk tolerance when deciding bet size
3. Your contrarian tendency when evaluating popular picks
4. Your current bankroll when sizing your bet

Output your prediction as a JSON object with this exact structure:
{{
    "winner": "TEAM_NAME",
    "confidence": 0.65,
    "bet_amount": 50.00,
    "reasoning": "Your detailed reasoning for this prediction..."
}}

Where:
- winner: The team you predict will win (exact team name)
- confidence: Your confidence level (0.0 to 1.0)
- bet_amount: How much to bet from your ${self.current_bankroll} bankroll
- reasoning: Detailed explanation of your prediction

Respond ONLY with the JSON object, no other text."""

        return prompt

    async def generate_prediction(self, game_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Generate prediction by calling Claude via SDK.

        Args:
            game_data: Game statistics and information

        Returns:
            Prediction dict with winner, confidence, bet_amount, reasoning
        """

        try:
            # Build prompt
            prompt = self.build_prediction_prompt(game_data)

            # Call Claude via SDK (no API key needed!)
            print(f"🤖 Calling Claude Code SDK for {self.expert_name}...")

            # Query Claude and collect response
            response_text = ""
            async for message in query(prompt=prompt):
                # Extract text from AssistantMessage content blocks
                if hasattr(message, 'content') and isinstance(message.content, list):
                    for block in message.content:
                        if hasattr(block, 'text'):
                            response_text += block.text

            print(f"📝 Claude response ({len(response_text)} chars): {response_text[:200]}...")

            # Parse JSON from response
            # Sometimes Claude wraps JSON in markdown code blocks, so extract it
            if "```json" in response_text:
                # Extract JSON from code block
                json_start = response_text.find("```json") + 7
                json_end = response_text.find("```", json_start)
                json_text = response_text[json_start:json_end].strip()
            elif "```" in response_text:
                # Extract from generic code block
                json_start = response_text.find("```") + 3
                json_end = response_text.find("```", json_start)
                json_text = response_text[json_start:json_end].strip()
            else:
                json_text = response_text.strip()

            prediction = json.loads(json_text)

            # Validate required fields
            required_fields = ['winner', 'confidence', 'bet_amount', 'reasoning']
            if not all(field in prediction for field in required_fields):
                raise ValueError(f"Missing required fields in prediction: {prediction.keys()}")

            print(f"✅ Prediction generated: {prediction['winner']} with {prediction['confidence']*100:.1f}% confidence")

            return prediction

        except json.JSONDecodeError as e:
            print(f"❌ Failed to parse JSON from Claude response: {e}")
            print(f"Response was: {response_text if 'response_text' in locals() else 'No response'}")
            return None
        except Exception as e:
            print(f"❌ Error generating prediction: {e}")
            import traceback
            traceback.print_exc()
            return None

    async def store_prediction(self, game_id: str, prediction: Dict[str, Any]) -> bool:
        """
        Store prediction in expert_predictions_comprehensive table.

        Args:
            game_id: Game identifier
            prediction: Prediction dict from generate_prediction()

        Returns:
            True if stored successfully, False otherwise
        """

        try:
            prediction_data = {
                'game_id': game_id,
                'expert_id': self.expert_id,
                'predicted_winner': prediction['winner'],
                'confidence': prediction['confidence'],
                'bet_amount': prediction['bet_amount'],
                'reasoning_summary': prediction['reasoning'][:500],  # Truncate if too long
                'prediction_timestamp': datetime.utcnow().isoformat(),
                'model_version': 'claude-3-5-sonnet-20241022'
            }

            result = self.supabase.table('expert_predictions_comprehensive') \
                .insert(prediction_data) \
                .execute()

            print(f"✅ Prediction stored in database")
            return True

        except Exception as e:
            print(f"❌ Error storing prediction: {e}")
            return False

    async def store_reasoning_chain(self, game_id: str, prediction: Dict[str, Any]) -> bool:
        """
        Store detailed reasoning in expert_reasoning_chains table.

        Args:
            game_id: Game identifier
            prediction: Prediction dict from generate_prediction()

        Returns:
            True if stored successfully, False otherwise
        """

        try:
            reasoning_data = {
                'game_id': game_id,
                'expert_id': self.expert_id,
                'reasoning_text': prediction['reasoning'],
                'confidence': prediction['confidence'],
                'key_factors': self._extract_key_factors(prediction['reasoning']),
                'timestamp': datetime.utcnow().isoformat()
            }

            result = self.supabase.table('expert_reasoning_chains') \
                .insert(reasoning_data) \
                .execute()

            print(f"✅ Reasoning chain stored in database")
            return True

        except Exception as e:
            print(f"❌ Error storing reasoning chain: {e}")
            return False

    def _extract_key_factors(self, reasoning: str) -> list:
        """
        Extract key factors from reasoning text.

        Simple extraction - looks for common keywords.
        Can be improved with more sophisticated NLP.
        """

        factors = []
        keywords = ['home advantage', 'statistics', 'momentum', 'injuries', 'weather',
                   'odds', 'defense', 'offense', 'recent form', 'head to head']

        reasoning_lower = reasoning.lower()
        for keyword in keywords:
            if keyword in reasoning_lower:
                factors.append(keyword)

        return factors if factors else ['general analysis']

    async def predict(self, game_id: str, game_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Main method: Generate prediction and store in database.

        Args:
            game_id: Game identifier
            game_data: Game statistics and information

        Returns:
            Prediction dict if successful, None otherwise
        """

        print(f"\n{'='*80}")
        print(f"🎯 {self.expert_name} ({self.expert_id}) making prediction")
        print(f"{'='*80}")

        # Generate prediction
        prediction = await self.generate_prediction(game_data)

        if not prediction:
            print(f"❌ Failed to generate prediction")
            return None

        # Store prediction
        stored_pred = await self.store_prediction(game_id, prediction)
        stored_reasoning = await self.store_reasoning_chain(game_id, prediction)

        if stored_pred and stored_reasoning:
            print(f"✅ Prediction complete and stored!")
            return prediction
        else:
            print(f"⚠️ Prediction generated but storage failed")
            return prediction