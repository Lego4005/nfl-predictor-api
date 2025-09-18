"""
Advanced Analytics Service
Fetches premium analytics data including EPA, DVOA, success rates from SportsData.io
"""

import os
import requests
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import json
from dotenv import load_dotenv
import statistics

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

class AdvancedAnalyticsService:
    """Fetches advanced NFL analytics from SportsData.io"""

    def __init__(self):
        # API Keys from environment variables
        self.sportsdata_io_key = os.getenv('VITE_SPORTSDATA_IO_KEY', '')
        self.sportsdata_base = "https://api.sportsdata.io/v3/nfl"

        # Cache for expensive API calls
        self.cache = {}
        self.cache_ttl = 1800  # 30 minutes cache for analytics

        logger.info("📊 Advanced Analytics Service initialized")

    def get_team_epa_stats(self, team: str, season: int = 2024) -> Dict:
        """Get Expected Points Added (EPA) statistics for a team"""
        cache_key = f"epa_stats_{team}_{season}"

        if self._is_cached(cache_key):
            return self.cache[cache_key]['data']

        try:
            # Get advanced team stats
            url = f"{self.sportsdata_base}/stats/json/TeamSeasonStats/{season}"
            headers = {'Ocp-Apim-Subscription-Key': self.sportsdata_io_key}

            response = requests.get(url, headers=headers)
            response.raise_for_status()

            all_teams = response.json()

            # Find team stats
            team_stats = None
            for team_data in all_teams:
                if team_data.get('Team') == team:
                    team_stats = team_data
                    break

            if not team_stats:
                logger.warning(f"Team {team} not found in EPA stats")
                return {}

            # Calculate EPA metrics
            epa_data = {
                'team': team,
                'season': season,

                # Offensive EPA
                'offensive_epa_per_play': self._calculate_offensive_epa(team_stats),
                'passing_epa_per_play': self._calculate_passing_epa(team_stats),
                'rushing_epa_per_play': self._calculate_rushing_epa(team_stats),
                'red_zone_epa': self._calculate_red_zone_epa(team_stats),

                # Defensive EPA (opponents)
                'defensive_epa_per_play': self._calculate_defensive_epa(team_stats),
                'pass_defense_epa': self._calculate_pass_defense_epa(team_stats),
                'rush_defense_epa': self._calculate_rush_defense_epa(team_stats),

                # Situational EPA
                'first_down_epa': self._calculate_first_down_epa(team_stats),
                'second_down_epa': self._calculate_second_down_epa(team_stats),
                'third_down_epa': self._calculate_third_down_epa(team_stats),
                'fourth_down_epa': self._calculate_fourth_down_epa(team_stats),

                # Special situations
                'goal_to_go_epa': self._calculate_goal_to_go_epa(team_stats),
                'two_minute_drill_epa': self._calculate_two_minute_epa(team_stats),
                'late_game_epa': self._calculate_late_game_epa(team_stats),

                # EPA rankings (estimated)
                'offensive_epa_rank': self._estimate_epa_rank(self._calculate_offensive_epa(team_stats), 'offense'),
                'defensive_epa_rank': self._estimate_epa_rank(self._calculate_defensive_epa(team_stats), 'defense'),

                'last_updated': datetime.now().isoformat()
            }

            # Cache the results
            self._cache_data(cache_key, epa_data)

            logger.info(f"✅ Fetched EPA stats for {team}")
            return epa_data

        except Exception as e:
            logger.error(f"❌ Error fetching EPA stats: {e}")
            return {}

    def get_team_dvoa_metrics(self, team: str, season: int = 2024) -> Dict:
        """Get Defense-adjusted Value Over Average (DVOA) metrics"""
        cache_key = f"dvoa_stats_{team}_{season}"

        if self._is_cached(cache_key):
            return self.cache[cache_key]['data']

        try:
            # Get team stats for DVOA calculations
            url = f"{self.sportsdata_base}/stats/json/TeamSeasonStats/{season}"
            headers = {'Ocp-Apim-Subscription-Key': self.sportsdata_io_key}

            response = requests.get(url, headers=headers)
            response.raise_for_status()

            all_teams = response.json()

            # Find team stats
            team_stats = None
            for team_data in all_teams:
                if team_data.get('Team') == team:
                    team_stats = team_data
                    break

            if not team_stats:
                return {}

            # Calculate DVOA metrics
            dvoa_data = {
                'team': team,
                'season': season,

                # Overall DVOA
                'total_dvoa': self._calculate_total_dvoa(team_stats),
                'offensive_dvoa': self._calculate_offensive_dvoa(team_stats),
                'defensive_dvoa': self._calculate_defensive_dvoa(team_stats),
                'special_teams_dvoa': self._calculate_special_teams_dvoa(team_stats),

                # Offensive DVOA breakdown
                'passing_dvoa': self._calculate_passing_dvoa(team_stats),
                'rushing_dvoa': self._calculate_rushing_dvoa(team_stats),
                'first_down_dvoa': self._calculate_first_down_dvoa(team_stats),
                'second_down_dvoa': self._calculate_second_down_dvoa(team_stats),
                'third_down_dvoa': self._calculate_third_down_dvoa(team_stats),

                # Defensive DVOA breakdown
                'pass_defense_dvoa': self._calculate_pass_defense_dvoa(team_stats),
                'rush_defense_dvoa': self._calculate_rush_defense_dvoa(team_stats),
                'red_zone_defense_dvoa': self._calculate_red_zone_defense_dvoa(team_stats),

                # Situational DVOA
                'red_zone_dvoa': self._calculate_red_zone_dvoa(team_stats),
                'goal_line_dvoa': self._calculate_goal_line_dvoa(team_stats),
                'late_and_close_dvoa': self._calculate_late_close_dvoa(team_stats),

                # Variance metrics
                'offensive_consistency': self._calculate_offensive_consistency(team_stats),
                'defensive_consistency': self._calculate_defensive_consistency(team_stats),

                # Rankings (estimated)
                'total_dvoa_rank': self._estimate_dvoa_rank(self._calculate_total_dvoa(team_stats)),
                'offensive_dvoa_rank': self._estimate_dvoa_rank(self._calculate_offensive_dvoa(team_stats)),
                'defensive_dvoa_rank': self._estimate_dvoa_rank(self._calculate_defensive_dvoa(team_stats)),

                'last_updated': datetime.now().isoformat()
            }

            # Cache the results
            self._cache_data(cache_key, dvoa_data)

            logger.info(f"✅ Fetched DVOA metrics for {team}")
            return dvoa_data

        except Exception as e:
            logger.error(f"❌ Error fetching DVOA metrics: {e}")
            return {}

    def get_team_success_rates(self, team: str, season: int = 2024) -> Dict:
        """Get success rate metrics for a team"""
        cache_key = f"success_rates_{team}_{season}"

        if self._is_cached(cache_key):
            return self.cache[cache_key]['data']

        try:
            # Get detailed team stats
            url = f"{self.sportsdata_base}/stats/json/TeamSeasonStats/{season}"
            headers = {'Ocp-Apim-Subscription-Key': self.sportsdata_io_key}

            response = requests.get(url, headers=headers)
            response.raise_for_status()

            all_teams = response.json()

            # Find team stats
            team_stats = None
            for team_data in all_teams:
                if team_data.get('Team') == team:
                    team_stats = team_data
                    break

            if not team_stats:
                return {}

            # Calculate success rates
            success_data = {
                'team': team,
                'season': season,

                # Offensive success rates
                'overall_success_rate': self._calculate_overall_success_rate(team_stats),
                'passing_success_rate': self._calculate_passing_success_rate(team_stats),
                'rushing_success_rate': self._calculate_rushing_success_rate(team_stats),

                # Down-specific success rates
                'first_down_success_rate': self._calculate_first_down_success(team_stats),
                'second_down_success_rate': self._calculate_second_down_success(team_stats),
                'third_down_success_rate': team_stats.get('ThirdDownPercentage', 0) / 100,
                'fourth_down_success_rate': team_stats.get('FourthDownPercentage', 0) / 100,

                # Situational success rates
                'red_zone_success_rate': team_stats.get('RedZonePercentage', 0) / 100,
                'goal_line_success_rate': self._calculate_goal_line_success(team_stats),
                'short_yardage_success_rate': self._calculate_short_yardage_success(team_stats),
                'explosive_play_rate': self._calculate_explosive_play_rate(team_stats),

                # Defensive success rates (preventing opponent success)
                'defensive_success_rate': self._calculate_defensive_success_rate(team_stats),
                'pass_defense_success_rate': self._calculate_pass_defense_success(team_stats),
                'rush_defense_success_rate': self._calculate_rush_defense_success(team_stats),

                # Advanced metrics
                'early_down_success_rate': self._calculate_early_down_success(team_stats),
                'late_down_success_rate': self._calculate_late_down_success(team_stats),
                'scoring_drive_rate': self._calculate_scoring_drive_rate(team_stats),
                'three_and_out_rate': self._calculate_three_and_out_rate(team_stats),

                # Rankings (estimated)
                'overall_success_rank': self._estimate_success_rank(self._calculate_overall_success_rate(team_stats)),
                'third_down_rank': self._estimate_success_rank(team_stats.get('ThirdDownPercentage', 0) / 100),
                'red_zone_rank': self._estimate_success_rank(team_stats.get('RedZonePercentage', 0) / 100),

                'last_updated': datetime.now().isoformat()
            }

            # Cache the results
            self._cache_data(cache_key, success_data)

            logger.info(f"✅ Fetched success rates for {team}")
            return success_data

        except Exception as e:
            logger.error(f"❌ Error fetching success rates: {e}")
            return {}

    def get_team_situational_analytics(self, team: str, season: int = 2024) -> Dict:
        """Get comprehensive situational analytics"""
        cache_key = f"situational_analytics_{team}_{season}"

        if self._is_cached(cache_key):
            return self.cache[cache_key]['data']

        try:
            epa_data = self.get_team_epa_stats(team, season)
            dvoa_data = self.get_team_dvoa_metrics(team, season)
            success_data = self.get_team_success_rates(team, season)

            # Combine into comprehensive analytics
            analytics = {
                'team': team,
                'season': season,

                # Combined efficiency metrics
                'offensive_efficiency_score': self._calculate_efficiency_score(epa_data, dvoa_data, success_data, 'offense'),
                'defensive_efficiency_score': self._calculate_efficiency_score(epa_data, dvoa_data, success_data, 'defense'),

                # Situation-specific ratings
                'red_zone_efficiency': self._combine_red_zone_metrics(epa_data, dvoa_data, success_data),
                'third_down_efficiency': self._combine_third_down_metrics(epa_data, dvoa_data, success_data),
                'two_minute_efficiency': self._combine_two_minute_metrics(epa_data, dvoa_data, success_data),

                # Strength/weakness analysis
                'offensive_strengths': self._identify_offensive_strengths(epa_data, dvoa_data, success_data),
                'offensive_weaknesses': self._identify_offensive_weaknesses(epa_data, dvoa_data, success_data),
                'defensive_strengths': self._identify_defensive_strengths(epa_data, dvoa_data, success_data),
                'defensive_weaknesses': self._identify_defensive_weaknesses(epa_data, dvoa_data, success_data),

                # Game script tendencies
                'leading_performance': self._analyze_leading_performance(team),
                'trailing_performance': self._analyze_trailing_performance(team),
                'close_game_performance': self._analyze_close_game_performance(team),

                # Weather/dome splits
                'dome_performance': self._analyze_dome_performance(team),
                'weather_performance': self._analyze_weather_performance(team),

                # Opponent quality adjustments
                'strength_of_schedule_adj': self._calculate_sos_adjustment(team),
                'garbage_time_adjustment': self._calculate_garbage_time_adj(team),

                'last_updated': datetime.now().isoformat()
            }

            # Cache the results
            self._cache_data(cache_key, analytics)

            logger.info(f"✅ Generated situational analytics for {team}")
            return analytics

        except Exception as e:
            logger.error(f"❌ Error generating situational analytics: {e}")
            return {}

    def get_matchup_analytics(self, home_team: str, away_team: str, season: int = 2024) -> Dict:
        """Get comprehensive matchup analytics between two teams"""
        try:
            home_analytics = self.get_team_situational_analytics(home_team, season)
            away_analytics = self.get_team_situational_analytics(away_team, season)

            matchup = {
                'home_team': home_team,
                'away_team': away_team,
                'season': season,

                # Efficiency matchups
                'offensive_matchup': {
                    'home_offense_vs_away_defense': self._calculate_unit_matchup(
                        home_analytics.get('offensive_efficiency_score', 50),
                        away_analytics.get('defensive_efficiency_score', 50)
                    ),
                    'away_offense_vs_home_defense': self._calculate_unit_matchup(
                        away_analytics.get('offensive_efficiency_score', 50),
                        home_analytics.get('defensive_efficiency_score', 50)
                    )
                },

                # Key matchup areas
                'red_zone_advantage': self._calculate_red_zone_advantage(home_analytics, away_analytics),
                'third_down_advantage': self._calculate_third_down_advantage(home_analytics, away_analytics),
                'explosive_play_advantage': self._calculate_explosive_advantage(home_analytics, away_analytics),

                # Situational advantages
                'home_field_impact': self._calculate_home_field_impact(home_team),
                'coaching_advantage': self._calculate_coaching_advantage(home_team, away_team),
                'experience_advantage': self._calculate_experience_advantage(home_team, away_team),

                # Prediction factors
                'key_factors': self._identify_key_matchup_factors(home_analytics, away_analytics),
                'upset_potential': self._calculate_upset_potential(home_analytics, away_analytics),
                'game_script_prediction': self._predict_game_script(home_analytics, away_analytics),

                # Expert insights
                'analytics_recommendation': self._generate_analytics_recommendation(home_analytics, away_analytics),
                'confidence_level': self._calculate_analytics_confidence(home_analytics, away_analytics),

                'last_updated': datetime.now().isoformat()
            }

            return matchup

        except Exception as e:
            logger.error(f"❌ Error generating matchup analytics: {e}")
            return {}

    # EPA Calculation Methods
    def _calculate_offensive_epa(self, stats: Dict) -> float:
        """Calculate offensive EPA per play"""
        try:
            # Simplified EPA calculation based on yards per play and scoring
            yards_per_play = stats.get('OffensiveYardsPerPlay', 5.0)
            points_per_game = stats.get('PointsPerGame', 20)

            # EPA roughly correlates to yards per play and scoring efficiency
            base_epa = (yards_per_play - 5.0) * 0.1  # Average is ~5.0 yards per play
            scoring_bonus = (points_per_game - 22) * 0.01  # Average is ~22 PPG

            return round(base_epa + scoring_bonus, 3)
        except:
            return 0.0

    def _calculate_passing_epa(self, stats: Dict) -> float:
        """Calculate passing EPA per play"""
        try:
            pass_yards_per_attempt = stats.get('PassingYardsPerAttempt', 7.0)
            return round((pass_yards_per_attempt - 7.0) * 0.15, 3)
        except:
            return 0.0

    def _calculate_rushing_epa(self, stats: Dict) -> float:
        """Calculate rushing EPA per play"""
        try:
            rush_yards_per_attempt = stats.get('RushingYardsPerAttempt', 4.0)
            return round((rush_yards_per_attempt - 4.0) * 0.2, 3)
        except:
            return 0.0

    def _calculate_red_zone_epa(self, stats: Dict) -> float:
        """Calculate red zone EPA"""
        try:
            rz_pct = stats.get('RedZonePercentage', 50) / 100
            return round((rz_pct - 0.5) * 0.5, 3)
        except:
            return 0.0

    def _calculate_defensive_epa(self, stats: Dict) -> float:
        """Calculate defensive EPA (opponent)"""
        try:
            opp_yards_per_play = stats.get('OpponentOffensiveYardsPerPlay', 5.0)
            opp_points_per_game = stats.get('OpponentPointsPerGame', 22)

            base_epa = (5.0 - opp_yards_per_play) * 0.1
            scoring_bonus = (22 - opp_points_per_game) * 0.01

            return round(base_epa + scoring_bonus, 3)
        except:
            return 0.0

    def _calculate_pass_defense_epa(self, stats: Dict) -> float:
        """Calculate pass defense EPA"""
        try:
            opp_pass_yards_per_attempt = stats.get('OpponentPassingYardsPerAttempt', 7.0)
            return round((7.0 - opp_pass_yards_per_attempt) * 0.15, 3)
        except:
            return 0.0

    def _calculate_rush_defense_epa(self, stats: Dict) -> float:
        """Calculate rush defense EPA"""
        try:
            opp_rush_yards_per_attempt = stats.get('OpponentRushingYardsPerAttempt', 4.0)
            return round((4.0 - opp_rush_yards_per_attempt) * 0.2, 3)
        except:
            return 0.0

    # Down-specific EPA calculations
    def _calculate_first_down_epa(self, stats: Dict) -> float:
        """Calculate first down EPA"""
        return round(self._calculate_offensive_epa(stats) * 1.1, 3)  # Slightly better on first down

    def _calculate_second_down_epa(self, stats: Dict) -> float:
        """Calculate second down EPA"""
        return round(self._calculate_offensive_epa(stats) * 0.9, 3)  # Slightly worse on second down

    def _calculate_third_down_epa(self, stats: Dict) -> float:
        """Calculate third down EPA"""
        third_down_pct = stats.get('ThirdDownPercentage', 40) / 100
        return round((third_down_pct - 0.4) * 0.3, 3)

    def _calculate_fourth_down_epa(self, stats: Dict) -> float:
        """Calculate fourth down EPA"""
        fourth_down_pct = stats.get('FourthDownPercentage', 50) / 100
        return round((fourth_down_pct - 0.5) * 0.4, 3)

    def _calculate_goal_to_go_epa(self, stats: Dict) -> float:
        """Calculate goal-to-go EPA"""
        return self._calculate_red_zone_epa(stats)

    def _calculate_two_minute_epa(self, stats: Dict) -> float:
        """Calculate two-minute drill EPA"""
        return round(self._calculate_offensive_epa(stats) * 1.15, 3)  # Teams tend to be more efficient

    def _calculate_late_game_epa(self, stats: Dict) -> float:
        """Calculate late game EPA"""
        return round(self._calculate_offensive_epa(stats) * 0.95, 3)  # Slightly conservative

    def _estimate_epa_rank(self, epa_value: float, unit_type: str) -> int:
        """Estimate EPA ranking (1-32)"""
        if unit_type == 'offense':
            if epa_value > 0.15: return 5
            elif epa_value > 0.05: return 12
            elif epa_value > -0.05: return 18
            else: return 25
        else:  # defense
            if epa_value > 0.15: return 5
            elif epa_value > 0.05: return 12
            elif epa_value > -0.05: return 18
            else: return 25

    # DVOA Calculation Methods
    def _calculate_total_dvoa(self, stats: Dict) -> float:
        """Calculate total DVOA"""
        offensive_dvoa = self._calculate_offensive_dvoa(stats)
        defensive_dvoa = self._calculate_defensive_dvoa(stats)
        special_teams_dvoa = self._calculate_special_teams_dvoa(stats)
        return round(offensive_dvoa + defensive_dvoa + special_teams_dvoa, 1)

    def _calculate_offensive_dvoa(self, stats: Dict) -> float:
        """Calculate offensive DVOA"""
        try:
            yards_per_play = stats.get('OffensiveYardsPerPlay', 5.0)
            points_per_game = stats.get('PointsPerGame', 20)

            # DVOA as percentage above/below average
            dvoa = ((yards_per_play / 5.0) + (points_per_game / 22) - 2) * 50
            return round(dvoa, 1)
        except:
            return 0.0

    def _calculate_defensive_dvoa(self, stats: Dict) -> float:
        """Calculate defensive DVOA"""
        try:
            opp_yards_per_play = stats.get('OpponentOffensiveYardsPerPlay', 5.0)
            opp_points_per_game = stats.get('OpponentPointsPerGame', 22)

            # Defensive DVOA (negative is better)
            dvoa = ((5.0 / opp_yards_per_play) + (22 / opp_points_per_game) - 2) * 50
            return round(dvoa, 1)
        except:
            return 0.0

    def _calculate_special_teams_dvoa(self, stats: Dict) -> float:
        """Calculate special teams DVOA"""
        # Simplified ST DVOA based on available stats
        return 0.0  # Would need more detailed ST stats

    def _calculate_passing_dvoa(self, stats: Dict) -> float:
        """Calculate passing DVOA"""
        try:
            pass_yards_per_attempt = stats.get('PassingYardsPerAttempt', 7.0)
            return round((pass_yards_per_attempt / 7.0 - 1) * 50, 1)
        except:
            return 0.0

    def _calculate_rushing_dvoa(self, stats: Dict) -> float:
        """Calculate rushing DVOA"""
        try:
            rush_yards_per_attempt = stats.get('RushingYardsPerAttempt', 4.0)
            return round((rush_yards_per_attempt / 4.0 - 1) * 50, 1)
        except:
            return 0.0

    def _calculate_first_down_dvoa(self, stats: Dict) -> float:
        """Calculate first down DVOA"""
        return round(self._calculate_offensive_dvoa(stats) * 1.1, 1)

    def _calculate_second_down_dvoa(self, stats: Dict) -> float:
        """Calculate second down DVOA"""
        return round(self._calculate_offensive_dvoa(stats) * 0.9, 1)

    def _calculate_third_down_dvoa(self, stats: Dict) -> float:
        """Calculate third down DVOA"""
        third_down_pct = stats.get('ThirdDownPercentage', 40) / 100
        return round((third_down_pct / 0.4 - 1) * 50, 1)

    def _calculate_pass_defense_dvoa(self, stats: Dict) -> float:
        """Calculate pass defense DVOA"""
        try:
            opp_pass_yards_per_attempt = stats.get('OpponentPassingYardsPerAttempt', 7.0)
            return round((7.0 / opp_pass_yards_per_attempt - 1) * 50, 1)
        except:
            return 0.0

    def _calculate_rush_defense_dvoa(self, stats: Dict) -> float:
        """Calculate rush defense DVOA"""
        try:
            opp_rush_yards_per_attempt = stats.get('OpponentRushingYardsPerAttempt', 4.0)
            return round((4.0 / opp_rush_yards_per_attempt - 1) * 50, 1)
        except:
            return 0.0

    def _calculate_red_zone_defense_dvoa(self, stats: Dict) -> float:
        """Calculate red zone defense DVOA"""
        return self._calculate_defensive_dvoa(stats)

    def _calculate_red_zone_dvoa(self, stats: Dict) -> float:
        """Calculate red zone DVOA"""
        rz_pct = stats.get('RedZonePercentage', 50) / 100
        return round((rz_pct / 0.5 - 1) * 50, 1)

    def _calculate_goal_line_dvoa(self, stats: Dict) -> float:
        """Calculate goal line DVOA"""
        return self._calculate_red_zone_dvoa(stats)

    def _calculate_late_close_dvoa(self, stats: Dict) -> float:
        """Calculate late and close DVOA"""
        return round(self._calculate_offensive_dvoa(stats) * 0.95, 1)

    def _calculate_offensive_consistency(self, stats: Dict) -> float:
        """Calculate offensive consistency"""
        return 75.0  # Simplified - would need game-by-game data

    def _calculate_defensive_consistency(self, stats: Dict) -> float:
        """Calculate defensive consistency"""
        return 75.0  # Simplified - would need game-by-game data

    def _estimate_dvoa_rank(self, dvoa_value: float) -> int:
        """Estimate DVOA ranking"""
        if dvoa_value > 20: return 5
        elif dvoa_value > 10: return 12
        elif dvoa_value > -10: return 18
        else: return 25

    # Success Rate Calculation Methods
    def _calculate_overall_success_rate(self, stats: Dict) -> float:
        """Calculate overall success rate"""
        try:
            third_down = stats.get('ThirdDownPercentage', 40) / 100
            red_zone = stats.get('RedZonePercentage', 50) / 100
            return round((third_down + red_zone) / 2, 3)
        except:
            return 0.45

    def _calculate_passing_success_rate(self, stats: Dict) -> float:
        """Calculate passing success rate"""
        try:
            pass_yards_per_attempt = stats.get('PassingYardsPerAttempt', 7.0)
            # Success typically defined as 5+ yards on 1st down, 50%+ distance on 2nd, 100%+ on 3rd
            return round(min(0.8, max(0.3, pass_yards_per_attempt / 10)), 3)
        except:
            return 0.5

    def _calculate_rushing_success_rate(self, stats: Dict) -> float:
        """Calculate rushing success rate"""
        try:
            rush_yards_per_attempt = stats.get('RushingYardsPerAttempt', 4.0)
            # Success typically defined as 4+ yards on 1st down, 50%+ distance on 2nd, 100%+ on 3rd
            return round(min(0.7, max(0.3, rush_yards_per_attempt / 6)), 3)
        except:
            return 0.45

    def _calculate_first_down_success(self, stats: Dict) -> float:
        """Calculate first down success rate"""
        return round(self._calculate_overall_success_rate(stats) * 1.1, 3)

    def _calculate_second_down_success(self, stats: Dict) -> float:
        """Calculate second down success rate"""
        return round(self._calculate_overall_success_rate(stats) * 0.85, 3)

    def _calculate_goal_line_success(self, stats: Dict) -> float:
        """Calculate goal line success rate"""
        return stats.get('RedZonePercentage', 50) / 100

    def _calculate_short_yardage_success(self, stats: Dict) -> float:
        """Calculate short yardage success rate"""
        fourth_down = stats.get('FourthDownPercentage', 50) / 100
        return fourth_down

    def _calculate_explosive_play_rate(self, stats: Dict) -> float:
        """Calculate explosive play rate"""
        try:
            total_yards = stats.get('OffensiveYards', 5000)
            total_plays = total_yards / stats.get('OffensiveYardsPerPlay', 5.0)
            # Estimate explosive plays (20+ yards passing, 10+ rushing)
            return round(min(0.15, max(0.05, total_plays * 0.08 / total_plays)), 3)
        except:
            return 0.08

    def _calculate_defensive_success_rate(self, stats: Dict) -> float:
        """Calculate defensive success rate"""
        try:
            opp_third_down = 100 - stats.get('OpponentThirdDownPercentage', 40)
            opp_red_zone = 100 - stats.get('OpponentRedZonePercentage', 50)
            return round((opp_third_down + opp_red_zone) / 200, 3)
        except:
            return 0.55

    def _calculate_pass_defense_success(self, stats: Dict) -> float:
        """Calculate pass defense success rate"""
        try:
            opp_pass_yards_per_attempt = stats.get('OpponentPassingYardsPerAttempt', 7.0)
            return round(min(0.8, max(0.3, (10 - opp_pass_yards_per_attempt) / 10)), 3)
        except:
            return 0.5

    def _calculate_rush_defense_success(self, stats: Dict) -> float:
        """Calculate rush defense success rate"""
        try:
            opp_rush_yards_per_attempt = stats.get('OpponentRushingYardsPerAttempt', 4.0)
            return round(min(0.7, max(0.3, (6 - opp_rush_yards_per_attempt) / 6)), 3)
        except:
            return 0.55

    def _calculate_early_down_success(self, stats: Dict) -> float:
        """Calculate early down (1st & 2nd) success rate"""
        first_down = self._calculate_first_down_success(stats)
        second_down = self._calculate_second_down_success(stats)
        return round((first_down + second_down) / 2, 3)

    def _calculate_late_down_success(self, stats: Dict) -> float:
        """Calculate late down (3rd & 4th) success rate"""
        third_down = stats.get('ThirdDownPercentage', 40) / 100
        fourth_down = stats.get('FourthDownPercentage', 50) / 100
        return round((third_down + fourth_down) / 2, 3)

    def _calculate_scoring_drive_rate(self, stats: Dict) -> float:
        """Calculate scoring drive rate"""
        try:
            points_per_game = stats.get('PointsPerGame', 20)
            # Estimate drives per game (typically 10-12)
            drives_per_game = 11
            scores_per_game = points_per_game / 6  # Rough estimate
            return round(min(0.8, scores_per_game / drives_per_game), 3)
        except:
            return 0.35

    def _calculate_three_and_out_rate(self, stats: Dict) -> float:
        """Calculate three-and-out rate"""
        try:
            # Inverse relationship with third down conversion
            third_down_pct = stats.get('ThirdDownPercentage', 40) / 100
            return round(max(0.1, 0.35 - (third_down_pct * 0.5)), 3)
        except:
            return 0.25

    def _estimate_success_rank(self, success_rate: float) -> int:
        """Estimate success rate ranking"""
        if success_rate > 0.55: return 8
        elif success_rate > 0.45: return 16
        elif success_rate > 0.35: return 24
        else: return 30

    # Helper methods for advanced analytics
    def _calculate_efficiency_score(self, epa_data: Dict, dvoa_data: Dict, success_data: Dict, unit_type: str) -> float:
        """Calculate combined efficiency score"""
        try:
            if unit_type == 'offense':
                epa_score = epa_data.get('offensive_epa_per_play', 0) * 100
                dvoa_score = dvoa_data.get('offensive_dvoa', 0)
                success_score = success_data.get('overall_success_rate', 0.45) * 100
            else:
                epa_score = epa_data.get('defensive_epa_per_play', 0) * 100
                dvoa_score = dvoa_data.get('defensive_dvoa', 0)
                success_score = success_data.get('defensive_success_rate', 0.55) * 100

            # Weighted combination
            efficiency = (epa_score * 0.4) + (dvoa_score * 0.4) + (success_score * 0.2)
            return round(max(0, min(100, efficiency + 50)), 1)  # Scale to 0-100
        except:
            return 50.0

    def _combine_red_zone_metrics(self, epa_data: Dict, dvoa_data: Dict, success_data: Dict) -> Dict:
        """Combine red zone metrics"""
        return {
            'epa': epa_data.get('red_zone_epa', 0),
            'dvoa': dvoa_data.get('red_zone_dvoa', 0),
            'success_rate': success_data.get('red_zone_success_rate', 0.5),
            'combined_rating': round((
                epa_data.get('red_zone_epa', 0) * 100 +
                dvoa_data.get('red_zone_dvoa', 0) +
                success_data.get('red_zone_success_rate', 0.5) * 100
            ) / 3 + 50, 1)
        }

    def _combine_third_down_metrics(self, epa_data: Dict, dvoa_data: Dict, success_data: Dict) -> Dict:
        """Combine third down metrics"""
        return {
            'epa': epa_data.get('third_down_epa', 0),
            'dvoa': dvoa_data.get('third_down_dvoa', 0),
            'success_rate': success_data.get('third_down_success_rate', 0.4),
            'combined_rating': round((
                epa_data.get('third_down_epa', 0) * 100 +
                dvoa_data.get('third_down_dvoa', 0) +
                success_data.get('third_down_success_rate', 0.4) * 100
            ) / 3 + 50, 1)
        }

    def _combine_two_minute_metrics(self, epa_data: Dict, dvoa_data: Dict, success_data: Dict) -> Dict:
        """Combine two-minute drill metrics"""
        return {
            'epa': epa_data.get('two_minute_drill_epa', 0),
            'dvoa': dvoa_data.get('late_and_close_dvoa', 0),
            'success_rate': success_data.get('late_down_success_rate', 0.4),
            'combined_rating': round((
                epa_data.get('two_minute_drill_epa', 0) * 100 +
                dvoa_data.get('late_and_close_dvoa', 0) +
                success_data.get('late_down_success_rate', 0.4) * 100
            ) / 3 + 50, 1)
        }

    def _identify_offensive_strengths(self, epa_data: Dict, dvoa_data: Dict, success_data: Dict) -> List[str]:
        """Identify offensive strengths"""
        strengths = []

        if epa_data.get('passing_epa_per_play', 0) > 0.1:
            strengths.append('Passing efficiency')
        if epa_data.get('rushing_epa_per_play', 0) > 0.05:
            strengths.append('Rushing attack')
        if success_data.get('red_zone_success_rate', 0) > 0.6:
            strengths.append('Red zone conversion')
        if success_data.get('third_down_success_rate', 0) > 0.45:
            strengths.append('Third down conversion')
        if success_data.get('explosive_play_rate', 0) > 0.1:
            strengths.append('Big play ability')

        return strengths[:3]  # Top 3

    def _identify_offensive_weaknesses(self, epa_data: Dict, dvoa_data: Dict, success_data: Dict) -> List[str]:
        """Identify offensive weaknesses"""
        weaknesses = []

        if epa_data.get('passing_epa_per_play', 0) < -0.05:
            weaknesses.append('Passing inefficiency')
        if epa_data.get('rushing_epa_per_play', 0) < -0.05:
            weaknesses.append('Rushing struggles')
        if success_data.get('red_zone_success_rate', 0) < 0.4:
            weaknesses.append('Red zone failures')
        if success_data.get('third_down_success_rate', 0) < 0.35:
            weaknesses.append('Third down struggles')
        if success_data.get('three_and_out_rate', 0) > 0.3:
            weaknesses.append('Drive sustainability')

        return weaknesses[:3]  # Top 3

    def _identify_defensive_strengths(self, epa_data: Dict, dvoa_data: Dict, success_data: Dict) -> List[str]:
        """Identify defensive strengths"""
        strengths = []

        if epa_data.get('pass_defense_epa', 0) > 0.1:
            strengths.append('Pass defense')
        if epa_data.get('rush_defense_epa', 0) > 0.05:
            strengths.append('Run defense')
        if success_data.get('defensive_success_rate', 0) > 0.6:
            strengths.append('Situational defense')
        if dvoa_data.get('defensive_dvoa', 0) > 10:
            strengths.append('Overall efficiency')

        return strengths[:3]

    def _identify_defensive_weaknesses(self, epa_data: Dict, dvoa_data: Dict, success_data: Dict) -> List[str]:
        """Identify defensive weaknesses"""
        weaknesses = []

        if epa_data.get('pass_defense_epa', 0) < -0.05:
            weaknesses.append('Pass defense')
        if epa_data.get('rush_defense_epa', 0) < -0.05:
            weaknesses.append('Run defense')
        if success_data.get('defensive_success_rate', 0) < 0.5:
            weaknesses.append('Situational defense')
        if dvoa_data.get('defensive_dvoa', 0) < -10:
            weaknesses.append('Overall efficiency')

        return weaknesses[:3]

    # Mock methods for complex analytics (would need more detailed data)
    def _analyze_leading_performance(self, team: str) -> Dict:
        """Analyze performance when leading"""
        return {'efficiency': 75, 'play_calling': 'Conservative', 'success_rate': 0.65}

    def _analyze_trailing_performance(self, team: str) -> Dict:
        """Analyze performance when trailing"""
        return {'efficiency': 70, 'play_calling': 'Aggressive', 'success_rate': 0.55}

    def _analyze_close_game_performance(self, team: str) -> Dict:
        """Analyze performance in close games"""
        return {'efficiency': 68, 'clutch_rating': 7.5, 'success_rate': 0.58}

    def _analyze_dome_performance(self, team: str) -> Dict:
        """Analyze performance in dome games"""
        return {'efficiency': 72, 'passing_boost': 1.1, 'success_rate': 0.60}

    def _analyze_weather_performance(self, team: str) -> Dict:
        """Analyze performance in weather games"""
        return {'efficiency': 65, 'running_emphasis': 1.2, 'success_rate': 0.52}

    def _calculate_sos_adjustment(self, team: str) -> float:
        """Calculate strength of schedule adjustment"""
        return 0.02  # Mock adjustment

    def _calculate_garbage_time_adj(self, team: str) -> float:
        """Calculate garbage time adjustment"""
        return -0.01  # Mock adjustment

    def _calculate_unit_matchup(self, offense_score: float, defense_score: float) -> Dict:
        """Calculate unit vs unit matchup"""
        advantage = offense_score - defense_score
        return {
            'advantage_score': round(advantage, 1),
            'advantage_team': 'offense' if advantage > 0 else 'defense',
            'strength': 'Strong' if abs(advantage) > 15 else 'Moderate' if abs(advantage) > 5 else 'Slight'
        }

    def _calculate_red_zone_advantage(self, home_analytics: Dict, away_analytics: Dict) -> Dict:
        """Calculate red zone advantage"""
        home_rz = home_analytics.get('red_zone_efficiency', {}).get('combined_rating', 50)
        away_rz = away_analytics.get('red_zone_efficiency', {}).get('combined_rating', 50)

        return {
            'home_advantage': round(home_rz - away_rz, 1),
            'advantage_team': 'home' if home_rz > away_rz else 'away'
        }

    def _calculate_third_down_advantage(self, home_analytics: Dict, away_analytics: Dict) -> Dict:
        """Calculate third down advantage"""
        home_3rd = home_analytics.get('third_down_efficiency', {}).get('combined_rating', 50)
        away_3rd = away_analytics.get('third_down_efficiency', {}).get('combined_rating', 50)

        return {
            'home_advantage': round(home_3rd - away_3rd, 1),
            'advantage_team': 'home' if home_3rd > away_3rd else 'away'
        }

    def _calculate_explosive_advantage(self, home_analytics: Dict, away_analytics: Dict) -> Dict:
        """Calculate explosive play advantage"""
        return {
            'home_advantage': 2.5,
            'advantage_team': 'home'
        }

    def _calculate_home_field_impact(self, home_team: str) -> float:
        """Calculate home field advantage impact"""
        # Mock home field values - would be based on historical data
        home_field_map = {
            'SEA': 4.2, 'GB': 3.8, 'KC': 3.5, 'NO': 3.2, 'DEN': 3.0,
            'BUF': 2.8, 'PIT': 2.5, 'BAL': 2.3, 'SF': 2.0
        }
        return home_field_map.get(home_team, 2.5)

    def _calculate_coaching_advantage(self, home_team: str, away_team: str) -> float:
        """Calculate coaching advantage"""
        return 0.5  # Mock value

    def _calculate_experience_advantage(self, home_team: str, away_team: str) -> float:
        """Calculate experience advantage"""
        return 0.2  # Mock value

    def _identify_key_matchup_factors(self, home_analytics: Dict, away_analytics: Dict) -> List[str]:
        """Identify key factors for the matchup"""
        return [
            'Red zone efficiency differential',
            'Third down conversion rates',
            'Turnover differential potential',
            'Weather impact on passing game',
            'Home field advantage'
        ]

    def _calculate_upset_potential(self, home_analytics: Dict, away_analytics: Dict) -> Dict:
        """Calculate upset potential"""
        home_efficiency = home_analytics.get('offensive_efficiency_score', 50)
        away_efficiency = away_analytics.get('offensive_efficiency_score', 50)

        efficiency_gap = abs(home_efficiency - away_efficiency)

        if efficiency_gap < 5:
            upset_chance = 45
        elif efficiency_gap < 10:
            upset_chance = 35
        elif efficiency_gap < 15:
            upset_chance = 25
        else:
            upset_chance = 15

        return {
            'upset_percentage': upset_chance,
            'volatility': 'High' if efficiency_gap < 8 else 'Medium' if efficiency_gap < 15 else 'Low'
        }

    def _predict_game_script(self, home_analytics: Dict, away_analytics: Dict) -> Dict:
        """Predict likely game script"""
        return {
            'predicted_script': 'Competitive',
            'pace': 'Average',
            'total_plays': 125,
            'likely_leader': 'home'
        }

    def _generate_analytics_recommendation(self, home_analytics: Dict, away_analytics: Dict) -> str:
        """Generate analytics-based recommendation"""
        return "Based on advanced metrics, expect a competitive game with slight home field advantage."

    def _calculate_analytics_confidence(self, home_analytics: Dict, away_analytics: Dict) -> int:
        """Calculate confidence in analytics"""
        return 78  # Mock confidence level

    def _is_cached(self, key: str) -> bool:
        """Check if data is cached and still valid"""
        if key not in self.cache:
            return False
        return datetime.now().timestamp() - self.cache[key]['timestamp'] < self.cache_ttl

    def _cache_data(self, key: str, data: Any) -> None:
        """Cache data with timestamp"""
        self.cache[key] = {
            'data': data,
            'timestamp': datetime.now().timestamp()
        }

# Create singleton instance
advanced_analytics_service = AdvancedAnalyticsService()