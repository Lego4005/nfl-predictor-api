"""
Transformer for SportsDataIO API responses.
Converts SportsDataIO data to standard format for prop bets and fantasy picks.
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

from .base_transformer import (
    BaseTransformer,
    StandardGamePrediction,
    StandardATSPrediction,
    StandardTotalsPrediction,
    StandardPropBet,
    StandardFantasyPick
)

logger = logging.getLogger(__name__)


class SportsDataTransformer(BaseTransformer):
    """
    Transformer for SportsDataIO API data.
    Handles player props, DFS salaries, and fantasy projections.
    """
    
    def __init__(self):
        super().__init__("sportsdata_io")
    
    def _determine_prop_pick(self, prop_type: str, line: float, player_stats: Dict[str, Any] = None) -> str:
        """
        Determine Over/Under pick for prop bet.
        In production, this would use ML models and historical data.
        """
        # Simplified logic for demonstration
        prop_lower = prop_type.lower()
        
        if "passing" in prop_lower and "yard" in prop_lower:
            # QB passing yards - favor Over for lines under 280
            return "Over" if line < 280 else "Under"
        elif "rushing" in prop_lower and "yard" in prop_lower:
            # RB rushing yards - favor Over for lines under 80
            return "Over" if line < 80 else "Under"
        elif "receiving" in prop_lower and "yard" in prop_lower:
            # WR receiving yards - favor Over for lines under 70
            return "Over" if line < 70 else "Under"
        elif "reception" in prop_lower:
            # Receptions - favor Over for lines under 6
            return "Over" if line < 6 else "Under"
        elif "touchdown" in prop_lower:
            # Touchdowns - favor Under (TDs are hard to predict)
            return "Under"
        elif "fantasy" in prop_lower:
            # Fantasy points - favor Over for lines under 15
            return "Over" if line < 15 else "Under"
        else:
            return "Over"  # Default
    
    def _calculate_prop_confidence(self, prop_type: str, line: float, pick: str) -> float:
        """Calculate confidence for prop bet based on type and line"""
        base_confidence = 0.58
        
        prop_lower = prop_type.lower()
        
        # Adjust confidence based on prop type
        if "passing" in prop_lower:
            # Passing yards are more predictable
            confidence_boost = 0.05
        elif "rushing" in prop_lower:
            # Rushing yards are moderately predictable
            confidence_boost = 0.03
        elif "receiving" in prop_lower:
            # Receiving yards are less predictable
            confidence_boost = 0.02
        elif "reception" in prop_lower:
            # Receptions are fairly predictable
            confidence_boost = 0.04
        elif "touchdown" in prop_lower:
            # Touchdowns are very unpredictable
            confidence_boost = -0.05
        else:
            confidence_boost = 0.01
        
        # Adjust based on line value (extreme lines are often easier)
        if line > 100:  # High lines
            line_boost = 0.02
        elif line < 10:  # Low lines
            line_boost = 0.03
        else:
            line_boost = 0.01
        
        return min(base_confidence + confidence_boost + line_boost, 0.85)
    
    def _calculate_value_score(self, salary: int, projected_points: float) -> float:
        """Calculate fantasy value score (points per $1000 of salary)"""
        if salary <= 0:
            return 0.0
        return (projected_points / salary) * 1000
    
    def _normalize_position(self, position: str) -> str:
        """Normalize position strings to standard format"""
        position_mapping = {
            "QB": "QB",
            "RB": "RB", 
            "WR": "WR",
            "TE": "TE",
            "K": "K",
            "DEF": "DST",
            "DST": "DST",
            "D/ST": "DST"
        }
        
        return position_mapping.get(position.upper(), position.upper())
    
    def transform_game_predictions(self, raw_data: List[Dict[str, Any]]) -> List[StandardGamePrediction]:
        """
        Transform SportsDataIO data to game predictions.
        Note: SportsDataIO doesn't typically provide game predictions,
        so this returns empty list. Use The Odds API for game predictions.
        """
        logger.info("SportsDataIO doesn't provide game predictions - use The Odds API instead")
        return []
    
    def transform_ats_predictions(self, raw_data: List[Dict[str, Any]]) -> List[StandardATSPrediction]:
        """
        Transform SportsDataIO data to ATS predictions.
        Note: SportsDataIO doesn't typically provide ATS predictions,
        so this returns empty list. Use The Odds API for ATS predictions.
        """
        logger.info("SportsDataIO doesn't provide ATS predictions - use The Odds API instead")
        return []
    
    def transform_totals_predictions(self, raw_data: List[Dict[str, Any]]) -> List[StandardTotalsPrediction]:
        """
        Transform SportsDataIO data to totals predictions.
        Note: SportsDataIO doesn't typically provide totals predictions,
        so this returns empty list. Use The Odds API for totals predictions.
        """
        logger.info("SportsDataIO doesn't provide totals predictions - use The Odds API instead")
        return []
    
    def transform_prop_bets(self, raw_data: List[Dict[str, Any]]) -> List[StandardPropBet]:
        """Transform SportsDataIO prop data to standard prop bets format"""
        prop_bets = []
        
        for prop_data in raw_data:
            try:
                # Validate required fields
                required_fields = ["PlayerName", "MarketName", "Line"]
                if not self._validate_required_fields(prop_data, required_fields):
                    continue
                
                player = prop_data["PlayerName"]
                prop_type = prop_data["MarketName"]
                line = self._safe_float_conversion(prop_data["Line"])
                
                if line <= 0:
                    continue
                
                # Extract team information
                team = self._parse_team_abbreviation(prop_data.get("Team", ""))
                opponent = self._parse_team_abbreviation(prop_data.get("Opponent", ""))
                
                # Determine pick and confidence
                pick = self._determine_prop_pick(prop_type, line)
                confidence = self._calculate_prop_confidence(prop_type, line, pick)
                
                # Determine units based on prop type
                prop_lower = prop_type.lower()
                if "yard" in prop_lower:
                    units = "yds"
                elif "reception" in prop_lower:
                    units = "rec"
                elif "touchdown" in prop_lower:
                    units = "td"
                elif "fantasy" in prop_lower or "point" in prop_lower:
                    units = "pts"
                else:
                    units = "pts"
                
                bookmaker = prop_data.get("Sportsbook", "SportsDataIO")
                
                prop_bet = StandardPropBet(
                    player=player,
                    prop_type=prop_type,
                    units=units,
                    line=line,
                    pick=pick,
                    confidence=confidence,
                    bookmaker=bookmaker,
                    team=team,
                    opponent=opponent,
                    source=self.source_name,
                    timestamp=self.timestamp
                )
                
                prop_bets.append(prop_bet)
                
            except Exception as e:
                logger.warning(f"Failed to transform prop bet: {str(e)}")
                continue
        
        # Sort by confidence and return top props
        prop_bets.sort(key=lambda x: x.confidence, reverse=True)
        
        logger.info(f"Transformed {len(prop_bets)} prop bets from {self.source_name}")
        return prop_bets
    
    def transform_fantasy_picks(self, raw_data: List[Dict[str, Any]]) -> List[StandardFantasyPick]:
        """Transform SportsDataIO fantasy data to standard fantasy picks format"""
        fantasy_picks = []
        
        for player_data in raw_data:
            try:
                # Validate required fields
                required_fields = ["Name", "Position"]
                if not self._validate_required_fields(player_data, required_fields):
                    continue
                
                player = player_data["Name"]
                position = self._normalize_position(player_data["Position"])
                
                # Extract salary data (try multiple DFS sites)
                salary = 0
                salary_fields = ["DraftKingsSalary", "FanDuelSalary", "SuperDraftSalary", "Salary"]
                for field in salary_fields:
                    salary = self._safe_int_conversion(player_data.get(field, 0))
                    if salary > 0:
                        break
                
                if salary <= 0:
                    continue  # Skip players without salary data
                
                # Extract projected points (try multiple sources)
                projected_points = 0.0
                points_fields = [
                    "FantasyPointsDraftKings", 
                    "FantasyPointsFanDuel",
                    "FantasyPoints",
                    "ProjectedFantasyPoints"
                ]
                for field in points_fields:
                    projected_points = self._safe_float_conversion(player_data.get(field, 0))
                    if projected_points > 0:
                        break
                
                if projected_points <= 0:
                    continue  # Skip players without projections
                
                # Calculate value score
                value_score = self._calculate_value_score(salary, projected_points)
                
                fantasy_pick = StandardFantasyPick(
                    player=player,
                    position=position,
                    salary=salary,
                    projected_points=projected_points,
                    value_score=value_score,
                    source=self.source_name,
                    timestamp=self.timestamp
                )
                
                fantasy_picks.append(fantasy_pick)
                
            except Exception as e:
                logger.warning(f"Failed to transform fantasy pick: {str(e)}")
                continue
        
        # Sort by value score and return top picks
        fantasy_picks.sort(key=lambda x: x.value_score, reverse=True)
        
        logger.info(f"Transformed {len(fantasy_picks)} fantasy picks from {self.source_name}")
        return fantasy_picks