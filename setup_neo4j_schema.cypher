// Create constraints for unique identifiers
CREATE CONSTRAINT team_id IF NOT EXISTS FOR (t:Team) REQUIRE t.id IS UNIQUE;
CREATE CONSTRAINT expert_id IF NOT EXISTS FOR (e:Expert) REQUIRE e.id IS UNIQUE;
CREATE CONSTRAINT game_id IF NOT EXISTS FOR (g:Game) REQUIRE g.id IS UNIQUE;
CREATE CONSTRAINT prediction_id IF NOT EXISTS FOR (p:Prediction) REQUIRE p.id IS UNIQUE;

// Create indexes for performance
CREATE INDEX team_name IF NOT EXISTS FOR (t:Team) ON (t.name);
CREATE INDEX expert_personality IF NOT EXISTS FOR (e:Expert) ON (e.personality_type);
CREATE INDEX game_season_week IF NOT EXISTS FOR (g:Game) ON (g.season, g.week);
CREATE INDEX prediction_accuracy IF NOT EXISTS FOR (p:Prediction) ON (p.correct);
CREATE INDEX game_date IF NOT EXISTS FOR (g:Game) ON (g.date);

// Create composite indexes for common queries
CREATE INDEX game_teams IF NOT EXISTS FOR (g:Game) ON (g.home_team, g.away_team);
CREATE INDEX expert_accuracy IF NOT EXISTS FOR (e:Expert) ON (e.total_predictions, e.correct_predictions);

// Initialize team nodes (run this after creating constraints)
MERGE (t:Team {id: 'ARI', name: 'Arizona Cardinals', conference: 'NFC', division: 'West'});
MERGE (t:Team {id: 'ATL', name: 'Atlanta Falcons', conference: 'NFC', division: 'South'});
MERGE (t:Team {id: 'BAL', name: 'Baltimore Ravens', conference: 'AFC', division: 'North'});
MERGE (t:Team {id: 'BUF', name: 'Buffalo Bills', conference: 'AFC', division: 'East'});
MERGE (t:Team {id: 'CAR', name: 'Carolina Panthers', conference: 'NFC', division: 'South'});
MERGE (t:Team {id: 'CHI', name: 'Chicago Bears', conference: 'NFC', division: 'North'});
MERGE (t:Team {id: 'CIN', name: 'Cincinnati Bengals', conference: 'AFC', division: 'North'});
MERGE (t:Team {id: 'CLE', name: 'Cleveland Browns', conference: 'AFC', division: 'North'});
MERGE (t:Team {id: 'DAL', name: 'Dallas Cowboys', conference: 'NFC', division: 'East'});
MERGE (t:Team {id: 'DEN', name: 'Denver Broncos', conference: 'AFC', division: 'West'});
MERGE (t:Team {id: 'DET', name: 'Detroit Lions', conference: 'NFC', division: 'North'});
MERGE (t:Team {id: 'GB', name: 'Green Bay Packers', conference: 'NFC', division: 'North'});
MERGE (t:Team {id: 'HOU', name: 'Houston Texans', conference: 'AFC', division: 'South'});
MERGE (t:Team {id: 'IND', name: 'Indianapolis Colts', conference: 'AFC', division: 'South'});
MERGE (t:Team {id: 'JAX', name: 'Jacksonville Jaguars', conference: 'AFC', division: 'South'});
MERGE (t:Team {id: 'KC', name: 'Kansas City Chiefs', conference: 'AFC', division: 'West'});
MERGE (t:Team {id: 'LV', name: 'Las Vegas Raiders', conference: 'AFC', division: 'West'});
MERGE (t:Team {id: 'LAC', name: 'Los Angeles Chargers', conference: 'AFC', division: 'West'});
MERGE (t:Team {id: 'LAR', name: 'Los Angeles Rams', conference: 'NFC', division: 'West'});
MERGE (t:Team {id: 'MIA', name: 'Miami Dolphins', conference: 'AFC', division: 'East'});
MERGE (t:Team {id: 'MIN', name: 'Minnesota Vikings', conference: 'NFC', division: 'North'});
MERGE (t:Team {id: 'NE', name: 'New England Patriots', conference: 'AFC', division: 'East'});
MERGE (t:Team {id: 'NO', name: 'New Orleans Saints', conference: 'NFC', division: 'South'});
MERGE (t:Team {id: 'NYG', name: 'New York Giants', conference: 'NFC', division: 'East'});
MERGE (t:Team {id: 'NYJ', name: 'New York Jets', conference: 'AFC', division: 'East'});
MERGE (t:Team {id: 'PHI', name: 'Philadelphia Eagles', conference: 'NFC', division: 'East'});
MERGE (t:Team {id: 'PIT', name: 'Pittsburgh Steelers', conference: 'AFC', division: 'North'});
MERGE (t:Team {id: 'SF', name: 'San Francisco 49ers', conference: 'NFC', division: 'West'});
MERGE (t:Team {id: 'SEA', name: 'Seattle Seahawks', conference: 'NFC', division: 'West'});
MERGE (t:Team {id: 'TB', name: 'Tampa Bay Buccaneers', conference: 'NFC', division: 'South'});
MERGE (t:Team {id: 'TEN', name: 'Tennessee Titans', conference: 'AFC', division: 'South'});
MERGE (t:Team {id: 'WAS', name: 'Washington Commanders', conference: 'NFC', division: 'East'});

