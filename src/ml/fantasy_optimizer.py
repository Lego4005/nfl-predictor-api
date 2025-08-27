"""
Fantasy Football Lineup Optimization Engine

Linear programming optimization for DFS lineup construction with
salary cap constraints and position requirements.

Target Accuracy: >68% for fantasy optimization
"""

import logging
import numpy as np
import pandas as pd
from datetime import datetime
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass
import itertools
from scipy.optimize import linprog
import pulp

from data_pipeline import DataPipeline
from enhanced_features import EnhancedFeatureEngine
from player_props_engine import PlayerPropsEngine

logger = logging.getLogger(__name__)

@dataclass
class DFSPlayer:
    """DFS player with projections and salary"""
    name: str
    position: str
    team: str
    opponent: str
    salary: int
    projected_points: float
    ownership_projection: float
    value: float  # Points per $1000
    
    # Advanced metrics
    ceiling: float  # 90th percentile projection
    floor: float    # 10th percentile projection
    consistency: float  # Inverse of standard deviation
    
    # Correlations
    stack_bonus: float = 0.0  # Bonus for stacking
    leverage_score: float = 0.0  # Contrarian value

@dataclass
class OptimalLineup:
    """Optimized DFS lineup"""
    players: List[DFSPlayer]
    total_salary: int
    projected_points: float
    projected_ownership: float
    
    # Lineup composition
    qb: DFSPlayer
    rb1: DFSPlayer
    rb2: DFSPlayer
    wr1: DFSPlayer
    wr2: DFSPlayer
    wr3: DFSPlayer
    te: DFSPlayer
    flex: DFSPlayer  # RB/WR/TE
    dst: Optional[DFSPlayer] = None
    
    # Advanced metrics
    ceiling: float = 0.0
    floor: float = 0.0
    leverage_score: float = 0.0
    stack_correlation: float = 0.0
    
    # Strategy info
    strategy: str = "balanced"  # balanced, cash, gpp, contrarian
    risk_level: str = "medium"  # low, medium, high

