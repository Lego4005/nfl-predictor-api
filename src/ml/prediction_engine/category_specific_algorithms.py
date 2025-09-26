"""
Category-Specific Prediction Algorithms
Implements prediction algorithms for each of the 27 categories, customized by expert personality
"""

from typing import Dict, List, Any, Optional
from datetime import datetime
import numpy as np
import random
from .comprehensive_prediction_categories import ExpertPrediction, get_prediction_categories

class CategorySpecificPredictor:
    """Generates category-specific predictions based on expert personality"""
    
    def __init__(self):
        self.categories = get_prediction_categories()
    
    def generate_comprehensive_prediction(
        self, 
        expert: Any, 
        game_data: Dict[str, Any]
    ) -> ExpertPrediction:
        """Generate complete 27-category prediction for an expert"""
        
        # Initialize prediction object
        prediction = ExpertPrediction(
            expert_id=expert.expert_id,
            expert_name=expert.name,
            game_id=game_data.get('game_id', 'unknown'),
            prediction_timestamp=datetime.now()
        )
        
        # Get expert personality traits for algorithm customization
        personality_traits = getattr(expert, 'personality_traits', {})
        
        # Generate predictions by category group
        self._predict_game_outcomes(prediction, expert, game_data, personality_traits)
        self._predict_betting_markets(prediction, expert, game_data, personality_traits)
        self._predict_live_scenarios(prediction, expert, game_data, personality_traits)
        self._predict_player_props(prediction, expert, game_data, personality_traits)
        self._predict_situational_factors(prediction, expert, game_data, personality_traits)
        
        # Calculate overall confidence and reasoning
        self._calculate_overall_confidence(prediction, expert, personality_traits)
        self._generate_reasoning(prediction, expert, game_data, personality_traits)
        
        return prediction
    
    def _predict_game_outcomes(
        self, 
        prediction: ExpertPrediction, 
        expert: Any, 
        game_data: Dict[str, Any], 
        traits: Dict[str, Any]
    ):
        """Predict game outcome categories"""
        
        # Base win probability calculation influenced by personality
        risk_tolerance = self._get_trait_value(traits, 'risk_tolerance', 0.5)
        analytics_trust = self._get_trait_value(traits, 'analytics_trust', 0.5)
        
        # Calculate base home win probability
        spread = game_data.get('spread', 0)
        home_advantage = game_data.get('home_field_advantage', 2.5)
        
        # Personality adjustments
        if analytics_trust > 0.7:
            # Data-driven experts rely more on spread
            base_prob = 0.5 + (spread * -0.03)  # Negative because spread is for home team
        else:
            # Intuitive experts use gut feeling
            base_prob = 0.5 + random.uniform(-0.2, 0.2)
        
        # Risk tolerance affects confidence in picks
        if risk_tolerance > 0.7:
            # High risk tolerance - more extreme predictions
            base_prob = 0.5 + (base_prob - 0.5) * 1.3
        elif risk_tolerance < 0.3:
            # Conservative - predictions closer to 50/50
            base_prob = 0.5 + (base_prob - 0.5) * 0.7
        
        base_prob = max(0.1, min(0.9, base_prob))
        
        # Winner Prediction
        prediction.winner_prediction = "home" if base_prob > 0.5 else "away"
        
        # Exact Scores - influenced by expert's scoring tendencies
        total_points = game_data.get('total', 45)
        home_share = base_prob * 0.8 + 0.1  # Convert prob to score share
        
        prediction.exact_score_home = int(total_points * home_share)
        prediction.exact_score_away = int(total_points * (1 - home_share))
        
        # Margin of Victory
        prediction.margin_of_victory = abs(prediction.exact_score_home - prediction.exact_score_away)
        
        # Add category-specific confidence
        prediction.confidence_by_category['winner_prediction'] = min(0.95, max(0.55, abs(base_prob - 0.5) * 2 + 0.5))
        prediction.confidence_by_category['exact_score'] = 0.3 + risk_tolerance * 0.3  # Lower confidence for exact scores
        prediction.confidence_by_category['margin'] = 0.4 + analytics_trust * 0.3
    
    def _predict_betting_markets(
        self, 
        prediction: ExpertPrediction, 
        expert: Any, 
        game_data: Dict[str, Any], 
        traits: Dict[str, Any]
    ):
        """Predict betting market categories"""
        
        contrarian_tendency = self._get_trait_value(traits, 'contrarian_tendency', 0.5)
        market_trust = self._get_trait_value(traits, 'market_trust', 0.5)
        
        # Against the Spread
        spread = game_data.get('spread', 0)
        if contrarian_tendency > 0.7:
            # Contrarians often take the underdog
            prediction.against_the_spread = "away" if spread < 0 else "home"
        else:
            # Follow the winner prediction
            prediction.against_the_spread = prediction.winner_prediction
        
        # Totals Over/Under
        total_line = game_data.get('total', 45)
        predicted_total = prediction.exact_score_home + prediction.exact_score_away
        
        if abs(predicted_total - total_line) < 3:
            prediction.totals_over_under = "push"
        else:
            prediction.totals_over_under = "over" if predicted_total > total_line else "under"
        
        # First Half Winner
        # Simulate first half based on game flow expectations
        if market_trust > 0.6:
            # Trust market - first half often matches game winner
            prediction.first_half_winner = prediction.winner_prediction
        else:
            # More random first half prediction
            first_half_prob = 0.5 + random.uniform(-0.3, 0.3)
            prediction.first_half_winner = "home" if first_half_prob > 0.5 else "away"
        
        # Highest Scoring Quarter
        # Use expert personality to determine quarter preference
        confidence_level = self._get_trait_value(traits, 'confidence_level', 0.5)
        if confidence_level > 0.7:
            # Confident experts predict 4th quarter drama
            prediction.highest_scoring_quarter = "Q4"
        else:
            # More conservative - predict middle quarters
            prediction.highest_scoring_quarter = random.choice(["Q2", "Q3"])
        
        # Betting market confidence
        prediction.confidence_by_category['spread'] = 0.6 + contrarian_tendency * 0.2
        prediction.confidence_by_category['total'] = 0.5 + market_trust * 0.3
        prediction.confidence_by_category['first_half'] = 0.4 + confidence_level * 0.2
        prediction.confidence_by_category['quarter'] = 0.3 + confidence_level * 0.2
    
    def _predict_live_scenarios(
        self, 
        prediction: ExpertPrediction, 
        expert: Any, 
        game_data: Dict[str, Any], 
        traits: Dict[str, Any]
    ):
        """Predict live game scenario categories"""
        
        chaos_comfort = self._get_trait_value(traits, 'chaos_comfort', 0.5)
        intuition_weight = self._get_trait_value(traits, 'intuition_weight', 0.5)
        
        # Live Win Probability - dynamic based on game state
        base_win_prob = 0.6 if prediction.winner_prediction == "home" else 0.4
        
        # Adjust for expert's comfort with changing situations
        if chaos_comfort > 0.7:
            # Comfortable with volatility - more extreme probabilities
            base_win_prob = 0.5 + (base_win_prob - 0.5) * 1.4
        
        prediction.live_win_probability = max(0.05, min(0.95, base_win_prob))
        
        # Next Score Probability
        if intuition_weight > 0.7:
            # Intuitive experts more likely to predict touchdowns
            prediction.next_score_probability = "touchdown"
        else:
            # Conservative experts predict field goals
            prediction.next_score_probability = "field_goal"
        
        # Drive Outcome Prediction
        offensive_confidence = random.uniform(0.3, 0.8)
        if offensive_confidence > 0.6:
            prediction.drive_outcome_prediction = "touchdown"
        elif offensive_confidence > 0.4:
            prediction.drive_outcome_prediction = "field_goal"
        else:
            prediction.drive_outcome_prediction = "punt"
        
        # Fourth Down Decision
        risk_tolerance = self._get_trait_value(traits, 'risk_tolerance', 0.5)
        if risk_tolerance > 0.7:
            prediction.fourth_down_decision = "go_for_it"
        elif risk_tolerance > 0.3:
            prediction.fourth_down_decision = "field_goal"
        else:
            prediction.fourth_down_decision = "punt"
        
        # Live scenario confidence
        prediction.confidence_by_category['live_prob'] = 0.4 + chaos_comfort * 0.3
        prediction.confidence_by_category['next_score'] = 0.3 + intuition_weight * 0.3
        prediction.confidence_by_category['drive'] = 0.4
        prediction.confidence_by_category['fourth_down'] = 0.3 + risk_tolerance * 0.2
    
    def _predict_player_props(
        self, 
        prediction: ExpertPrediction, 
        expert: Any, 
        game_data: Dict[str, Any], 
        traits: Dict[str, Any]
    ):
        """Predict player performance categories"""
        
        optimism = self._get_trait_value(traits, 'optimism', 0.5)
        data_reliance = self._get_trait_value(traits, 'data_reliance', 0.5)
        
        # Base player performance expectations
        game_total = prediction.exact_score_home + prediction.exact_score_away
        
        # QB Passing Yards - scaled with game total
        base_passing = 250 + (game_total - 45) * 3
        if optimism > 0.6:
            base_passing *= 1.1  # Optimistic experts predict higher stats
        prediction.qb_passing_yards = max(150, min(450, base_passing + random.uniform(-30, 30)))
        
        # QB Touchdowns
        touchdown_rate = game_total / 21  # Rough touchdowns per total points
        prediction.qb_touchdowns = max(0, min(6, int(touchdown_rate * 0.7 + random.uniform(-0.5, 1))))
        
        # QB Interceptions - inversely related to optimism
        int_rate = 2.5 - optimism * 1.5
        prediction.qb_interceptions = max(0, min(4, int(int_rate + random.uniform(-0.5, 0.5))))
        
        # RB Rushing Yards
        rushing_emphasis = 1.0 - data_reliance * 0.3  # Less analytical = more running
        base_rushing = 85 * rushing_emphasis
        prediction.rb_rushing_yards = max(20, min(200, base_rushing + random.uniform(-25, 40)))
        
        # RB Touchdowns
        prediction.rb_touchdowns = max(0, min(3, int(game_total / 25 + random.uniform(-0.3, 0.8))))
        
        # WR Receiving Yards
        passing_correlation = prediction.qb_passing_yards / 250 * 80
        prediction.wr_receiving_yards = max(30, min(150, passing_correlation + random.uniform(-20, 20)))
        
        # WR Receptions
        reception_rate = prediction.wr_receiving_yards / 12  # Average yards per catch
        prediction.wr_receptions = max(2, min(12, int(reception_rate + random.uniform(-1, 2))))
        
        # Fantasy Points Projection
        qb_fantasy = prediction.qb_passing_yards * 0.04 + prediction.qb_touchdowns * 4 - prediction.qb_interceptions * 2
        prediction.fantasy_points_projection = max(5, min(35, qb_fantasy + random.uniform(-3, 3)))
        
        # Player props confidence
        prediction.confidence_by_category['qb_yards'] = 0.5 + data_reliance * 0.2
        prediction.confidence_by_category['qb_tds'] = 0.4 + optimism * 0.2
        prediction.confidence_by_category['rb_yards'] = 0.4 + (1 - data_reliance) * 0.2
        prediction.confidence_by_category['wr_yards'] = 0.4
        prediction.confidence_by_category['fantasy'] = 0.5
    
    def _predict_situational_factors(
        self, 
        prediction: ExpertPrediction, 
        expert: Any, 
        game_data: Dict[str, Any], 
        traits: Dict[str, Any]
    ):
        """Predict situational analysis categories"""
        
        # Weather Impact Score
        weather = game_data.get('weather', {})
        temp = weather.get('temperature', 70)
        wind = weather.get('wind_speed', 5)
        precipitation = weather.get('precipitation', 0)
        
        weather_impact = 0.0
        if temp < 35 or temp > 85:
            weather_impact += 0.3
        if wind > 15:
            weather_impact += 0.4
        if precipitation > 0.3:
            weather_impact += 0.5
        
        prediction.weather_impact_score = min(1.0, weather_impact)
        
        # Injury Impact Score
        injuries = game_data.get('injuries', {})
        injury_impact = 0.0
        for team, team_injuries in injuries.items():
            for injury in team_injuries:
                if isinstance(injury, dict):
                    severity = injury.get('severity', 'probable')
                    is_starter = injury.get('is_starter', False)
                    
                    if severity == 'out' and is_starter:
                        injury_impact += 0.4
                    elif severity == 'doubtful' and is_starter:
                        injury_impact += 0.2
                    elif severity == 'questionable' and is_starter:
                        injury_impact += 0.1
        
        prediction.injury_impact_score = min(1.0, injury_impact)
        
        # Travel/Rest Factor
        travel_info = game_data.get('travel', {})
        home_rest = travel_info.get('home_rest_days', 7)
        away_rest = travel_info.get('away_rest_days', 7)
        travel_distance = travel_info.get('travel_distance', 500)
        
        rest_advantage = (home_rest - away_rest) / 14  # Normalize to roughly -0.5 to 0.5
        travel_disadvantage = min(0.3, travel_distance / 3000 * 0.3)
        prediction.travel_rest_factor = max(-0.5, min(0.5, rest_advantage - travel_disadvantage))
        
        # Divisional Rivalry Factor
        is_divisional = game_data.get('is_divisional', False)
        prediction.divisional_rivalry_factor = 0.8 if is_divisional else 0.2
        
        # Coaching Advantage
        coaching_data = game_data.get('coaching', {})
        home_coach_exp = coaching_data.get('home_experience', 5)
        away_coach_exp = coaching_data.get('away_experience', 5)
        
        if home_coach_exp > away_coach_exp + 2:
            prediction.coaching_advantage = "home"
        elif away_coach_exp > home_coach_exp + 2:
            prediction.coaching_advantage = "away"
        else:
            prediction.coaching_advantage = "neutral"
        
        # Home Field Advantage
        venue_data = game_data.get('venue', {})
        crowd_factor = venue_data.get('crowd_factor', 1.0)
        altitude = venue_data.get('altitude', 0)
        
        base_advantage = 2.5 * crowd_factor
        if altitude > 3000:  # High altitude adjustment
            base_advantage += 1.0
        
        prediction.home_field_advantage = max(0, min(8, base_advantage))
        
        # Momentum Factor
        home_momentum = game_data.get('home_momentum', 0)
        away_momentum = game_data.get('away_momentum', 0)
        prediction.momentum_factor = max(-1.0, min(1.0, (home_momentum - away_momentum) / 100))
        
        # Situational confidence
        prediction.confidence_by_category['weather'] = 0.7
        prediction.confidence_by_category['injury'] = 0.6
        prediction.confidence_by_category['travel'] = 0.5
        prediction.confidence_by_category['divisional'] = 0.8
        prediction.confidence_by_category['coaching'] = 0.4
        prediction.confidence_by_category['home_field'] = 0.6
        prediction.confidence_by_category['momentum'] = 0.5
    
    def _calculate_overall_confidence(
        self, 
        prediction: ExpertPrediction, 
        expert: Any, 
        traits: Dict[str, Any]
    ):
        """Calculate overall prediction confidence"""
        
        # Average category confidences
        if prediction.confidence_by_category:
            avg_confidence = sum(prediction.confidence_by_category.values()) / len(prediction.confidence_by_category)
        else:
            avg_confidence = 0.5
        
        # Adjust for expert's natural confidence level
        confidence_trait = self._get_trait_value(traits, 'confidence_level', 0.5)
        
        # Apply personality adjustment
        adjusted_confidence = avg_confidence * 0.7 + confidence_trait * 0.3
        
        prediction.confidence_overall = max(0.1, min(0.95, adjusted_confidence))
    
    def _generate_reasoning(
        self, 
        prediction: ExpertPrediction, 
        expert: Any, 
        game_data: Dict[str, Any], 
        traits: Dict[str, Any]
    ):
        """Generate reasoning for the prediction"""
        
        key_factors = []
        reasoning_parts = []
        
        # Add key factors based on prediction
        if prediction.weather_impact_score > 0.5:
            key_factors.append("Weather conditions")
            reasoning_parts.append(f"Weather conditions will significantly impact the game (impact: {prediction.weather_impact_score:.1f})")
        
        if prediction.injury_impact_score > 0.3:
            key_factors.append("Key injuries")
            reasoning_parts.append(f"Injuries to key players affect team performance (impact: {prediction.injury_impact_score:.1f})")
        
        if prediction.divisional_rivalry_factor > 0.7:
            key_factors.append("Divisional rivalry")
            reasoning_parts.append("Divisional game dynamics create added intensity")
        
        if abs(prediction.travel_rest_factor) > 0.2:
            key_factors.append("Travel/Rest advantage")
            factor_desc = "advantage" if prediction.travel_rest_factor > 0 else "disadvantage" 
            reasoning_parts.append(f"Home team has rest/travel {factor_desc}")
        
        # Add personality-specific reasoning
        if self._get_trait_value(traits, 'analytics_trust', 0.5) > 0.7:
            reasoning_parts.append("Analysis based on statistical models and historical data")
        elif self._get_trait_value(traits, 'intuition_weight', 0.5) > 0.7:
            reasoning_parts.append("Prediction incorporates situational awareness and gut instinct")
        
        if self._get_trait_value(traits, 'contrarian_tendency', 0.5) > 0.7:
            reasoning_parts.append("Taking a contrarian approach against public sentiment")
        
        # Combine reasoning
        if reasoning_parts:
            prediction.reasoning = ". ".join(reasoning_parts) + "."
        else:
            prediction.reasoning = f"Standard analysis for {prediction.winner_prediction} team victory."
        
        prediction.key_factors = key_factors
    
    def _get_trait_value(self, traits: Dict[str, Any], trait_name: str, default: float) -> float:
        """Get personality trait value safely"""
        trait = traits.get(trait_name)
        if trait is None:
            return default
        
        # Handle PersonalityTrait objects
        if hasattr(trait, 'value'):
            return trait.value
        
        # Handle direct values
        if isinstance(trait, (int, float)):
            return float(trait)
        
        return default