// Neo4j Bootstrap Schema for NFL Expert Learning System
// Clean graph verbs for provenance and relationship tracking

// ========================================
// 1. CONSTRAINTS AND INDEXES
// ========================================

// Node constraints
CREATE CONSTRAINT expert_id_unique IF NOT EXISTS FOR (e:Expert) REQUIRE e.id IS UNIQUE;
CREATE CONSTRAINT team_id_unique IF NOT EXISTS FOR (t:Team) REQUIRE t.id IS UNIQUE;
CREATE CONSTRAINT game_id_unique IF NOT EXISTS FOR (g:Game) REQUIRE g.id IS UNIQUE;
CREATE CONSTRAINT memory_id_unique IF NOT EXISTS FOR (m:Memory) REQUIRE m.id IS UNIQUE;

// Performance indexes
CREATE INDEX expert_name_idx IF NOT EXISTS FOR (e:Expert) ON (e.name);
CREATE INDEX team_division_idx IF NOT EXISTS FOR (t:Team) ON (t.division);
CREATE INDEX game_date_idx IF NOT EXISTS FOR (g:Game) ON (g.date);
CREATE INDEX game_season_week_idx IF NOT EXISTS FOR (g:Game) ON (g.season, g.week);
CREATE INDEX memory_type_idx IF NOT EXISTS FOR (m:Memory) ON (m.type);

// ========================================
// 2. CORE NODES CREATION
// ========================================

// Create Expert nodes (15 personality experts)
MERGE (e1:Expert {id: 'conservative_analyzer', name: 'The Analyst', personality: 'analytical', decision_style: 'data_driven'})
MERGE (e2:Expert {id: 'risk_taking_gambler', name: 'The Gambler', personality: 'aggressive', decision_style: 'high_risk'})
MERGE (e3:Expert {id: 'contrarian_rebel', name: 'The Rebel', personality: 'contrarian', decision_style: 'fade_public'})
MERGE (e4:Expert {id: 'value_hunter', name: 'The Hunter', personality: 'value_focused', decision_style: 'find_edges'})
MERGE (e5:Expert {id: 'momentum_rider', name: 'The Rider', personality: 'trend_following', decision_style: 'ride_streaks'})
MERGE (e6:Expert {id: 'fundamentalist_scholar', name: 'The Scholar', personality: 'research_heavy', decision_style: 'deep_analysis'})
MERGE (e7:Expert {id: 'chaos_theory_believer', name: 'The Chaos', personality: 'unpredictable', decision_style: 'embrace_variance'})
MERGE (e8:Expert {id: 'gut_instinct_expert', name: 'The Intuition', personality: 'intuitive', decision_style: 'feel_based'})
MERGE (e9:Expert {id: 'statistics_purist', name: 'The Quant', personality: 'mathematical', decision_style: 'numbers_only'})
MERGE (e10:Expert {id: 'trend_reversal_specialist', name: 'The Reversal', personality: 'contrarian_timing', decision_style: 'spot_reversals'})
MERGE (e11:Expert {id: 'popular_narrative_fader', name: 'The Fader', personality: 'narrative_skeptic', decision_style: 'fade_stories'})
MERGE (e12:Expert {id: 'sharp_money_follower', name: 'The Sharp', personality: 'market_follower', decision_style: 'follow_smart_money'})
MERGE (e13:Expert {id: 'underdog_champion', name: 'The Underdog', personality: 'underdog_bias', decision_style: 'back_dogs'})
MERGE (e14:Expert {id: 'consensus_follower', name: 'The Consensus', personality: 'group_think', decision_style: 'follow_crowd'})
MERGE (e15:Expert {id: 'market_inefficiency_exploiter', name: 'The Exploiter', personality: 'efficiency_hunter', decision_style: 'find_mispricing'});