class FantasyOptimizer:
    """
    Advanced fantasy football lineup optimizer with multiple strategies
    """
    
    def __init__(self, data_pipeline: DataPipeline, feature_engine: EnhancedFeatureEngine, 
                 props_engine: PlayerPropsEngine):
        self.data_pipeline = data_pipeline
        self.feature_engine = feature_engine
        self.props_engine = props_engine
        
        # DFS settings (DraftKings format)
        self.salary_cap = 50000
        self.roster_positions = {
            'QB': 1,
            'RB': 2,
            'WR': 3,
            'TE': 1,
            'FLEX': 1,  # RB/WR/TE
            'DST': 1
        }
        
        # Scoring settings (DraftKings)
        self.scoring = {
            'passing_yard': 0.04,  # 1 point per 25 yards
            'passing_td': 4.0,
            'rushing_yard': 0.1,   # 1 point per 10 yards
            'rushing_td': 6.0,
            'receiving_yard': 0.1, # 1 point per 10 yards
            'receiving_td': 6.0,
            'reception': 1.0,      # PPR
            'interception': -1.0,
            'fumble': -1.0
        }
        
    def create_player_pool(self, week: int, season: int = 2024) -> List[DFSPlayer]:
        """Create player pool with projections and salaries"""
        logger.info(f"🏗️ Creating player pool for Week {week}...")
        
        player_pool = []
        
        if self.data_pipeline.players_df is None:
            logger.warning("No player data available")
            return player_pool
            
        # Get unique players from recent games
        recent_players = self.data_pipeline.players_df[
            (self.data_pipeline.players_df['season'] == season) &
            (self.data_pipeline.players_df['week'] >= max(1, week - 3))  # Recent weeks
        ].drop_duplicates(['player_name', 'team'])
        
        for _, player_row in recent_players.iterrows():
            try:
                player_name = player_row['player_name']
                team = player_row['team']
                position = player_row['position']
                
                # Skip non-skill positions
                if position not in ['QB', 'RB', 'WR', 'TE']:
                    continue
                    
                # Get opponent (simplified - use a random opponent for demo)
                opponent = self._get_opponent(team, week)
                
                # Generate projections using props engine
                date = datetime(season, 9, 1) + pd.Timedelta(weeks=week-1)
                
                try:
                    props_prediction = self.props_engine.predict_player_props(
                        player_name, team, opponent, date, week
                    )
                    
                    # Calculate projected fantasy points
                    projected_points = self._calculate_fantasy_points(props_prediction)
                    
                    # Generate salary (simplified model based on projections)
                    salary = self._estimate_salary(projected_points, position)
                    
                    # Calculate value
                    value = (projected_points / salary) * 1000 if salary > 0 else 0
                    
                    # Estimate ownership (simplified)
                    ownership = self._estimate_ownership(projected_points, salary, position)
                    
                    # Calculate ceiling and floor
                    ceiling = projected_points * 1.4  # 40% upside
                    floor = projected_points * 0.6    # 40% downside
                    consistency = 1.0 / (0.2 * projected_points + 1)  # Simplified consistency
                    
                    dfs_player = DFSPlayer(
                        name=player_name,
                        position=position,
                        team=team,
                        opponent=opponent,
                        salary=salary,
                        projected_points=projected_points,
                        ownership_projection=ownership,
                        value=value,
                        ceiling=ceiling,
                        floor=floor,
                        consistency=consistency
                    )
                    
                    player_pool.append(dfs_player)
                    
                except Exception as e:
                    logger.debug(f"Skipping {player_name}: {e}")
                    continue
                    
            except Exception as e:
                logger.debug(f"Error processing player: {e}")
                continue
                
        # Add DST players (simplified)
        player_pool.extend(self._create_dst_players(week, season))
        
        logger.info(f"✅ Created player pool with {len(player_pool)} players")
        return player_pool
        
    def _get_opponent(self, team: str, week: int) -> str:
        """Get opponent for a team in a given week (simplified)"""
        # This is a simplified implementation
        # In practice, you'd have a schedule lookup
        all_teams = ['ARI', 'ATL', 'BAL', 'BUF', 'CAR', 'CHI', 'CIN', 'CLE', 
                    'DAL', 'DEN', 'DET', 'GB', 'HOU', 'IND', 'JAX', 'KC', 
                    'LV', 'LAC', 'LAR', 'MIA', 'MIN', 'NE', 'NO', 'NYG', 
                    'NYJ', 'PHI', 'PIT', 'SF', 'SEA', 'TB', 'TEN', 'WAS']
        
        # Simple rotation for demo
        team_index = all_teams.index(team) if team in all_teams else 0
        opponent_index = (team_index + week) % len(all_teams)
        return all_teams[opponent_index]
        
    def _calculate_fantasy_points(self, props_prediction) -> float:
        """Calculate projected fantasy points from props"""
        points = 0.0
        
        # Passing
        points += props_prediction.passing_yards * self.scoring['passing_yard']
        points += props_prediction.passing_tds * self.scoring['passing_td']
        
        # Rushing
        points += props_prediction.rushing_yards * self.scoring['rushing_yard']
        points += props_prediction.rushing_tds * self.scoring['rushing_td']
        
        # Receiving
        points += props_prediction.receiving_yards * self.scoring['receiving_yard']
        points += props_prediction.receiving_tds * self.scoring['receiving_td']
        points += props_prediction.receptions * self.scoring['reception']
        
        return max(0, points)
        
    def _estimate_salary(self, projected_points: float, position: str) -> int:
        """Estimate DFS salary based on projections"""
        # Base salary by position
        base_salaries = {
            'QB': 7000,
            'RB': 6000,
            'WR': 5500,
            'TE': 4500,
            'DST': 3000
        }
        
        base = base_salaries.get(position, 5000)
        
        # Adjust based on projected points
        if position == 'QB':
            salary = base + (projected_points - 15) * 200
        elif position in ['RB', 'WR']:
            salary = base + (projected_points - 10) * 300
        elif position == 'TE':
            salary = base + (projected_points - 8) * 250
        else:
            salary = base
            
        # Clamp to reasonable range
        return max(3000, min(12000, int(salary)))
        
    def _estimate_ownership(self, projected_points: float, salary: int, position: str) -> float:
        """Estimate ownership percentage"""
        # Higher projected points and lower salary = higher ownership
        value = (projected_points / salary) * 1000
        
        # Base ownership by position
        base_ownership = {
            'QB': 0.15,
            'RB': 0.20,
            'WR': 0.18,
            'TE': 0.12,
            'DST': 0.10
        }
        
        base = base_ownership.get(position, 0.15)
        
        # Adjust based on value
        ownership = base + (value - 2.0) * 0.05
        
        return max(0.01, min(0.50, ownership))
        
    def _create_dst_players(self, week: int, season: int) -> List[DFSPlayer]:
        """Create DST players with projections"""
        dst_players = []
        
        teams = ['KC', 'BUF', 'SF', 'DAL', 'PHI', 'BAL', 'DET', 'MIA']  # Top defenses
        
        for i, team in enumerate(teams):
            # Simple DST scoring model
            projected_points = 8.0 - (i * 0.5)  # Top defenses score more
            salary = 3000 + (i * 100)
            
            dst_player = DFSPlayer(
                name=f"{team} DST",
                position='DST',
                team=team,
                opponent=self._get_opponent(team, week),
                salary=salary,
                projected_points=projected_points,
                ownership_projection=0.10 + (i * 0.01),
                value=(projected_points / salary) * 1000,
                ceiling=projected_points * 1.5,
                floor=projected_points * 0.3,
                consistency=0.7
            )
            
            dst_players.append(dst_player)
            
        return dst_players
        
    def optimize_lineup(self, player_pool: List[DFSPlayer], strategy: str = "balanced") -> OptimalLineup:
        """Optimize lineup using linear programming"""
        logger.info(f"🔧 Optimizing lineup with {strategy} strategy...")
        
        if not player_pool:
            raise ValueError("Empty player pool")
            
        # Filter players by position
        qbs = [p for p in player_pool if p.position == 'QB']
        rbs = [p for p in player_pool if p.position == 'RB']
        wrs = [p for p in player_pool if p.position == 'WR']
        tes = [p for p in player_pool if p.position == 'TE']
        dsts = [p for p in player_pool if p.position == 'DST']
        
        # Flex eligible (RB/WR/TE)
        flex_eligible = rbs + wrs + tes
        
        logger.info(f"Player pool: {len(qbs)} QBs, {len(rbs)} RBs, {len(wrs)} WRs, {len(tes)} TEs, {len(dsts)} DSTs")
        
        # Use PuLP for optimization
        prob = pulp.LpProblem("DFS_Lineup_Optimization", pulp.LpMaximize)
        
        # Decision variables
        player_vars = {}
        for player in player_pool:
            player_vars[player.name] = pulp.LpVariable(f"player_{player.name}", cat='Binary')
            
        # Objective function (maximize points with strategy adjustments)
        objective = []
        for player in player_pool:
            points = player.projected_points
            
            # Strategy adjustments
            if strategy == "cash":
                points = points * player.consistency  # Favor consistent players
            elif strategy == "gpp":
                points = player.ceiling * 0.7 + points * 0.3  # Favor upside
            elif strategy == "contrarian":
                points = points * (1.5 - player.ownership_projection)  # Fade popular players
                
            objective.append(points * player_vars[player.name])
            
        prob += pulp.lpSum(objective)
        
        # Salary constraint
        prob += pulp.lpSum([player.salary * player_vars[player.name] for player in player_pool]) <= self.salary_cap
        
        # Position constraints - simplified approach
        prob += pulp.lpSum([player_vars[player.name] for player in qbs]) == 1
        prob += pulp.lpSum([player_vars[player.name] for player in rbs]) == 2
        prob += pulp.lpSum([player_vars[player.name] for player in wrs]) == 3
        prob += pulp.lpSum([player_vars[player.name] for player in tes]) == 1
        prob += pulp.lpSum([player_vars[player.name] for player in flex_eligible]) == 1  # 1 FLEX
        prob += pulp.lpSum([player_vars[player.name] for player in dsts]) == 1
        
        # Total players constraint (1 QB + 2 RB + 3 WR + 1 TE + 1 FLEX + 1 DST = 9)
        prob += pulp.lpSum([player_vars[player.name] for player in player_pool]) == 9
        
        # Solve
        prob.solve(pulp.PULP_CBC_CMD(msg=0))
        
        if prob.status != pulp.LpStatusOptimal:
            logger.warning(f"Optimization status: {pulp.LpStatus[prob.status]}")
            # Try a simpler approach - greedy selection
            return self._greedy_lineup_selection(player_pool, strategy)
            
        # Extract solution
        selected_players = []
        for player in player_pool:
            if player_vars[player.name].varValue == 1:
                selected_players.append(player)
                
        # Organize by position
        lineup_qb = next((p for p in selected_players if p.position == 'QB'), None)
        lineup_rbs = [p for p in selected_players if p.position == 'RB']
        lineup_wrs = [p for p in selected_players if p.position == 'WR']
        lineup_te = next((p for p in selected_players if p.position == 'TE'), None)
        lineup_dst = next((p for p in selected_players if p.position == 'DST'), None)
        
        # Find flex player (should be exactly 1 from flex_eligible beyond the core positions)
        flex_player = None
        core_players = set()
        if lineup_qb:
            core_players.add(lineup_qb.name)
        for rb in lineup_rbs[:2]:  # First 2 RBs
            core_players.add(rb.name)
        for wr in lineup_wrs[:3]:  # First 3 WRs
            core_players.add(wr.name)
        if lineup_te:
            core_players.add(lineup_te.name)
        if lineup_dst:
            core_players.add(lineup_dst.name)
            
        # Find the flex player (the one not in core positions)
        for player in selected_players:
            if player.name not in core_players and player.position in ['RB', 'WR', 'TE']:
                flex_player = player
                break
            
        # Calculate lineup metrics
        total_salary = sum(p.salary for p in selected_players)
        projected_points = sum(p.projected_points for p in selected_players)
        projected_ownership = np.mean([p.ownership_projection for p in selected_players])
        ceiling = sum(p.ceiling for p in selected_players)
        floor = sum(p.floor for p in selected_players)
        
        # Create optimal lineup
        optimal_lineup = OptimalLineup(
            players=selected_players,
            total_salary=total_salary,
            projected_points=projected_points,
            projected_ownership=projected_ownership,
            qb=lineup_qb,
            rb1=lineup_rbs[0] if len(lineup_rbs) > 0 else None,
            rb2=lineup_rbs[1] if len(lineup_rbs) > 1 else None,
            wr1=lineup_wrs[0] if len(lineup_wrs) > 0 else None,
            wr2=lineup_wrs[1] if len(lineup_wrs) > 1 else None,
            wr3=lineup_wrs[2] if len(lineup_wrs) > 2 else None,
            te=lineup_te,
            flex=flex_player,
            dst=lineup_dst,
            ceiling=ceiling,
            floor=floor,
            strategy=strategy,
            risk_level="medium"
        )
        
        logger.info(f"✅ Optimized lineup: {projected_points:.1f} points, ${total_salary} salary")
        return optimal_lineup
        
    def generate_multiple_lineups(self, player_pool: List[DFSPlayer], num_lineups: int = 5) -> List[OptimalLineup]:
        """Generate multiple optimized lineups with different strategies"""
        logger.info(f"🔧 Generating {num_lineups} optimized lineups...")
        
        lineups = []
        strategies = ["balanced", "cash", "gpp", "contrarian", "balanced"]
        
        for i in range(num_lineups):
            strategy = strategies[i % len(strategies)]
            
            try:
                lineup = self.optimize_lineup(player_pool, strategy)
                lineups.append(lineup)
                
                # Remove top players to create diversity (simplified approach)
                if i < num_lineups - 1:
                    # Remove highest owned players for next iteration
                    used_players = {p.name for p in lineup.players}
                    player_pool = [p for p in player_pool if p.name not in used_players or p.ownership_projection < 0.15]
                    
            except Exception as e:
                logger.warning(f"⚠️ Failed to generate lineup {i+1}: {e}")
                continue
                
        logger.info(f"✅ Generated {len(lineups)} unique lineups")
        return lineups
        
    def _greedy_lineup_selection(self, player_pool: List[DFSPlayer], strategy: str) -> OptimalLineup:
        """Fallback greedy lineup selection when optimization fails"""
        logger.info("🔄 Using greedy selection fallback...")
        
        # Sort players by value (points per $1000)
        sorted_players = sorted(player_pool, key=lambda p: p.value, reverse=True)
        
        # Select players greedily
        selected = []
        remaining_salary = self.salary_cap
        positions_needed = {'QB': 1, 'RB': 2, 'WR': 3, 'TE': 1, 'FLEX': 1, 'DST': 1}
        
        # First pass - fill required positions
        for player in sorted_players:
            if player.salary > remaining_salary:
                continue
                
            if positions_needed.get(player.position, 0) > 0:
                selected.append(player)
                remaining_salary -= player.salary
                positions_needed[player.position] -= 1
                
        # Second pass - fill FLEX
        if positions_needed.get('FLEX', 0) > 0:
            for player in sorted_players:
                if player in selected or player.salary > remaining_salary:
                    continue
                if player.position in ['RB', 'WR', 'TE']:
                    selected.append(player)
                    remaining_salary -= player.salary
                    positions_needed['FLEX'] -= 1
                    break
                    
        # Create lineup from selected players
        lineup_players = {pos: [] for pos in ['QB', 'RB', 'WR', 'TE', 'DST']}
        flex_player = None
        
        position_counts = {'QB': 0, 'RB': 0, 'WR': 0, 'TE': 0, 'DST': 0}
        
        for player in selected:
            if player.position == 'QB' and position_counts['QB'] < 1:
                lineup_players['QB'].append(player)
                position_counts['QB'] += 1
            elif player.position == 'RB' and position_counts['RB'] < 2:
                lineup_players['RB'].append(player)
                position_counts['RB'] += 1
            elif player.position == 'WR' and position_counts['WR'] < 3:
                lineup_players['WR'].append(player)
                position_counts['WR'] += 1
            elif player.position == 'TE' and position_counts['TE'] < 1:
                lineup_players['TE'].append(player)
                position_counts['TE'] += 1
            elif player.position == 'DST' and position_counts['DST'] < 1:
                lineup_players['DST'].append(player)
                position_counts['DST'] += 1
            elif player.position in ['RB', 'WR', 'TE'] and not flex_player:
                flex_player = player
                
        # Calculate metrics
        total_salary = sum(p.salary for p in selected)
        projected_points = sum(p.projected_points for p in selected)
        projected_ownership = np.mean([p.ownership_projection for p in selected])
        ceiling = sum(p.ceiling for p in selected)
        floor = sum(p.floor for p in selected)
        
        return OptimalLineup(
            players=selected,
            total_salary=total_salary,
            projected_points=projected_points,
            projected_ownership=projected_ownership,
            qb=lineup_players['QB'][0] if lineup_players['QB'] else None,
            rb1=lineup_players['RB'][0] if len(lineup_players['RB']) > 0 else None,
            rb2=lineup_players['RB'][1] if len(lineup_players['RB']) > 1 else None,
            wr1=lineup_players['WR'][0] if len(lineup_players['WR']) > 0 else None,
            wr2=lineup_players['WR'][1] if len(lineup_players['WR']) > 1 else None,
            wr3=lineup_players['WR'][2] if len(lineup_players['WR']) > 2 else None,
            te=lineup_players['TE'][0] if lineup_players['TE'] else None,
            flex=flex_player,
            dst=lineup_players['DST'][0] if lineup_players['DST'] else None,
            ceiling=ceiling,
            floor=floor,
            strategy=strategy,
            risk_level="medium"
        )

