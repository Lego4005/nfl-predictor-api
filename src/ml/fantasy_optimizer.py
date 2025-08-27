"""
Fantasy Football Optimization Engine
Advanced DFS lineup construction with correlation analysis and stacking strategies
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional, Any
from datetime import datetime
import logging
from itertools import combinations
import warnings
warnings.filterwarnings('ignore')

# Try to import optimization libraries
try:
    from scipy.optimize import linprog
    SCIPY_AVAILABLE = True
except ImportError:
    SCIPY_AVAILABLE = False

logger = logging.getLogger(__name__)

class FantasyOptimizer:
    """
    Advanced fantasy football optimizer with linear programming and correlation analysis
    Target accuracy: 68% for fantasy predictions
    """
    
    def __init__(self):
        # DraftKings salary cap and roster requirements
        self.salary_cap = 50000
        self.roster_requirements = {
            'QB': {'min': 1, 'max': 1},
            'RB': {'min': 2, 'max': 3},
            'WR': {'min': 3, 'max': 4},
            'TE': {'min': 1, 'max': 2},
            'FLEX': {'min': 1, 'max': 1},  # RB/WR/TE
            'DST': {'min': 1, 'max': 1}
        }
        
        self.total_roster_size = 9
        
        # Correlation matrices
        self.position_correlations = {}
        self.team_correlations = {}
        self.game_correlations = {}
        
        # Optimization settings
        self.optimization_settings = {
            'max_players_per_team': 4,
            'max_players_per_game': 6,
            'min_salary_usage': 0.95,  # Use at least 95% of salary cap
            'stack_bonus': 1.1,  # 10% bonus for QB-WR stacks
            'contrarian_threshold': 0.15,  # 15% ownership threshold
            'leverage_multiplier': 1.05  # 5% bonus for low ownership
        }
        
    def create_player_pool(self, num_players: int = 200) -> pd.DataFrame:
        """Create mock player pool for optimization"""
        np.random.seed(42)
        
        positions = ['QB', 'RB', 'WR', 'TE', 'DST']
        teams = ['KC', 'BUF', 'CIN', 'BAL', 'MIA', 'DAL', 'PHI', 'SF', 'LAR', 'GB', 
                'MIN', 'TB', 'NO', 'DET', 'SEA', 'ATL']
        
        players = []
        
        for i in range(num_players):
            position = np.random.choice(positions, p=[0.15, 0.25, 0.35, 0.15, 0.1])
            team = np.random.choice(teams)
            
            # Position-specific salary and projection ranges
            if position == 'QB':
                salary = np.random.randint(5500, 8500)
                projection = np.random.uniform(18, 28)
                ceiling = projection * np.random.uniform(1.3, 1.8)
                floor = projection * np.random.uniform(0.6, 0.8)
            elif position == 'RB':
                salary = np.random.randint(4000, 9000)
                projection = np.random.uniform(8, 22)
                ceiling = projection * np.random.uniform(1.5, 2.2)
                floor = projection * np.random.uniform(0.4, 0.7)
            elif position == 'WR':
                salary = np.random.randint(3500, 8000)
                projection = np.random.uniform(6, 20)
                ceiling = projection * np.random.uniform(1.4, 2.0)
                floor = projection * np.random.uniform(0.3, 0.6)
            elif position == 'TE':
                salary = np.random.randint(3000, 7000)
                projection = np.random.uniform(5, 16)
                ceiling = projection * np.random.uniform(1.3, 1.9)
                floor = projection * np.random.uniform(0.4, 0.7)
            else:  # DST
                salary = np.random.randint(2000, 3500)
                projection = np.random.uniform(6, 14)
                ceiling = projection * np.random.uniform(1.2, 1.6)
                floor = projection * np.random.uniform(0.5, 0.8)
            
            # Calculate value metrics
            value = projection / (salary / 1000)  # Points per $1K
            
            # Ownership projection (higher for better value)
            ownership = min(0.4, max(0.01, (value - 2.5) * 0.1 + np.random.uniform(0.05, 0.15)))
            
            # Game environment
            game_total = np.random.uniform(42, 54)
            team_implied_total = game_total / 2 + np.random.uniform(-6, 6)
            
            players.append({
                'player_id': f'player_{i}',
                'name': f'Player {i}',
                'position': position,
                'team': team,
                'salary': salary,
                'projection': projection,
                'ceiling': ceiling,
                'floor': floor,
                'value': value,
                'ownership': ownership,
                'game_total': game_total,
                'team_implied_total': team_implied_total,
                'opponent': np.random.choice([t for t in teams if t != team]),
                'is_home': np.random.choice([True, False]),
                'weather_factor': np.random.uniform(0.9, 1.1),
                'injury_risk': np.random.uniform(0.0, 0.3)
            })
        
        return pd.DataFrame(players)
    
    def calculate_correlations(self, player_pool: pd.DataFrame) -> Dict:
        """Calculate player correlations for stacking"""
        try:
            correlations = {
                'qb_wr_same_team': 0.65,  # QB and WR from same team
                'qb_te_same_team': 0.45,  # QB and TE from same team
                'rb_dst_same_team': -0.25,  # RB and DST from same team (negative)
                'wr_wr_same_team': -0.15,  # WRs from same team (compete for targets)
                'rb_rb_same_team': -0.35,  # RBs from same team (compete for carries)
                'game_stack': 0.35,  # Players from same game
                'opposing_dst': -0.40,  # Player vs opposing DST
                'high_total_game': 0.25,  # Players in high-scoring games
                'weather_correlation': 0.15  # Weather impact correlation
            }
            
            # Calculate team-specific correlations
            team_correlations = {}
            for team in player_pool['team'].unique():
                team_players = player_pool[player_pool['team'] == team]
                
                # QB correlation with pass catchers
                qb_players = team_players[team_players['position'] == 'QB']
                wr_players = team_players[team_players['position'] == 'WR']
                te_players = team_players[team_players['position'] == 'TE']
                
                team_correlations[team] = {
                    'qb_count': len(qb_players),
                    'wr_count': len(wr_players),
                    'te_count': len(te_players),
                    'avg_game_total': team_players['game_total'].mean(),
                    'avg_implied_total': team_players['team_implied_total'].mean()
                }
            
            self.position_correlations = correlations
            self.team_correlations = team_correlations
            
            return {
                'position_correlations': correlations,
                'team_correlations': team_correlations
            }
            
        except Exception as e:
            logger.error(f"Error calculating correlations: {e}")
            return {}
    
    def optimize_lineup(self, player_pool: pd.DataFrame, 
                       strategy: str = 'balanced',
                       stacking_preferences: Optional[Dict] = None) -> Dict:
        """Optimize DFS lineup using linear programming"""
        try:
            logger.info(f"🎯 Optimizing lineup with {strategy} strategy...")
            
            # Calculate correlations
            self.calculate_correlations(player_pool)
            
            # Apply strategy adjustments
            adjusted_pool = self._apply_strategy(player_pool, strategy)
            
            # Use simple greedy optimization if scipy not available
            if not SCIPY_AVAILABLE:
                return self._greedy_optimization(adjusted_pool, strategy)
            
            # Linear programming optimization
            return self._linear_programming_optimization(adjusted_pool, strategy, stacking_preferences)
            
        except Exception as e:
            logger.error(f"Error optimizing lineup: {e}")
            return {'success': False, 'error': str(e)}
    
    def _apply_strategy(self, player_pool: pd.DataFrame, strategy: str) -> pd.DataFrame:
        """Apply strategy-specific adjustments to player projections"""
        pool = player_pool.copy()
        
        if strategy == 'cash':
            # Cash game strategy: prioritize floor and consistency
            pool['adjusted_projection'] = (pool['projection'] * 0.7 + pool['floor'] * 0.3)
            pool['adjusted_projection'] *= (1 - pool['injury_risk'] * 0.5)  # Penalize injury risk
            
        elif strategy == 'gpp':
            # GPP strategy: prioritize ceiling and leverage
            pool['adjusted_projection'] = (pool['projection'] * 0.5 + pool['ceiling'] * 0.5)
            # Leverage low ownership
            ownership_multiplier = 1 + (self.optimization_settings['contrarian_threshold'] - pool['ownership']) * 0.3
            pool['adjusted_projection'] *= np.clip(ownership_multiplier, 0.8, 1.3)
            
        elif strategy == 'contrarian':
            # Contrarian strategy: target very low ownership
            pool['adjusted_projection'] = pool['ceiling']
            ownership_bonus = np.where(pool['ownership'] < 0.05, 1.4, 
                                      np.where(pool['ownership'] < 0.10, 1.2, 1.0))
            pool['adjusted_projection'] *= ownership_bonus
            
        else:  # balanced
            # Balanced strategy: equal weight to projection and upside
            pool['adjusted_projection'] = (pool['projection'] * 0.6 + pool['ceiling'] * 0.4)
        
        # Apply stacking bonuses
        pool = self._apply_stacking_bonuses(pool)
        
        return pool
    
    def _apply_stacking_bonuses(self, player_pool: pd.DataFrame) -> pd.DataFrame:
        """Apply correlation bonuses for stacking opportunities"""
        pool = player_pool.copy()
        
        # QB-WR/TE stacking bonus
        for team in pool['team'].unique():
            team_players = pool[pool['team'] == team]
            qb_players = team_players[team_players['position'] == 'QB']
            
            if len(qb_players) > 0:
                # Boost WR/TE from same team
                wr_te_mask = (pool['team'] == team) & pool['position'].isin(['WR', 'TE'])
                pool.loc[wr_te_mask, 'adjusted_projection'] *= self.optimization_settings['stack_bonus']
        
        # Game stack bonus (players from high-total games)
        high_total_threshold = pool['game_total'].quantile(0.75)
        high_total_mask = pool['game_total'] >= high_total_threshold
        pool.loc[high_total_mask, 'adjusted_projection'] *= 1.05
        
        return pool
    
    def _greedy_optimization(self, player_pool: pd.DataFrame, strategy: str) -> Dict:
        """Greedy optimization algorithm (fallback when scipy unavailable)"""
        try:
            logger.info("Using greedy optimization algorithm...")
            
            # Sort by value (adjusted projection per salary)
            player_pool['value_score'] = player_pool['adjusted_projection'] / (player_pool['salary'] / 1000)
            sorted_pool = player_pool.sort_values('value_score', ascending=False)
            
            lineup = []
            remaining_salary = self.salary_cap
            position_counts = {pos: 0 for pos in ['QB', 'RB', 'WR', 'TE', 'DST']}
            team_counts = {}
            
            # Fill required positions
            for _, player in sorted_pool.iterrows():
                pos = player['position']
                team = player['team']
                salary = player['salary']
                
                # Check constraints
                if salary > remaining_salary:
                    continue
                
                if pos in position_counts:
                    pos_req = self.roster_requirements.get(pos, {'min': 0, 'max': 10})
                    if position_counts[pos] >= pos_req['max']:
                        continue
                
                # Team limit
                if team_counts.get(team, 0) >= self.optimization_settings['max_players_per_team']:
                    continue
                
                # Add player to lineup
                lineup.append(player)
                remaining_salary -= salary
                position_counts[pos] += 1
                team_counts[team] = team_counts.get(team, 0) + 1
                
                # Check if lineup is complete
                if len(lineup) >= self.total_roster_size:
                    break
            
            # Fill FLEX position if needed
            if len(lineup) < self.total_roster_size:
                flex_positions = ['RB', 'WR', 'TE']
                for _, player in sorted_pool.iterrows():
                    if len(lineup) >= self.total_roster_size:
                        break
                    
                    if (player['position'] in flex_positions and 
                        player['salary'] <= remaining_salary and
                        not any(p['player_id'] == player['player_id'] for p in lineup)):
                        
                        lineup.append(player)
                        remaining_salary -= player['salary']
            
            # Calculate lineup metrics
            if len(lineup) >= 8:  # Allow slightly incomplete lineups
                total_projection = sum(p['adjusted_projection'] for p in lineup)
                total_salary = sum(p['salary'] for p in lineup)
                total_ownership = np.mean([p['ownership'] for p in lineup])
                
                return {
                    'success': True,
                    'lineup': lineup,
                    'total_projection': total_projection,
                    'total_salary': total_salary,
                    'remaining_salary': remaining_salary,
                    'total_ownership': total_ownership,
                    'strategy': strategy,
                    'optimization_method': 'greedy',
                    'lineup_count': len(lineup)
                }
            else:
                return {
                    'success': False,
                    'error': f'Could not build complete lineup (only {len(lineup)} players)',
                    'partial_lineup': lineup
                }
                
        except Exception as e:
            logger.error(f"Error in greedy optimization: {e}")
            return {'success': False, 'error': str(e)}
    
    def _linear_programming_optimization(self, player_pool: pd.DataFrame, 
                                       strategy: str, stacking_preferences: Optional[Dict]) -> Dict:
        """Linear programming optimization (when scipy available)"""
        try:
            logger.info("Using linear programming optimization...")
            
            n_players = len(player_pool)
            
            # Objective: maximize adjusted projections (minimize negative)
            c = -player_pool['adjusted_projection'].values
            
            # Constraint matrices
            A_eq = []
            b_eq = []
            A_ub = []
            b_ub = []
            
            # Roster size constraint
            A_eq.append(np.ones(n_players))
            b_eq.append(self.total_roster_size)
            
            # Position constraints
            for pos, req in self.roster_requirements.items():
                if pos == 'FLEX':
                    continue  # Handle FLEX separately
                
                pos_mask = (player_pool['position'] == pos).astype(int).values
                
                # Minimum constraint
                if req['min'] > 0:
                    A_ub.append(-pos_mask)
                    b_ub.append(-req['min'])
                
                # Maximum constraint
                if req['max'] < 10:
                    A_ub.append(pos_mask)
                    b_ub.append(req['max'])
            
            # FLEX constraint (RB + WR + TE >= 6)
            flex_mask = player_pool['position'].isin(['RB', 'WR', 'TE']).astype(int).values
            A_ub.append(-flex_mask)
            b_ub.append(-6)  # At least 6 RB/WR/TE total
            
            # Salary constraint
            A_ub.append(player_pool['salary'].values)
            b_ub.append(self.salary_cap)
            
            # Team constraints
            for team in player_pool['team'].unique():
                team_mask = (player_pool['team'] == team).astype(int).values
                A_ub.append(team_mask)
                b_ub.append(self.optimization_settings['max_players_per_team'])
            
            # Variable bounds (binary)
            bounds = [(0, 1) for _ in range(n_players)]
            
            # Solve
            result = linprog(c, A_ub=np.array(A_ub), b_ub=np.array(b_ub),
                           A_eq=np.array(A_eq), b_eq=np.array(b_eq),
                           bounds=bounds, method='highs')
            
            if result.success:
                # Extract lineup
                selected = result.x > 0.5
                lineup_players = player_pool[selected].to_dict('records')
                
                total_projection = sum(p['adjusted_projection'] for p in lineup_players)
                total_salary = sum(p['salary'] for p in lineup_players)
                total_ownership = np.mean([p['ownership'] for p in lineup_players])
                
                return {
                    'success': True,
                    'lineup': lineup_players,
                    'total_projection': total_projection,
                    'total_salary': total_salary,
                    'remaining_salary': self.salary_cap - total_salary,
                    'total_ownership': total_ownership,
                    'strategy': strategy,
                    'optimization_method': 'linear_programming',
                    'lineup_count': len(lineup_players)
                }
            else:
                logger.warning("Linear programming failed, falling back to greedy")
                return self._greedy_optimization(player_pool, strategy)
                
        except Exception as e:
            logger.error(f"Error in linear programming: {e}")
            return self._greedy_optimization(player_pool, strategy)
    
    def generate_multiple_lineups(self, player_pool: pd.DataFrame, 
                                 num_lineups: int = 5,
                                 strategies: Optional[List[str]] = None) -> List[Dict]:
        """Generate multiple optimized lineups with different strategies"""
        try:
            logger.info(f"🎯 Generating {num_lineups} optimized lineups...")
            
            if strategies is None:
                strategies = ['balanced', 'cash', 'gpp', 'contrarian']
            
            lineups = []
            used_players = set()
            
            for i in range(num_lineups):
                # Cycle through strategies
                strategy = strategies[i % len(strategies)]
                
                # Create variation in player pool
                varied_pool = self._create_lineup_variation(player_pool, used_players, i)
                
                # Optimize lineup
                lineup_result = self.optimize_lineup(varied_pool, strategy)
                
                if lineup_result['success']:
                    lineup_result['lineup_id'] = i + 1
                    lineups.append(lineup_result)
                    
                    # Track used players for diversity
                    for player in lineup_result['lineup']:
                        used_players.add(player['player_id'])
                else:
                    logger.warning(f"Failed to generate lineup {i + 1}: {lineup_result.get('error')}")
            
            return lineups
            
        except Exception as e:
            logger.error(f"Error generating multiple lineups: {e}")
            return []
    
    def _create_lineup_variation(self, player_pool: pd.DataFrame, 
                               used_players: set, iteration: int) -> pd.DataFrame:
        """Create variation in player pool for lineup diversity"""
        pool = player_pool.copy()
        
        # Add randomness to projections for diversity
        np.random.seed(42 + iteration)
        noise_factor = 0.05  # 5% noise
        noise = np.random.normal(1, noise_factor, len(pool))
        pool['projection'] *= noise
        pool['ceiling'] *= noise
        
        # Slightly penalize previously used players
        if used_players:
            used_mask = pool['player_id'].isin(used_players)
            pool.loc[used_mask, 'projection'] *= 0.95
        
        return pool
    
    def analyze_lineup_correlation(self, lineup: List[Dict]) -> Dict:
        """Analyze correlation and stacking in a lineup"""
        try:
            analysis = {
                'stacks': [],
                'correlations': {},
                'risk_factors': {},
                'leverage_opportunities': []
            }
            
            # Find stacks
            teams = {}
            for player in lineup:
                team = player['team']
                if team not in teams:
                    teams[team] = []
                teams[team].append(player)
            
            # Identify meaningful stacks
            for team, players in teams.items():
                if len(players) >= 2:
                    positions = [p['position'] for p in players]
                    
                    # QB stack
                    if 'QB' in positions:
                        pass_catchers = [p for p in players if p['position'] in ['WR', 'TE']]
                        if pass_catchers:
                            analysis['stacks'].append({
                                'type': 'QB_stack',
                                'team': team,
                                'players': [p['name'] for p in players],
                                'correlation_score': 0.65 if any(p['position'] == 'WR' for p in pass_catchers) else 0.45
                            })
                    
                    # Game stack
                    if len(players) >= 3:
                        analysis['stacks'].append({
                            'type': 'game_stack',
                            'team': team,
                            'players': [p['name'] for p in players],
                            'correlation_score': 0.35
                        })
            
            # Calculate ownership leverage
            low_ownership_players = [p for p in lineup if p['ownership'] < 0.10]
            if low_ownership_players:
                analysis['leverage_opportunities'] = [
                    {
                        'player': p['name'],
                        'ownership': p['ownership'],
                        'leverage_score': (0.15 - p['ownership']) * 2
                    }
                    for p in low_ownership_players
                ]
            
            # Risk analysis
            total_ownership = np.mean([p['ownership'] for p in lineup])
            injury_risk = np.mean([p['injury_risk'] for p in lineup])
            
            analysis['risk_factors'] = {
                'total_ownership': total_ownership,
                'injury_risk': injury_risk,
                'chalk_level': 'high' if total_ownership > 0.20 else 'medium' if total_ownership > 0.12 else 'low',
                'risk_level': 'high' if injury_risk > 0.20 else 'medium' if injury_risk > 0.10 else 'low'
            }
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error analyzing lineup correlation: {e}")
            return {}
    
    def calculate_lineup_value(self, lineup: List[Dict]) -> Dict:
        """Calculate comprehensive value metrics for a lineup"""
        try:
            if not lineup:
                return {}
            
            total_salary = sum(p['salary'] for p in lineup)
            total_projection = sum(p['projection'] for p in lineup)
            total_ceiling = sum(p['ceiling'] for p in lineup)
            total_floor = sum(p['floor'] for p in lineup)
            
            # Value metrics
            points_per_dollar = total_projection / (total_salary / 1000)
            salary_efficiency = total_salary / self.salary_cap
            
            # Position value breakdown
            position_values = {}
            for pos in ['QB', 'RB', 'WR', 'TE', 'DST']:
                pos_players = [p for p in lineup if p['position'] == pos]
                if pos_players:
                    pos_projection = sum(p['projection'] for p in pos_players)
                    pos_salary = sum(p['salary'] for p in pos_players)
                    position_values[pos] = {
                        'projection': pos_projection,
                        'salary': pos_salary,
                        'value': pos_projection / (pos_salary / 1000),
                        'count': len(pos_players)
                    }
            
            return {
                'total_projection': total_projection,
                'total_ceiling': total_ceiling,
                'total_floor': total_floor,
                'total_salary': total_salary,
                'remaining_salary': self.salary_cap - total_salary,
                'points_per_dollar': points_per_dollar,
                'salary_efficiency': salary_efficiency,
                'position_breakdown': position_values,
                'upside_ratio': total_ceiling / total_projection if total_projection > 0 else 0,
                'safety_ratio': total_floor / total_projection if total_projection > 0 else 0
            }
            
        except Exception as e:
            logger.error(f"Error calculating lineup value: {e}")
            return {}

# Example usage
if __name__ == "__main__":
    optimizer = FantasyOptimizer()
    
    # Create player pool
    player_pool = optimizer.create_player_pool(150)
    
    print("🏈 Fantasy Optimizer Test")
    print(f"Player pool: {len(player_pool)} players")
    print(f"Salary cap: ${optimizer.salary_cap:,}")
    
    # Test single lineup optimization
    lineup_result = optimizer.optimize_lineup(player_pool, strategy='balanced')
    
    if lineup_result['success']:
        print(f"\\n✅ Optimized Lineup ({lineup_result['optimization_method']}):")
        print(f"Total projection: {lineup_result['total_projection']:.1f}")
        print(f"Total salary: ${lineup_result['total_salary']:,}")
        print(f"Remaining: ${lineup_result['remaining_salary']:,}")
        print(f"Ownership: {lineup_result['total_ownership']:.1%}")
        
        print("\\nLineup:")
        for player in lineup_result['lineup']:
            print(f"  {player['position']:3} {player['name']:15} ${player['salary']:5,} {player['projection']:5.1f}pts")
        
        # Analyze lineup
        correlation_analysis = optimizer.analyze_lineup_correlation(lineup_result['lineup'])
        if correlation_analysis.get('stacks'):
            print(f"\\n🔗 Stacks found: {len(correlation_analysis['stacks'])}")
            for stack in correlation_analysis['stacks']:
                print(f"  {stack['type']}: {', '.join(stack['players'])}")
        
        # Value analysis
        value_analysis = optimizer.calculate_lineup_value(lineup_result['lineup'])
        print(f"\\n💰 Value Analysis:")
        print(f"  Points per $1K: {value_analysis['points_per_dollar']:.2f}")
        print(f"  Upside ratio: {value_analysis['upside_ratio']:.2f}")
        print(f"  Safety ratio: {value_analysis['safety_ratio']:.2f}")
    else:
        print(f"❌ Optimization failed: {lineup_result.get('error')}")
    
    # Test multiple lineups
    print(f"\\n🎯 Generating multiple lineups...")
    multiple_lineups = optimizer.generate_multiple_lineups(player_pool, num_lineups=3)
    
    print(f"Generated {len(multiple_lineups)} lineups:")
    for i, lineup in enumerate(multiple_lineups):
        print(f"  Lineup {i+1}: {lineup['total_projection']:.1f}pts, ${lineup['total_salary']:,}, {lineup['strategy']}")
    
    print("\\n🎉 Fantasy Optimizer test completed!")