// Create Team nodes (32 NFL teams)
MERGE (t1:Team {id: 'ARI', name: 'Arizona Cardinals', division: 'NFC West', conference: 'NFC'})
MERGE (t2:Team {id: 'ATL', name: 'Atlanta Falcons', division: 'NFC South', conference: 'NFC'})
MERGE (t3:Team {id: 'BAL', name: 'Baltimore Ravens', division: 'AFC North', conference: 'AFC'})
MERGE (t4:Team {id: 'BUF', name: 'Buffalo Bills', division: 'AFC East', conference: 'AFC'})
MERGE (t5:Team {id: 'CAR', name: 'Carolina Panthers', division: 'NFC South', conference: 'NFC'})
MERGE (t6:Team {id: 'CHI', name: 'Chicago Bears', division: 'NFC North', conference: 'NFC'})
MERGE (t7:Team {id: 'CIN', name: 'Cincinnati Bengals', division: 'AFC North', conference: 'AFC'})
MERGE (t8:Team {id: 'CLE', name: 'Cleveland Browns', division: 'AFC North', conference: 'AFC'})
MERGE (t9:Team {id: 'DAL', name: 'Dallas Cowboys', division: 'NFC East', conference: 'NFC'})
MERGE (t10:Team {id: 'DEN', name: 'Denver Broncos', division: 'AFC West', conference: 'AFC'})
MERGE (t11:Team {id: 'DET', name: 'Detroit Lions', division: 'NFC North', conference: 'NFC'})
MERGE (t12:Team {id: 'GB', name: 'Green Bay Packers', division: 'NFC North', conference: 'NFC'})
MERGE (t13:Team {id: 'HOU', name: 'Houston Texans', division: 'AFC South', conference: 'AFC'})
MERGE (t14:Team {id: 'IND', name: 'Indianapolis Colts', division: 'AFC South', conference: 'AFC'})
MERGE (t15:Team {id: 'JAX', name: 'Jacksonville Jaguars', division: 'AFC South', conference: 'AFC'})
MERGE (t16:Team {id: 'KC', name: 'Kansas City Chiefs', division: 'AFC West', conference: 'AFC'})
MERGE (t17:Team {id: 'LV', name: 'Las Vegas Raiders', division: 'AFC West', conference: 'AFC'})
MERGE (t18:Team {id: 'LAC', name: 'Los Angeles Chargers', division: 'AFC West', conference: 'AFC'})
MERGE (t19:Team {id: 'LAR', name: 'Los Angeles Rams', division: 'NFC West', conference: 'NFC'})
MERGE (t20:Team {id: 'MIA', name: 'Miami Dolphins', division: 'AFC East', conference: 'AFC'})
MERGE (t21:Team {id: 'MIN', name: 'Minnesota Vikings', division: 'NFC North', conference: 'NFC'})
MERGE (t22:Team {id: 'NE', name: 'New England Patriots', division: 'AFC East', conference: 'AFC'})
MERGE (t23:Team {id: 'NO', name: 'New Orleans Saints', division: 'NFC South', conference: 'NFC'})
MERGE (t24:Team {id: 'NYG', name: 'New York Giants', division: 'NFC East', conference: 'NFC'})
MERGE (t25:Team {id: 'NYJ', name: 'New York Jets', division: 'AFC East', conference: 'AFC'})
MERGE (t26:Team {id: 'PHI', name: 'Philadelphia Eagles', division: 'NFC East', conference: 'NFC'})
MERGE (t27:Team {id: 'PIT', name: 'Pittsburgh Steelers', division: 'AFC North', conference: 'AFC'})
MERGE (t28:Team {id: 'SF', name: 'San Francisco 49ers', division: 'NFC West', conference: 'NFC'})
MERGE (t29:Team {id: 'SEA', name: 'Seattle Seahawks', division: 'NFC West', conference: 'NFC'})
MERGE (t30:Team {id: 'TB', name: 'Tampa Bay Buccaneers', division: 'NFC South', conference: 'NFC'})
MERGE (t31:Team {id: 'TEN', name: 'Tennessee Titans', division: 'AFC South', conference: 'AFC'})
MERGE (t32:Team {id: 'WAS', name: 'Washington Commanders', division: 'NFC East', conference: 'NFC'});

// ========================================
// 3. RELATIONSHIP TEMPLATES
// ========================================

