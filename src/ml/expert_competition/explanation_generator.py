"""
Explanation Generator
Generates natural language explanations for AI Council consensus decisions
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime
import logging

from .voting_consensus import ConsensusResult, WeightedPrediction

logger = logging.getLogger(__name__)

@dataclass
class ExplanationContext:
    """Context information for generating explanations"""
    game_data: Dict[str, Any]
    council_experts: List[Any]
    individual_predictions: Dict[str, Any]
    consensus_results: Dict[str, ConsensusResult]
    expert_weights: Dict[str, float]

class ExplanationGenerator:
    """Generates natural language explanations for AI Council decisions"""
    
    def __init__(self):
        self.explanation_templates = self._load_explanation_templates()
    
    def _load_explanation_templates(self) -> Dict[str, Dict[str, str]]:
        """Load explanation templates for different prediction categories"""
        return {
            'winner_prediction': {
                'high_consensus': "The AI Council reaches a strong consensus on {consensus_value} with {agreement_level:.0%} agreement. {top_experts} all favor this outcome.",
                'moderate_consensus': "The AI Council leans toward {consensus_value} with {agreement_level:.0%} agreement, though there is some disagreement among members.",
                'low_consensus': "The AI Council is divided on this prediction, with {consensus_value} receiving slight preference at {agreement_level:.0%} agreement.",
                'confidence_high': "The council shows high confidence in this prediction ({confidence_score:.0%}).",
                'confidence_moderate': "The council has moderate confidence in this prediction ({confidence_score:.0%}).",
                'confidence_low': "The council expresses low confidence in this prediction ({confidence_score:.0%})."
            },
            'exact_score': {
                'high_consensus': "The AI Council predicts a final score near {consensus_value:.1f} with strong agreement ({agreement_level:.0%}).",
                'moderate_consensus': "The AI Council estimates {consensus_value:.1f} with moderate consensus ({agreement_level:.0%}).",
                'low_consensus': "Score predictions vary significantly, with the weighted average at {consensus_value:.1f}.",
                'range_narrow': "Expert predictions cluster tightly around this value.",
                'range_wide': "Expert predictions show significant variation, indicating uncertainty."
            },
            'against_the_spread': {
                'unanimous': "All council members agree on {consensus_value} against the spread.",
                'majority': "The majority of the council ({agreement_level:.0%}) favors {consensus_value} against the spread.",
                'split': "The council is closely divided on the spread, with {consensus_value} holding a slight edge."
            },
            'totals_over_under': {
                'unanimous': "The council unanimously predicts the {consensus_value} on the total.",
                'majority': "The council heavily favors the {consensus_value} ({agreement_level:.0%} agreement).",
                'split': "The council is split on the total, with the {consensus_value} holding a narrow advantage."
            }
        }
    
    def generate_comprehensive_explanation(
        self,
        context: ExplanationContext
    ) -> Dict[str, str]:
        """Generate comprehensive explanation for all AI Council decisions"""
        try:
            explanations = {}
            
            # Generate explanation for each consensus result
            for category, consensus in context.consensus_results.items():
                if consensus.consensus_value is not None:
                    explanation = self._generate_category_explanation(
                        category, consensus, context
                    )
                    explanations[category] = explanation
            
            # Generate overall summary
            explanations['overall_summary'] = self._generate_overall_summary(context)
            
            # Generate expert spotlight
            explanations['expert_spotlight'] = self._generate_expert_spotlight(context)
            
            # Generate key factors
            explanations['key_factors'] = self._generate_key_factors_explanation(context)
            
            return explanations
            
        except Exception as e:
            logger.error(f"Failed to generate comprehensive explanation: {e}")
            return {'error': f"Could not generate explanation: {e}"}
    
    def _generate_category_explanation(
        self,
        category: str,
        consensus: ConsensusResult,
        context: ExplanationContext
    ) -> str:
        """Generate explanation for a specific prediction category"""
        try:
            # Get templates for this category
            category_key = self._map_category_to_template_key(category)
            templates = self.explanation_templates.get(category_key, {})
            
            if not templates:
                return self._generate_generic_explanation(category, consensus, context)
            
            # Determine consensus strength
            agreement_level = consensus.agreement_level
            confidence_score = consensus.confidence_score
            
            # Build explanation parts
            explanation_parts = []
            
            # Main consensus statement
            if agreement_level >= 0.8:
                template = templates.get('high_consensus', '')
            elif agreement_level >= 0.6:
                template = templates.get('moderate_consensus', '')
            else:
                template = templates.get('low_consensus', '')
            
            if template:
                # Get top supporting experts
                top_experts = self._get_top_supporting_experts(consensus, context, limit=2)
                
                main_statement = template.format(
                    consensus_value=consensus.consensus_value,
                    agreement_level=agreement_level,
                    confidence_score=confidence_score,
                    top_experts=top_experts
                )
                explanation_parts.append(main_statement)
            
            # Add confidence qualifier
            if confidence_score >= 0.75:
                conf_template = templates.get('confidence_high', '')
            elif confidence_score >= 0.55:
                conf_template = templates.get('confidence_moderate', '')
            else:
                conf_template = templates.get('confidence_low', '')
            
            if conf_template:
                confidence_statement = conf_template.format(
                    confidence_score=confidence_score
                )
                explanation_parts.append(confidence_statement)
            
            # Add specific insights based on category
            specific_insight = self._generate_category_specific_insight(
                category, consensus, context
            )
            if specific_insight:
                explanation_parts.append(specific_insight)
            
            return ' '.join(explanation_parts)
            
        except Exception as e:
            logger.error(f"Failed to generate explanation for {category}: {e}")
            return f"AI Council prediction: {consensus.consensus_value}"
    
    def _generate_generic_explanation(
        self,
        category: str,
        consensus: ConsensusResult,
        context: ExplanationContext
    ) -> str:
        """Generate generic explanation when no specific template exists"""
        try:
            agreement_level = consensus.agreement_level
            confidence_score = consensus.confidence_score
            
            if agreement_level >= 0.8:
                agreement_desc = "strong consensus"
            elif agreement_level >= 0.6:
                agreement_desc = "moderate agreement"
            else:
                agreement_desc = "divided opinion"
            
            if confidence_score >= 0.7:
                confidence_desc = "high confidence"
            elif confidence_score >= 0.5:
                confidence_desc = "moderate confidence"
            else:
                confidence_desc = "low confidence"
            
            return (f"The AI Council predicts {consensus.consensus_value} for {category.replace('_', ' ')} "
                   f"with {agreement_desc} ({agreement_level:.0%}) and {confidence_desc} "
                   f"({confidence_score:.0%}).")
            
        except Exception as e:
            logger.error(f"Failed to generate generic explanation: {e}")
            return f"AI Council prediction: {consensus.consensus_value}"
    
    def _generate_overall_summary(self, context: ExplanationContext) -> str:
        """Generate overall summary of AI Council decisions"""
        try:
            summary_parts = []
            
            # Game context
            game_data = context.game_data
            home_team = game_data.get('home_team', 'Home Team').replace('_', ' ').title()
            away_team = game_data.get('away_team', 'Away Team').replace('_', ' ').title()
            
            summary_parts.append(f"AI Council Analysis: {away_team} @ {home_team}")
            
            # Main prediction
            winner_consensus = context.consensus_results.get('winner_prediction')
            if winner_consensus and winner_consensus.consensus_value:
                winner = "home team" if winner_consensus.consensus_value == 'home' else "away team"
                confidence = winner_consensus.confidence_score
                agreement = winner_consensus.agreement_level
                
                if agreement >= 0.8:
                    summary_parts.append(f"The council strongly favors the {winner} with {confidence:.0%} confidence.")
                elif agreement >= 0.6:
                    summary_parts.append(f"The council leans toward the {winner} with {confidence:.0%} confidence.")
                else:
                    summary_parts.append(f"The council is divided but slightly favors the {winner}.")
            
            # Score prediction
            score_home = context.consensus_results.get('exact_score_home')
            score_away = context.consensus_results.get('exact_score_away')
            if score_home and score_away and score_home.consensus_value is not None and score_away.consensus_value is not None:
                predicted_score = f"{score_home.consensus_value:.0f}-{score_away.consensus_value:.0f}"
                summary_parts.append(f"Predicted final score: {predicted_score}.")
            
            # Key betting lines
            spread_consensus = context.consensus_results.get('against_the_spread')
            total_consensus = context.consensus_results.get('totals_over_under')
            
            betting_info = []
            if spread_consensus and spread_consensus.consensus_value:
                betting_info.append(f"spread: {spread_consensus.consensus_value}")
            if total_consensus and total_consensus.consensus_value:
                betting_info.append(f"total: {total_consensus.consensus_value}")
            
            if betting_info:
                summary_parts.append(f"Betting recommendations: {', '.join(betting_info)}.")
            
            return ' '.join(summary_parts)
            
        except Exception as e:
            logger.error(f"Failed to generate overall summary: {e}")
            return "AI Council has provided predictions for this game."
    
    def _generate_expert_spotlight(self, context: ExplanationContext) -> str:
        """Generate spotlight on key expert contributions"""
        try:
            spotlight_parts = []
            
            # Find most influential expert (highest average weight)
            expert_avg_weights = {}
            for expert_id, weight in context.expert_weights.items():
                expert_avg_weights[expert_id] = weight
            
            if expert_avg_weights:
                top_expert_id = max(expert_avg_weights.keys(), key=lambda k: expert_avg_weights[k])
                top_expert = next((e for e in context.council_experts if e.expert_id == top_expert_id), None)
                
                if top_expert:
                    expert_name = getattr(top_expert, 'name', top_expert_id)
                    weight = expert_avg_weights[top_expert_id]
                    
                    spotlight_parts.append(f"Leading voice: {expert_name} carries the highest influence "
                                         f"({weight:.0%}) due to strong recent performance.")
            
            # Find most contrarian expert
            contrarian_expert = self._find_most_contrarian_expert(context)
            if contrarian_expert:
                spotlight_parts.append(f"Contrarian perspective: {contrarian_expert} provides "
                                     f"alternative viewpoints on key predictions.")
            
            # Find consensus driver
            consensus_driver = self._find_consensus_driver(context)
            if consensus_driver:
                spotlight_parts.append(f"Consensus builder: {consensus_driver} aligns with "
                                     f"majority opinion across multiple categories.")
            
            return ' '.join(spotlight_parts) if spotlight_parts else "All council members contribute valuable insights."
            
        except Exception as e:
            logger.error(f"Failed to generate expert spotlight: {e}")
            return "Council members bring diverse expertise to the analysis."
    
    def _generate_key_factors_explanation(self, context: ExplanationContext) -> str:
        """Generate explanation of key factors influencing decisions"""
        try:
            factors = []
            game_data = context.game_data
            
            # Weather impact
            weather = game_data.get('weather', {})
            temp = weather.get('temperature', 70)
            wind = weather.get('wind_speed', 0)
            precipitation = weather.get('precipitation', 0)
            
            if temp < 35 or temp > 90:
                factors.append(f"extreme temperature ({temp}°F)")
            if wind > 15:
                factors.append(f"high winds ({wind} mph)")
            if precipitation > 0.3:
                factors.append("precipitation expected")
            
            # Injury impact
            injuries = game_data.get('injuries', {})
            significant_injuries = 0
            for team_injuries in injuries.values():
                for injury in team_injuries:
                    if isinstance(injury, dict) and injury.get('is_starter') and injury.get('severity') in ['out', 'doubtful']:
                        significant_injuries += 1
            
            if significant_injuries > 0:
                factors.append(f"{significant_injuries} key player injury concerns")
            
            # Rest/travel
            travel = game_data.get('travel', {})
            rest_difference = abs(travel.get('home_rest_days', 7) - travel.get('away_rest_days', 7))
            if rest_difference >= 2:
                factors.append("significant rest advantage")
            
            # Divisional rivalry
            if game_data.get('is_divisional'):
                factors.append("divisional rivalry dynamics")
            
            # Home field advantage
            venue = game_data.get('venue', {})
            crowd_factor = venue.get('crowd_factor', 1.0)
            if crowd_factor > 1.2:
                factors.append("strong home field advantage")
            
            if factors:
                return f"Key factors considered: {', '.join(factors)}."
            else:
                return "Standard game conditions with no significant external factors."
                
        except Exception as e:
            logger.error(f"Failed to generate key factors explanation: {e}")
            return "Multiple factors analyzed in reaching consensus."
    
    def _map_category_to_template_key(self, category: str) -> str:
        """Map prediction category to explanation template key"""
        mapping = {
            'winner_prediction': 'winner_prediction',
            'exact_score_home': 'exact_score',
            'exact_score_away': 'exact_score',
            'margin_of_victory': 'exact_score',
            'against_the_spread': 'against_the_spread',
            'totals_over_under': 'totals_over_under'
        }
        return mapping.get(category, 'generic')
    
    def _get_top_supporting_experts(
        self,
        consensus: ConsensusResult,
        context: ExplanationContext,
        limit: int = 2
    ) -> str:
        """Get names of top experts supporting the consensus"""
        try:
            if 'individual_predictions' not in consensus.breakdown:
                return ""
            
            # Sort experts by weight for this prediction
            individual_preds = consensus.breakdown['individual_predictions']
            supporting_experts = [
                pred for pred in individual_preds
                if pred.get('value') == consensus.consensus_value
            ]
            
            supporting_experts.sort(key=lambda x: x.get('weight', 0), reverse=True)
            
            # Get expert names
            expert_names = []
            for pred in supporting_experts[:limit]:
                expert_id = pred.get('expert_id')
                expert = next((e for e in context.council_experts if e.expert_id == expert_id), None)
                if expert:
                    name = getattr(expert, 'name', expert_id)
                    expert_names.append(name)
            
            if len(expert_names) == 1:
                return expert_names[0]
            elif len(expert_names) == 2:
                return f"{expert_names[0]} and {expert_names[1]}"
            else:
                return "key council members"
                
        except Exception as e:
            logger.error(f"Failed to get top supporting experts: {e}")
            return "council members"
    
    def _generate_category_specific_insight(
        self,
        category: str,
        consensus: ConsensusResult,
        context: ExplanationContext
    ) -> Optional[str]:
        """Generate category-specific insights"""
        try:
            if category == 'winner_prediction':
                return self._generate_winner_insight(consensus, context)
            elif category in ['exact_score_home', 'exact_score_away']:
                return self._generate_score_insight(consensus, context)
            elif category == 'against_the_spread':
                return self._generate_spread_insight(consensus, context)
            elif category == 'totals_over_under':
                return self._generate_total_insight(consensus, context)
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to generate category-specific insight for {category}: {e}")
            return None
    
    def _generate_winner_insight(self, consensus: ConsensusResult, context: ExplanationContext) -> str:
        """Generate winner prediction insight"""
        game_data = context.game_data
        spread = game_data.get('spread', 0)
        
        if consensus.consensus_value == 'home' and spread < -3:
            return "This aligns with the betting market's strong preference for the home team."
        elif consensus.consensus_value == 'away' and spread > 3:
            return "This supports the road team despite unfavorable betting odds."
        else:
            return "This prediction reflects careful analysis of team matchups."
    
    def _generate_score_insight(self, consensus: ConsensusResult, context: ExplanationContext) -> str:
        """Generate score prediction insight"""
        if 'statistics' in consensus.breakdown:
            stats = consensus.breakdown['statistics']
            std_dev = stats.get('std_dev', 0)
            
            if std_dev < 3:
                return "Expert predictions show strong convergence on the scoring expectation."
            elif std_dev > 7:
                return "Significant variance in scoring predictions indicates uncertainty."
        
        return "Score prediction reflects consensus analysis of offensive and defensive capabilities."
    
    def _generate_spread_insight(self, consensus: ConsensusResult, context: ExplanationContext) -> str:
        """Generate spread prediction insight"""
        game_data = context.game_data
        spread = game_data.get('spread', 0)
        
        if consensus.consensus_value == 'home' and spread > 0:
            return "The council sees value in backing the home underdog."
        elif consensus.consensus_value == 'away' and spread < 0:
            return "The council believes the road team will cover the spread."
        else:
            return "The spread recommendation aligns with market expectations."
    
    def _generate_total_insight(self, consensus: ConsensusResult, context: ExplanationContext) -> str:
        """Generate total (over/under) prediction insight"""
        game_data = context.game_data
        total_line = game_data.get('total', 45)
        
        if consensus.consensus_value == 'over':
            return f"The council expects a high-scoring game exceeding {total_line} points."
        elif consensus.consensus_value == 'under':
            return f"The council anticipates a lower-scoring game staying under {total_line} points."
        else:
            return "The total prediction reflects balanced offensive and defensive expectations."
    
    def _find_most_contrarian_expert(self, context: ExplanationContext) -> Optional[str]:
        """Find the expert with most contrarian positions"""
        try:
            expert_contrarian_scores = {}
            
            for expert in context.council_experts:
                contrarian_tendency = getattr(expert, 'personality_traits', {}).get('contrarian_tendency', 0.5)
                if hasattr(contrarian_tendency, 'value'):
                    contrarian_tendency = contrarian_tendency.value
                expert_contrarian_scores[expert.expert_id] = contrarian_tendency
            
            if expert_contrarian_scores:
                most_contrarian_id = max(expert_contrarian_scores.keys(), 
                                       key=lambda k: expert_contrarian_scores[k])
                expert = next((e for e in context.council_experts if e.expert_id == most_contrarian_id), None)
                return getattr(expert, 'name', most_contrarian_id) if expert else None
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to find most contrarian expert: {e}")
            return None
    
    def _find_consensus_driver(self, context: ExplanationContext) -> Optional[str]:
        """Find the expert who most often aligns with consensus"""
        try:
            # This would require tracking consensus alignment over time
            # For now, return the expert with highest overall weight
            if context.expert_weights:
                consensus_driver_id = max(context.expert_weights.keys(), 
                                        key=lambda k: context.expert_weights[k])
                expert = next((e for e in context.council_experts if e.expert_id == consensus_driver_id), None)
                return getattr(expert, 'name', consensus_driver_id) if expert else None
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to find consensus driver: {e}")
            return None