// Initialize expert nodes
MERGE (e:Expert {
    id: 'conservative_analyzer',
    name: 'Conservative Analyzer',
    personality_type: 'conservative',
    total_predictions: 0,
    correct_predictions: 0,
    accuracy: 0.0
});

MERGE (e:Expert {
    id: 'risk_taking_gambler',
    name: 'Risk Taking Gambler',
    personality_type: 'aggressive',
    total_predictions: 0,
    correct_predictions: 0,
    accuracy: 0.0
});

MERGE (e:Expert {
    id: 'contrarian_rebel',
    name: 'Contrarian Rebel',
    personality_type: 'contrarian',
    total_predictions: 0,
    correct_predictions: 0,
    accuracy: 0.0
});

MERGE (e:Expert {
    id: 'value_hunter',
    name: 'Value Hunter',
    personality_type: 'analytical',
    total_predictions: 0,
    correct_predictions: 0,
    accuracy: 0.0
});

MERGE (e:Expert {
    id: 'momentum_rider',
    name: 'Momentum Rider',
    personality_type: 'trend_following',
    total_predictions: 0,
    correct_predictions: 0,
    accuracy: 0.0
});

MERGE (e:Expert {
    id: 'fundamentalist_scholar',
    name: 'Fundamentalist Scholar',
    personality_type: 'analytical',
    total_predictions: 0,
    correct_predictions: 0,
    accuracy: 0.0
});

MERGE (e:Expert {
    id: 'gut_instinct_expert',
    name: 'Gut Instinct Expert',
    personality_type: 'intuitive',
    total_predictions: 0,
    correct_predictions: 0,
    accuracy: 0.0
});

MERGE (e:Expert {
    id: 'statistics_purist',
    name: 'Statistics Purist',
    personality_type: 'analytical',
    total_predictions: 0,
    correct_predictions: 0,
    accuracy: 0.0
});

MERGE (e:Expert {
    id: 'trend_reversal_specialist',
    name: 'Trend Reversal Specialist',
    personality_type: 'contrarian',
    total_predictions: 0,
    correct_predictions: 0,
    accuracy: 0.0
});

MERGE (e:Expert {
    id: 'underdog_champion',
    name: 'Underdog Champion',
    personality_type: 'contrarian',
    total_predictions: 0,
    correct_predictions: 0,
    accuracy: 0.0
});

MERGE (e:Expert {
    id: 'sharp_money_follower',
    name: 'Sharp Money Follower',
    personality_type: 'trend_following',
    total_predictions: 0,
    correct_predictions: 0,
    accuracy: 0.0
});

MERGE (e:Expert {
    id: 'popular_narrative_fader',
    name: 'Popular Narrative Fader',
    personality_type: 'contrarian',
    total_predictions: 0,
    correct_predictions: 0,
    accuracy: 0.0
});

MERGE (e:Expert {
    id: 'market_inefficiency_exploiter',
    name: 'Market Inefficiency Exploiter',
    personality_type: 'analytical',
    total_predictions: 0,
    correct_predictions: 0,
    accuracy: 0.0
});

MERGE (e:Expert {
    id: 'chaos_theory_believer',
    name: 'Chaos Theory Believer',
    personality_type: 'intuitive',
    total_predictions: 0,
    correct_predictions: 0,
    accuracy: 0.0
});

MERGE (e:Expert {
    id: 'consensus_follower',
    name: 'Consensus Follower',
    personality_type: 'trend_following',
    total_predictions: 0,
    correct_predictions: 0,
    accuracy: 0.0
});

// Create division rivalry relationships
MATCH (t1:Team), (t2:Team)
WHERE t1.division = t2.division AND t1.conference = t2.conference AND t1.id <> t2.id
MERGE (t1)-[:DIVISION_RIVAL]->(t2);

// Create conference relationships
MATCH (t1:Team), (t2:Team)
WHERE t1.conference = t2.conference AND t1.id <> t2.id
MERGE (t1)-[:SAME_CONFERENCE]->(t2);