// Expert-Game Prediction Relationships
// (:Expert)-[:PREDICTED {winner, confidence, accuracy, reasoning}]->(:Game)

// Memory-Game Usage Relationships
// (:Memory)-[:USED_IN {expert_id, influence_weight, retrieval_rank}]->(:Game)

// Team-Team Matchup Relationships
// (:Team)-[:FACED {games, wins, losses, last_game, avg_margin}]->(:Team)

// Expert-Team Knowledge Relationships
// (:Expert)-[:KNOWS_TEAM {knowledge_strength, games_analyzed, accuracy_rate, confidence}]->(:Team)

// Expert Learning Relationships
// (:Expert)-[:LEARNED_FROM {lesson, confidence_change, memory_formed}]->(:Game)

// ========================================
// 4. UTILITY QUERIES FOR PROVENANCE
// ========================================

// Query: Find all memories that influenced a specific prediction
// MATCH (e:Expert {id: $expert_id})-[:PREDICTED]->(g:Game {id: $game_id})
// MATCH (m:Memory)-[:USED_IN {expert_id: $expert_id}]->(g)
// RETURN m.id, m.type, m.content, m.influence_weight

// Query: Find expert's learning progression for a team
// MATCH (e:Expert {id: $expert_id})-[k:KNOWS_TEAM]->(t:Team {id: $team_id})
// MATCH (e)-[:LEARNED_FROM]->(g:Game)
// WHERE g.home_team = $team_id OR g.away_team = $team_id
// RETURN g.date, g.id, k.accuracy_rate, k.confidence
// ORDER BY g.date

// Query: Find team rivalry patterns
// MATCH (t1:Team {id: $team1})-[f:FACED]->(t2:Team {id: $team2})
// RETURN f.games, f.wins, f.losses, f.avg_margin, f.last_game

// Query: Expert prediction accuracy by team
// MATCH (e:Expert {id: $expert_id})-[p:PREDICTED]->(g:Game)
// WHERE g.home_team = $team_id OR g.away_team = $team_id
// RETURN AVG(p.accuracy), COUNT(p), COLLECT(g.id)

// ========================================
// 5. SAMPLE DATA INSERTION TEMPLATE
// ========================================

// Example: Create a game and prediction relationship
// MERGE (g:Game {
//   id: 'KC_BUF_2023_W6',
//   home_team: 'KC',
//   away_team: 'BUF',
//   season: 2023,
//   week: 6,
//   date: date('2023-10-15'),
//   final_score_home: 24,
//   final_score_away: 20,
//   winner: 'KC'
// })
//
// MATCH (e:Expert {id: 'momentum_rider'}), (g:Game {id: 'KC_BUF_2023_W6'})
// MERGE (e)-[:PREDICTED {
//   winner: 'KC',
//   confidence: 0.75,
//   win_probability: 0.68,
//   accuracy: 1.0,
//   reasoning: 'Chiefs momentum at home',
//   created_at: datetime()
// }]->(g)

// ========================================
// 6. PERFORMANCE OPTIMIZATION
// ========================================

// Create composite indexes for common query patterns
CREATE INDEX game_team_season_idx IF NOT EXISTS FOR (g:Game) ON (g.home_team, g.away_team, g.season);
CREATE INDEX prediction_accuracy_idx IF NOT EXISTS FOR ()-[p:PREDICTED]-() ON (p.accuracy);
CREATE INDEX team_knowledge_strength_idx IF NOT EXISTS FOR ()-[k:KNOWS_TEAM]-() ON (k.knowledge_strength);

// ========================================
// 7. DATA VALIDATION QUERIES
// ========================================

// Verify all experts exist
// MATCH (e:Expert) RETURN count(e) as expert_count;

// Verify all teams exist
// MATCH (t:Team) RETURN count(t) as team_count;

// Check for orphaned relationships
// MATCH ()-[r:PREDICTED]->() WHERE NOT EXISTS(()-[r]->(:Game)) RETURN count(r);

RETURN "Neo4j NFL Expert Learning System schema initialized successfully" as status;