def main():
    """Test fantasy optimizer"""
    # Initialize components
    pipeline = DataPipeline()
    feature_engine = EnhancedFeatureEngine(pipeline.games_df)
    props_engine = PlayerPropsEngine(pipeline, feature_engine)
    
    # Train props models first
    logger.info("🚀 Training props models for fantasy optimization...")
    props_engine.train_prop_models()
    
    # Create fantasy optimizer
    optimizer = FantasyOptimizer(pipeline, feature_engine, props_engine)
    
    # Create player pool
    week = 15
    player_pool = optimizer.create_player_pool(week)
    
    if not player_pool:
        print("❌ No players in pool")
        return
        
    # Generate optimal lineups
    lineups = optimizer.generate_multiple_lineups(player_pool, 3)
    
    for i, lineup in enumerate(lineups, 1):
        print(f"\n🏆 Optimal Lineup #{i} ({lineup.strategy}):")
        print(f"💰 Salary: ${lineup.total_salary:,} / ${optimizer.salary_cap:,}")
        print(f"📊 Projected Points: {lineup.projected_points:.1f}")
        print(f"📈 Ceiling: {lineup.ceiling:.1f}")
        print(f"📉 Floor: {lineup.floor:.1f}")
        print(f"👥 Avg Ownership: {lineup.projected_ownership:.1%}")
        
        print(f"\n🏈 Lineup:")
        if lineup.qb:
            print(f"  QB: {lineup.qb.name} ({lineup.qb.team}) - ${lineup.qb.salary} - {lineup.qb.projected_points:.1f} pts")
        if lineup.rb1:
            print(f"  RB: {lineup.rb1.name} ({lineup.rb1.team}) - ${lineup.rb1.salary} - {lineup.rb1.projected_points:.1f} pts")
        if lineup.rb2:
            print(f"  RB: {lineup.rb2.name} ({lineup.rb2.team}) - ${lineup.rb2.salary} - {lineup.rb2.projected_points:.1f} pts")
        if lineup.wr1:
            print(f"  WR: {lineup.wr1.name} ({lineup.wr1.team}) - ${lineup.wr1.salary} - {lineup.wr1.projected_points:.1f} pts")
        if lineup.wr2:
            print(f"  WR: {lineup.wr2.name} ({lineup.wr2.team}) - ${lineup.wr2.salary} - {lineup.wr2.projected_points:.1f} pts")
        if lineup.wr3:
            print(f"  WR: {lineup.wr3.name} ({lineup.wr3.team}) - ${lineup.wr3.salary} - {lineup.wr3.projected_points:.1f} pts")
        if lineup.te:
            print(f"  TE: {lineup.te.name} ({lineup.te.team}) - ${lineup.te.salary} - {lineup.te.projected_points:.1f} pts")
        if lineup.flex:
            print(f"FLEX: {lineup.flex.name} ({lineup.flex.team}) - ${lineup.flex.salary} - {lineup.flex.projected_points:.1f} pts")
        if lineup.dst:
            print(f" DST: {lineup.dst.name} - ${lineup.dst.salary} - {lineup.dst.projected_points:.1f} pts")
            
    print(f"\n🎉 Fantasy Optimization Complete!")
    print(f"📈 Target Accuracy: >68% fantasy optimization")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()