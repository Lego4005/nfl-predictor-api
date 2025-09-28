"""
Category-Specific Prediction Algorithms
Implements prediction algorithms for each of the 27 categories, customized by expert personality
"""

from typing import Dict, List, Any, Optional, Tuple
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
        """Predict game outcome categories with enhanced personality algorithms"""
        
        # Enhanced personality trait extraction
        risk_tolerance = self._get_trait_value(traits, 'risk_tolerance', 0.5)
        analytics_trust = self._get_trait_value(traits, 'analytics_trust', 0.5)
        contrarian_tendency = self._get_trait_value(traits, 'contrarian_tendency', 0.5)
        optimism = self._get_trait_value(traits, 'optimism', 0.5)
        
        # Enhanced base win probability calculation
        spread = game_data.get('spread', 0)
        total_line = game_data.get('total', 45)
        home_advantage = game_data.get('home_field_advantage', 2.5)
        
        # Multi-factor probability calculation
        if analytics_trust > 0.7:
            # Data-driven approach: sophisticated statistical model
            base_prob = self._calculate_analytical_win_probability(game_data, spread)
        elif analytics_trust < 0.3:
            # Intuitive approach: gut feeling with situational factors
            base_prob = self._calculate_intuitive_win_probability(game_data, traits)
        else:
            # Balanced approach: mix of analytics and intuition
            analytical_prob = self._calculate_analytical_win_probability(game_data, spread)
            intuitive_prob = self._calculate_intuitive_win_probability(game_data, traits)
            base_prob = analytical_prob * analytics_trust + intuitive_prob * (1 - analytics_trust)
        
        # Apply contrarian adjustment
        if contrarian_tendency > 0.6:
            public_sentiment = game_data.get('public_betting_percentage', 0.5)
            contrarian_adjustment = (0.5 - public_sentiment) * contrarian_tendency * 0.3
            base_prob += contrarian_adjustment
        
        # Risk tolerance affects prediction extremity
        if risk_tolerance > 0.7:
            # High risk tolerance - more extreme predictions
            base_prob = 0.5 + (base_prob - 0.5) * 1.4
        elif risk_tolerance < 0.3:
            # Conservative - predictions closer to 50/50
            base_prob = 0.5 + (base_prob - 0.5) * 0.6
        
        # Ensure probability bounds
        base_prob = max(0.05, min(0.95, base_prob))
        
        # Winner Prediction
        prediction.winner_prediction = "home" if base_prob > 0.5 else "away"
        
        # Enhanced Exact Scores with personality influence
        home_score, away_score = self._calculate_personality_scores(
            total_line, base_prob, game_data, traits
        )
        
        prediction.exact_score_home = int(home_score)
        prediction.exact_score_away = int(away_score)
        
        # Margin of Victory
        prediction.margin_of_victory = abs(prediction.exact_score_home - prediction.exact_score_away)
        
        # Enhanced category-specific confidence
        confidence_boost = optimism * 0.2  # Optimistic experts more confident
        prediction.confidence_by_category['winner_prediction'] = min(0.95, 
            max(0.55, abs(base_prob - 0.5) * 2 + 0.5 + confidence_boost))
        prediction.confidence_by_category['exact_score_home'] = 0.25 + risk_tolerance * 0.25
        prediction.confidence_by_category['exact_score_away'] = 0.25 + risk_tolerance * 0.25
        prediction.confidence_by_category['margin_of_victory'] = 0.35 + analytics_trust * 0.25
    
    def _calculate_analytical_win_probability(self, game_data: Dict[str, Any], spread: float) -> float:
        """Calculate win probability using analytical approach"""
        # Advanced statistical model
        base_prob = 0.5 + (spread * -0.027)  # More refined spread conversion
        
        # Adjust for additional factors
        if 'team_stats' in game_data:
            stats = game_data['team_stats']
            home_stats = stats.get('home', {})
            away_stats = stats.get('away', {})
            
            # Offensive efficiency adjustment
            home_off_eff = home_stats.get('offensive_efficiency', 0.5)
            away_off_eff = away_stats.get('offensive_efficiency', 0.5)
            base_prob += (home_off_eff - away_off_eff) * 0.15
            
            # Defensive efficiency adjustment
            home_def_eff = home_stats.get('defensive_efficiency', 0.5)
            away_def_eff = away_stats.get('defensive_efficiency', 0.5)
            base_prob += (home_def_eff - away_def_eff) * 0.12
        
        return max(0.1, min(0.9, base_prob))
    
    def _calculate_intuitive_win_probability(self, game_data: Dict[str, Any], traits: Dict[str, Any]) -> float:
        """Calculate win probability using intuitive approach"""
        # Start with slight home field bias
        base_prob = 0.52
        
        # Intuitive factors
        chaos_comfort = self._get_trait_value(traits, 'chaos_comfort', 0.5)
        
        # Weather intuition
        weather = game_data.get('weather', {})
        if weather.get('precipitation', 0) > 0.3:
            # Rain/snow favors home team in intuitive thinking
            base_prob += 0.08 * chaos_comfort
        
        # Injury intuition
        injuries = game_data.get('injuries', {})
        injury_impact = len(injuries.get('away', [])) - len(injuries.get('home', []))
        base_prob += injury_impact * 0.03
        
        # Momentum intuition
        home_momentum = game_data.get('home_momentum', 0)
        away_momentum = game_data.get('away_momentum', 0)
        momentum_diff = (home_momentum - away_momentum) / 100
        base_prob += momentum_diff * 0.1
        
        # Add some randomness for "gut feeling"
        gut_feeling = (random.random() - 0.5) * 0.15 * (1 - self._get_trait_value(traits, 'analytics_trust', 0.5))
        base_prob += gut_feeling
        
        return max(0.1, min(0.9, base_prob))
    
    def _calculate_personality_scores(
        self, total_line: float, win_prob: float, game_data: Dict[str, Any], traits: Dict[str, Any]
    ) -> Tuple[float, float]:
        """Calculate exact scores with personality influence"""
        
        optimism = self._get_trait_value(traits, 'optimism', 0.5)
        risk_tolerance = self._get_trait_value(traits, 'risk_tolerance', 0.5)
        
        # Base score distribution
        home_share = win_prob * 0.7 + 0.15  # Convert probability to score share
        
        # Optimism affects total scoring
        optimism_adjustment = 1.0 + (optimism - 0.5) * 0.3
        adjusted_total = total_line * optimism_adjustment
        
        # Risk tolerance affects score variance
        if risk_tolerance > 0.7:
            # High variance: more extreme scores
            variance_factor = 1.2
        elif risk_tolerance < 0.3:
            # Low variance: conservative scores
            variance_factor = 0.8
        else:
            variance_factor = 1.0
        
        # Apply variance to score distribution
        base_home = adjusted_total * home_share
        base_away = adjusted_total * (1 - home_share)
        
        # Add personality-driven variance
        score_variance = abs(base_home - base_away) * (variance_factor - 1)
        
        if base_home > base_away:
            final_home = base_home + score_variance / 2
            final_away = base_away - score_variance / 2
        else:
            final_home = base_home - score_variance / 2
            final_away = base_away + score_variance / 2
        
        return max(0, final_home), max(0, final_away)
    
    def _predict_betting_markets(
        self, 
        prediction: ExpertPrediction, 
        expert: Any, 
        game_data: Dict[str, Any], 
        traits: Dict[str, Any]
    ):
        """Predict betting market categories with enhanced algorithms"""
        
        contrarian_tendency = self._get_trait_value(traits, 'contrarian_tendency', 0.5)
        market_trust = self._get_trait_value(traits, 'market_trust', 0.5)
        sharp_money_awareness = self._get_trait_value(traits, 'sharp_money_awareness', 0.5)
        value_seeking = self._get_trait_value(traits, 'value_seeking', 0.5)
        
        # Enhanced Against the Spread prediction
        spread = game_data.get('spread', 0)
        predicted_margin = prediction.margin_of_victory
        
        # Determine which team is favored by spread
        home_favored = spread < 0
        spread_magnitude = abs(spread)
        
        # Calculate spread value based on prediction vs line
        if prediction.winner_prediction == "home":
            predicted_home_margin = predicted_margin
        else:
            predicted_home_margin = -predicted_margin
        
        # Compare predicted margin to spread
        spread_value = predicted_home_margin - spread
        
        # Apply personality-driven decision making
        if contrarian_tendency > 0.7:
            # Strong contrarians fade public money
            public_betting = game_data.get('public_betting_percentage', 0.5)
            if public_betting > 0.65:  # Heavy public on favorite
                prediction.against_the_spread = "away" if home_favored else "home"
            elif public_betting < 0.35:  # Heavy public on underdog
                prediction.against_the_spread = "home" if home_favored else "away"
            else:
                # Use spread value calculation
                prediction.against_the_spread = "home" if spread_value > 0 else "away"
        elif value_seeking > 0.7:
            # Value seekers look for line value
            line_movement = game_data.get('line_movement', {}).get('spread_movement', 0)
            if abs(line_movement) > 1.5:
                # Significant line movement - bet against the movement
                prediction.against_the_spread = "away" if line_movement > 0 else "home"
            else:
                prediction.against_the_spread = "home" if spread_value > 2 else "away"
        else:
            # Standard approach: follow the prediction
            if abs(spread_value) < 2:
                prediction.against_the_spread = "push"
            else:
                prediction.against_the_spread = "home" if spread_value > 0 else "away"
        
        # Enhanced Totals Over/Under prediction
        total_line = game_data.get('total', 45)
        predicted_total = prediction.exact_score_home + prediction.exact_score_away
        total_difference = predicted_total - total_line
        
        # Weather impact on totals
        weather = game_data.get('weather', {})
        weather_impact = self._calculate_weather_impact_on_totals(weather)
        
        # Pace of play adjustments
        pace_factor = self._calculate_pace_factor(game_data, traits)
        adjusted_total = predicted_total * pace_factor + weather_impact
        
        # Apply personality to totals decision
        if contrarian_tendency > 0.6:
            # Contrarians check public betting on totals
            public_total_percentage = game_data.get('public_total_percentage', 0.5)
            if public_total_percentage > 0.65:
                prediction.totals_over_under = "under"
            elif public_total_percentage < 0.35:
                prediction.totals_over_under = "over"
            else:
                prediction.totals_over_under = "over" if adjusted_total > total_line + 1 else "under"
        else:
            if abs(adjusted_total - total_line) < 2:
                prediction.totals_over_under = "push"
            else:
                prediction.totals_over_under = "over" if adjusted_total > total_line else "under"
        
        # Enhanced First Half Winner prediction
        first_half_factor = self._calculate_first_half_tendency(game_data, traits)
        
        if market_trust > 0.6:
            # Trust market indicators for first half
            if game_data.get('first_half_total', 0) > 22:
                # High-scoring first half expected
                prediction.first_half_winner = prediction.winner_prediction
            else:
                # Conservative first half
                prediction.first_half_winner = "home"  # Slight home bias
        else:
            # Use personality-driven first half prediction
            first_half_prob = 0.5 + first_half_factor
            prediction.first_half_winner = "home" if first_half_prob > 0.5 else "away"
        
        # Enhanced Highest Scoring Quarter prediction
        quarter_personality = self._predict_highest_scoring_quarter(game_data, traits)
        prediction.highest_scoring_quarter = quarter_personality
        
        # Enhanced betting market confidence calculations
        spread_confidence = 0.5 + contrarian_tendency * 0.2 + abs(spread_value) * 0.05
        total_confidence = 0.45 + market_trust * 0.25 + abs(total_difference) * 0.03
        
        prediction.confidence_by_category['against_the_spread'] = min(0.95, spread_confidence)
        prediction.confidence_by_category['totals_over_under'] = min(0.95, total_confidence)
        prediction.confidence_by_category['first_half_winner'] = 0.4 + market_trust * 0.2
        prediction.confidence_by_category['highest_scoring_quarter'] = 0.3 + value_seeking * 0.25
    
    def _calculate_weather_impact_on_totals(self, weather: Dict[str, Any]) -> float:
        """Calculate weather impact on game totals"""
        if not weather:
            return 0.0
        
        impact = 0.0
        temp = weather.get('temperature', 70)
        wind = weather.get('wind_speed', 5)
        precipitation = weather.get('precipitation', 0)
        
        # Temperature impact
        if temp < 35:
            impact -= 3.5  # Cold weather reduces scoring
        elif temp > 85:
            impact -= 1.5  # Very hot weather can reduce efficiency
        
        # Wind impact
        if wind > 15:
            impact -= wind * 0.15  # High winds reduce passing efficiency
        
        # Precipitation impact
        if precipitation > 0.3:
            impact -= 4.0  # Rain/snow significantly reduces scoring
        
        return impact
    
    def _calculate_pace_factor(self, game_data: Dict[str, Any], traits: Dict[str, Any]) -> float:
        """Calculate pace of play factor"""
        # Base pace factor
        pace_factor = 1.0
        
        # Team pace adjustments
        team_stats = game_data.get('team_stats', {})
        home_pace = team_stats.get('home', {}).get('pace_factor', 1.0)
        away_pace = team_stats.get('away', {}).get('pace_factor', 1.0)
        
        avg_pace = (home_pace + away_pace) / 2
        
        # Personality adjustment
        chaos_comfort = self._get_trait_value(traits, 'chaos_comfort', 0.5)
        if chaos_comfort > 0.7:
            # Chaos lovers expect faster pace
            pace_factor = avg_pace * 1.05
        elif chaos_comfort < 0.3:
            # Conservative experts expect slower pace
            pace_factor = avg_pace * 0.95
        else:
            pace_factor = avg_pace
        
        return max(0.8, min(1.3, pace_factor))
    
    def _calculate_first_half_tendency(self, game_data: Dict[str, Any], traits: Dict[str, Any]) -> float:
        """Calculate first half performance tendency"""
        # Coaching adjustments
        coaching = game_data.get('coaching', {})
        home_first_half_adj = coaching.get('home_first_half_performance', 0)
        away_first_half_adj = coaching.get('away_first_half_performance', 0)
        
        base_adjustment = (home_first_half_adj - away_first_half_adj) / 100
        
        # Personality influence
        analytics_trust = self._get_trait_value(traits, 'analytics_trust', 0.5)
        if analytics_trust > 0.7:
            # Analytical experts trust historical first half data
            return base_adjustment
        else:
            # Intuitive experts add randomness
            intuitive_factor = (random.random() - 0.5) * 0.2
            return base_adjustment + intuitive_factor
    
    def _predict_highest_scoring_quarter(self, game_data: Dict[str, Any], traits: Dict[str, Any]) -> str:
        """Predict highest scoring quarter based on personality"""
        confidence_level = self._get_trait_value(traits, 'confidence_level', 0.5)
        chaos_comfort = self._get_trait_value(traits, 'chaos_comfort', 0.5)
        
        if confidence_level > 0.7 and chaos_comfort > 0.6:
            # Confident chaos lovers predict dramatic 4th quarter
            return "Q4"
        elif confidence_level < 0.3:
            # Low confidence experts predict safe middle quarters
            return random.choice(["Q2", "Q3"])
        else:
            # Balanced prediction based on game flow expectations
            return "Q3"  # Third quarter often high scoring due to adjustments
    
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
        """Enhanced personality trait value extraction with validation"""
        trait = traits.get(trait_name)
        if trait is None:
            return default
        
        # Handle PersonalityTrait objects
        if hasattr(trait, 'value'):
            value = trait.value
        # Handle direct values
        elif isinstance(trait, (int, float)):
            value = float(trait)
        else:
            return default
        
        # Validate and clamp value to 0.0-1.0 range
        return max(0.0, min(1.0, value))
    
    def _apply_personality_amplification(
        self, 
        base_value: float, 
        trait_value: float, 
        amplification_factor: float = 1.0
    ) -> float:
        """Apply personality trait amplification to base values"""
        # Calculate deviation from neutral (0.5)
        trait_deviation = trait_value - 0.5
        
        # Apply amplification
        amplified_deviation = trait_deviation * amplification_factor
        
        # Apply to base value
        result = base_value + (amplified_deviation * 0.3)  # Max 30% adjustment
        
        return max(0.0, min(1.0, result))
    
    def _calculate_confidence_multiplier(self, traits: Dict[str, Any]) -> float:
        """Calculate personality-based confidence multiplier"""
        confidence_level = self._get_trait_value(traits, 'confidence_level', 0.5)
        risk_tolerance = self._get_trait_value(traits, 'risk_tolerance', 0.5)
        analytics_trust = self._get_trait_value(traits, 'analytics_trust', 0.5)
        
        # Base multiplier from confidence level
        base_multiplier = 0.7 + (confidence_level * 0.6)  # Range: 0.7-1.3
        
        # Risk tolerance adjustment
        risk_adjustment = (risk_tolerance - 0.5) * 0.2  # ±0.1 adjustment
        
        # Analytics trust adjustment (analytical experts more confident in data)
        analytics_adjustment = (analytics_trust - 0.5) * 0.15  # ±0.075 adjustment
        
        final_multiplier = base_multiplier + risk_adjustment + analytics_adjustment
        
        return max(0.5, min(1.5, final_multiplier))
    
    def _get_personality_biases(self, traits: Dict[str, Any]) -> Dict[str, float]:
        """Extract and calculate personality-specific biases"""
        return {
            'home_bias': self._calculate_home_bias(traits),
            'underdog_bias': self._calculate_underdog_bias(traits),
            'over_bias': self._calculate_scoring_bias(traits),
            'variance_bias': self._calculate_variance_bias(traits),
            'contrarian_bias': self._get_trait_value(traits, 'contrarian_tendency', 0.5),
            'weather_sensitivity': self._calculate_weather_sensitivity(traits),
            'injury_sensitivity': self._calculate_injury_sensitivity(traits)
        }
    
    def _calculate_home_bias(self, traits: Dict[str, Any]) -> float:
        """Calculate home field advantage bias based on personality"""
        conservatism = 1.0 - self._get_trait_value(traits, 'risk_tolerance', 0.5)
        tradition_respect = self._get_trait_value(traits, 'tradition_respect', 0.5)
        
        # Conservative and traditional experts favor home teams more
        home_bias = 0.5 + (conservatism * 0.15) + (tradition_respect * 0.1)
        
        return max(0.3, min(0.8, home_bias))
    
    def _calculate_underdog_bias(self, traits: Dict[str, Any]) -> float:
        """Calculate underdog preference based on personality"""
        contrarian_tendency = self._get_trait_value(traits, 'contrarian_tendency', 0.5)
        value_seeking = self._get_trait_value(traits, 'value_seeking', 0.5)
        risk_tolerance = self._get_trait_value(traits, 'risk_tolerance', 0.5)
        
        # Contrarians and value seekers favor underdogs
        underdog_bias = contrarian_tendency * 0.4 + value_seeking * 0.3 + risk_tolerance * 0.2
        
        return max(0.0, min(0.8, underdog_bias))
    
    def _calculate_scoring_bias(self, traits: Dict[str, Any]) -> float:
        """Calculate over/under scoring bias"""
        optimism = self._get_trait_value(traits, 'optimism', 0.5)
        chaos_comfort = self._get_trait_value(traits, 'chaos_comfort', 0.5)
        
        # Optimistic and chaos-comfortable experts lean toward overs
        over_bias = optimism * 0.3 + chaos_comfort * 0.2
        
        return max(0.0, min(0.6, over_bias))
    
    def _calculate_variance_bias(self, traits: Dict[str, Any]) -> float:
        """Calculate prediction variance preference"""
        risk_tolerance = self._get_trait_value(traits, 'risk_tolerance', 0.5)
        chaos_comfort = self._get_trait_value(traits, 'chaos_comfort', 0.5)
        confidence_level = self._get_trait_value(traits, 'confidence_level', 0.5)
        
        # High-risk, chaos-comfortable, confident experts make more extreme predictions
        variance_bias = risk_tolerance * 0.4 + chaos_comfort * 0.3 + confidence_level * 0.2
        
        return max(0.0, min(1.0, variance_bias))
    
    def _calculate_weather_sensitivity(self, traits: Dict[str, Any]) -> float:
        """Calculate sensitivity to weather conditions"""
        analytics_trust = self._get_trait_value(traits, 'analytics_trust', 0.5)
        attention_to_detail = self._get_trait_value(traits, 'attention_to_detail', 0.5)
        
        # Analytical and detail-oriented experts more sensitive to weather
        weather_sensitivity = analytics_trust * 0.4 + attention_to_detail * 0.3 + 0.3
        
        return max(0.3, min(1.0, weather_sensitivity))
    
    def _calculate_injury_sensitivity(self, traits: Dict[str, Any]) -> float:
        """Calculate sensitivity to injury reports"""
        analytics_trust = self._get_trait_value(traits, 'analytics_trust', 0.5)
        pessimism = 1.0 - self._get_trait_value(traits, 'optimism', 0.5)
        
        # Analytical and pessimistic experts more sensitive to injuries
        injury_sensitivity = analytics_trust * 0.4 + pessimism * 0.3 + 0.3
        
        return max(0.2, min(1.0, injury_sensitivity))